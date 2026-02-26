from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

import numpy as np

# ============================================================
# 1) Constants: strategies + file names
# ============================================================

# Strategies in the heatmap order (R=1, B=0):
#   RRR, RRB, RBR, RBB, BRR, BRB, BBR, BBB
STRATEGY_BITS: list[Tuple[int, int, int]] = [
    (1, 1, 1),
    (1, 1, 0),
    (1, 0, 1),
    (1, 0, 0),
    (0, 1, 1),
    (0, 1, 0),
    (0, 0, 1),
    (0, 0, 0),
]
N = 8
DECK_LEN = 52

# Processed outputs (separate files for each scoring rule)
TRICKS_STATE_FILE = "hn_tricks_state.npz"
TRICKS_META_FILE = "hn_tricks_meta.json"

CARDS_STATE_FILE = "ron_cards_state.npz"
CARDS_META_FILE = "ron_cards_meta.json"


# ============================================================
# 2) Raw data discovery + normalization
# ============================================================

def find_raw_chunks(raw_dir: Path, prefix: str) -> list[Path]:
    """
    Find raw .npy chunks like: decks_0001.npy, decks_0002.npy, ...
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    return sorted(raw_dir.glob(f"{prefix}_*.npy"))


def normalize_decks(raw: np.ndarray, name: str) -> np.ndarray:
    """
    Your generator saves decks as strings "1"/"0" (sometimes numeric).
    This converts to a numeric array of 0/1 with dtype uint8.

    Expected shape: (num_decks, 52)
    """
    if raw.ndim != 2 or raw.shape[1] != DECK_LEN:
        raise ValueError(f"{name}: expected shape (n,{DECK_LEN}), got {raw.shape}")

    # If numeric already, just validate values
    if np.issubdtype(raw.dtype, np.integer) or raw.dtype == bool:
        decks = raw.astype(np.uint8)
        if not np.isin(decks, [0, 1]).all():
            raise ValueError(f"{name}: numeric decks contain values other than 0/1")
        return decks

    # If strings/objects, convert "1"->1 and "0"->0
    if raw.dtype.kind in {"U", "S", "O"}:
        s = raw.astype(str)
        if not np.isin(s, ["0", "1"]).all():
            raise ValueError(f"{name}: found values other than '0'/'1'")
        return (s == "1").astype(np.uint8)

    raise ValueError(f"{name}: unsupported dtype {raw.dtype}")


# ============================================================
# 3) Two scoring rules (one deck, one matchup)
# ============================================================

def score_tricks(deck: np.ndarray, a: Tuple[int, int, int], b: Tuple[int, int, int]) -> Tuple[int, int]:
    """
    Original H–N scoring:
    - When a pattern hits, winner gets +1 trick.
    - Table clears.
    """
    a0, a1, a2 = a
    b0, b1, b2 = b

    table: list[int] = []
    ta = tb = 0

    for bit in deck:
        table.append(int(bit))
        if len(table) >= 3:
            x0, x1, x2 = table[-3], table[-2], table[-1]
            if (x0, x1, x2) == (a0, a1, a2):
                ta += 1
                table.clear()
            elif (x0, x1, x2) == (b0, b1, b2):
                tb += 1
                table.clear()

    return ta, tb


def score_cards_won(deck: np.ndarray, a: Tuple[int, int, int], b: Tuple[int, int, int]) -> Tuple[int, int]:
    """
    Ron's version:
    - When a pattern hits, winner gets ALL cards currently on the table pile.
      (So winner += len(table))
    - Table clears.
    """
    a0, a1, a2 = a
    b0, b1, b2 = b

    table: list[int] = []
    ca = cb = 0

    for bit in deck:
        table.append(int(bit))
        if len(table) >= 3:
            x0, x1, x2 = table[-3], table[-2], table[-1]
            if (x0, x1, x2) == (a0, a1, a2):
                ca += len(table)
                table.clear()
            elif (x0, x1, x2) == (b0, b1, b2):
                cb += len(table)
                table.clear()

    return ca, cb


# ============================================================
# 4) Save/load processed state (wins/draws/total + meta)
# ============================================================

def load_state(processed_dir: Path, state_file: str, meta_file: str) -> tuple[np.ndarray, np.ndarray, int, set[str]]:
    """
    Each scoring rule keeps:
      - wins[8,8], draws[8,8], total (number of decks processed)
      - processed_files: which raw chunks are already done for that rule
    """
    processed_dir.mkdir(parents=True, exist_ok=True)
    sp = processed_dir / state_file
    mp = processed_dir / meta_file

    if sp.exists():
        data = np.load(sp, allow_pickle=False)
        wins = data["wins"].astype(np.int64)
        draws = data["draws"].astype(np.int64)
        total = int(data["total"][0])
    else:
        wins = np.zeros((N, N), dtype=np.int64)
        draws = np.zeros((N, N), dtype=np.int64)
        total = 0

    if mp.exists():
        meta = json.loads(mp.read_text(encoding="utf-8"))
        done = set(meta.get("processed_files", []))
    else:
        done = set()

    return wins, draws, total, done


def save_state(processed_dir: Path, state_file: str, meta_file: str,
               wins: np.ndarray, draws: np.ndarray, total: int, done: set[str]) -> None:
    """
    Save state + meta so next run can resume without reprocessing old chunks.
    """
    processed_dir.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        processed_dir / state_file,
        wins=wins,
        draws=draws,
        total=np.array([total], dtype=np.int64),
    )

    (processed_dir / meta_file).write_text(
        json.dumps({"processed_files": sorted(done)}, indent=2),
        encoding="utf-8",
    )


# ============================================================
# 5) Main function: load each raw chunk ONCE, update both summaries
# ============================================================

def process_both_versions(raw_dir: Path, processed_dir: Path, prefix: str = "decks") -> None:
    """
    Pipeline:
    1) Find raw chunk files (prefix_*.npy)
    2) Load each chunk once (normalize to 0/1)
    3) For each deck:
         - update original tricks matrix
         - update Ron cards-won matrix
    4) Save separate processed outputs for each scoring rule
    """
    raw_chunks = find_raw_chunks(raw_dir, prefix)

    # Load processed summaries for BOTH versions
    t_wins, t_draws, t_total, t_done = load_state(processed_dir, TRICKS_STATE_FILE, TRICKS_META_FILE)
    c_wins, c_draws, c_total, c_done = load_state(processed_dir, CARDS_STATE_FILE, CARDS_META_FILE)

    # We process a chunk if either version hasn't seen it yet
    todo = [p for p in raw_chunks if (p.name not in t_done) or (p.name not in c_done)]

    print(f"[COMBINED] raw_dir={raw_dir}")
    print(f"[COMBINED] chunk files found: {len(raw_chunks)}")
    print(f"[COMBINED] new chunks to process: {len(todo)}")
    print(f"[TRICKS ] decks processed so far: {t_total}")
    print(f"[CARDS  ] decks processed so far: {c_total}")

    if not todo:
        print("[COMBINED] Nothing new to do.")
        return

    for chunk_path in todo:
        print(f"\n[COMBINED] Loading {chunk_path.name} ...")
        raw = np.load(chunk_path, allow_pickle=False)
        decks = normalize_decks(raw, chunk_path.name)
        print(f"[COMBINED] chunk shape: {decks.shape}")

        # Process every deck in this chunk
        for deck in decks:
            # --- Original (tricks) ---
            if chunk_path.name not in t_done:
                for i, a in enumerate(STRATEGY_BITS):
                    for j, b in enumerate(STRATEGY_BITS):
                        if i == j:
                            # same-pattern matchup not allowed; keep diagonal as draw
                            t_draws[i, j] += 1
                            continue
                        ta, tb = score_tricks(deck, a, b)
                        if ta > tb:
                            t_wins[i, j] += 1
                        elif ta == tb:
                            t_draws[i, j] += 1
                t_total += 1

            # --- Ron's version (cards won) ---
            if chunk_path.name not in c_done:
                for i, a in enumerate(STRATEGY_BITS):
                    for j, b in enumerate(STRATEGY_BITS):
                        if i == j:
                            c_draws[i, j] += 1
                            continue
                        ca, cb = score_cards_won(deck, a, b)
                        if ca > cb:
                            c_wins[i, j] += 1
                        elif ca == cb:
                            c_draws[i, j] += 1
                c_total += 1

        # Mark the chunk as processed for whichever versions we updated
        if chunk_path.name not in t_done:
            t_done.add(chunk_path.name)
        if chunk_path.name not in c_done:
            c_done.add(chunk_path.name)

        print(f"[COMBINED] Finished {chunk_path.name}")
        print(f"          totals -> tricks: {t_total}, cards: {c_total}")

    # Save BOTH versions (separately)
    save_state(processed_dir, TRICKS_STATE_FILE, TRICKS_META_FILE, t_wins, t_draws, t_total, t_done)
    save_state(processed_dir, CARDS_STATE_FILE, CARDS_META_FILE, c_wins, c_draws, c_total, c_done)

    print("\n[COMBINED] Saved processed files to:", processed_dir)
    print("  -", processed_dir / TRICKS_STATE_FILE)
    print("  -", processed_dir / TRICKS_META_FILE)
    print("  -", processed_dir / CARDS_STATE_FILE)
    print("  -", processed_dir / CARDS_META_FILE)