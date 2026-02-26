# src/process_tricks.py
from __future__ import annotations

"""
Simple processor for the ORIGINAL Humble–Nishiyama (tricks) game.

Assumptions (matches your generator code):
- Raw decks are saved in .npy chunk files.
- Each .npy contains a 2D array of shape (num_decks, 52).
- Deck entries are either strings "1"/"0" or numeric 1/0.

What this script does:
1. Find .npy chunk files (prefix default: "decks_XXXX.npy" or "decks_0001.npy")
2. Skip files already recorded in the meta file (incremental)
3. Load each new chunk, normalize to uint8 0/1
4. For each deck, evaluate all 8×8 matchups using trick scoring
5. Update wins/draws/total and save state + meta
"""

import json
from pathlib import Path
from typing import Iterable, Tuple

import numpy as np

# ----------------------
# Configuration
# ----------------------
# Strategy ordering (must match your heatmap labels)
# R=1, B=0
STRATEGY_BITS = [
    (1, 1, 1),  # RRR
    (1, 1, 0),  # RRB
    (1, 0, 1),  # RBR
    (1, 0, 0),  # RBB
    (0, 1, 1),  # BRR
    (0, 1, 0),  # BRB
    (0, 0, 1),  # BBR
    (0, 0, 0),  # BBB
]
N_STRATS = len(STRATEGY_BITS)
DECK_LEN = 52

# Where processed outputs go
PROCESSED_DIR_DEFAULT = Path("data") / "processed"
STATE_FILENAME = "hn_tricks_state.npz"
META_FILENAME = "hn_tricks_meta.json"

# Candidate raw directories to look for .npy chunks (in order).
# Your generator used Path(__file__).parent / "raw_decks" — include that possibility.
CANDIDATE_RAW_DIRS = [
    Path.cwd() / "data" / "raw_decks",     # common project layout
    Path.cwd() / "raw_decks",              # alternate
    Path(__file__).parent / "raw_decks",   # generator-local
]


# ----------------------
# Utility: normalize loaded chunk to numeric np.uint8 0/1
# ----------------------
def _normalize_deck_array(arr: np.ndarray) -> np.ndarray:
    """
    Convert loaded numpy array (strings or numeric) to shape (n,52) dtype uint8 with values 0/1.
    Raises ValueError for malformed input.
    """
    if arr.ndim != 2 or arr.shape[1] != DECK_LEN:
        raise ValueError(f"Expected array shape (n,{DECK_LEN}), got {arr.shape}")

    # numeric integer arrays (e.g., dtype=int, uint8)
    if np.issubdtype(arr.dtype, np.integer):
        arr2 = arr.astype(np.uint8)
        if not np.isin(arr2, [0, 1]).all():
            raise ValueError("Numeric deck array contains values other than 0/1")
        return arr2

    # boolean arrays
    if arr.dtype == bool:
        return arr.astype(np.uint8)

    # string/object arrays: expect "0"/"1"
    if arr.dtype.kind in {"U", "S", "O"}:
        arr_str = arr.astype(str)
        # Check values quickly
        flat = np.unique(arr_str)
        if not set(flat).issubset({"0", "1"}):
            raise ValueError(f"String deck array contains unexpected values: {flat}")
        # Convert "1" -> 1, "0" -> 0
        return (arr_str == "1").astype(np.uint8)

    # anything else is unsupported
    raise ValueError(f"Unsupported dtype for deck array: {arr.dtype}")


# ----------------------
# Game: play one deck under 'tricks' scoring for one matchup
# ----------------------
def play_deck_tricks(deck: np.ndarray, a: Tuple[int, int, int], b: Tuple[int, int, int]) -> Tuple[int, int]:
    """
    Play one deck and return (tricks_a, tricks_b).
    deck is 1D array-like length 52 with values 0/1 (np.uint8 or convertible).
    a, b are 3-tuples of ints (0/1).
    """
    a0, a1, a2 = a
    b0, b1, b2 = b

    table: list[int] = []
    ta = tb = 0

    for c in deck:
        x = int(c)
        table.append(x)

        if len(table) >= 3:
            x0, x1, x2 = table[-3], table[-2], table[-1]
            # check A first, then B (patterns are distinct; tie is impossible in same 3)
            if (x0 == a0) and (x1 == a1) and (x2 == a2):
                ta += 1
                table.clear()
            elif (x0 == b0) and (x1 == b1) and (x2 == b2):
                tb += 1
                table.clear()

    return ta, tb


# ----------------------
# Find raw chunk files
# ----------------------
def find_raw_chunks(prefix: str = "decks") -> list[Path]:
    """
    Search candidate directories for files matching prefix_*.npy.
    Returns a sorted list of Paths.
    """
    found = []
    for base in CANDIDATE_RAW_DIRS:
        if base.exists() and base.is_dir():
            found.extend(sorted(base.glob(f"{prefix}_*.npy")))
    # Also include any matching files in cwd/data/raw_decks specifically (fallback)
    fallback = Path.cwd() / "data" / "raw_decks"
    if fallback.exists():
        found.extend(sorted(fallback.glob(f"{prefix}_*.npy")))
    # Deduplicate & sort by filename
    unique = sorted(dict.fromkeys(found), key=lambda p: p.name)
    return unique


# ----------------------
# Processed state I/O
# ----------------------
def load_state(processed_dir: Path) -> tuple[np.ndarray, np.ndarray, int, set[str]]:
    """
    Load processed state (wins, draws, total) and the set of processed filenames.
    If not present, return zeros and empty set.
    """
    processed_dir.mkdir(parents=True, exist_ok=True)
    state_path = processed_dir / STATE_FILENAME
    meta_path = processed_dir / META_FILENAME

    if state_path.exists():
        data = np.load(state_path, allow_pickle=False)
        wins = data["wins"].astype(np.int64)
        draws = data["draws"].astype(np.int64)
        total = int(data["total"].tolist()[0])
    else:
        wins = np.zeros((N_STRATS, N_STRATS), dtype=np.int64)
        draws = np.zeros((N_STRATS, N_STRATS), dtype=np.int64)
        total = 0

    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        processed = set(meta.get("processed_files", []))
    else:
        processed = set()

    return wins, draws, total, processed


def save_state(processed_dir: Path, wins: np.ndarray, draws: np.ndarray, total: int, processed: set[str]) -> None:
    """
    Persist wins/draws/total and list of processed raw filenames.
    """
    processed_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(processed_dir / STATE_FILENAME, wins=wins, draws=draws, total=np.array([total], dtype=np.int64))
    (processed_dir / META_FILENAME).write_text(json.dumps({"processed_files": sorted(processed)}), encoding="utf-8")


# ----------------------
# Main incremental processing function
# ----------------------
def process_new_raw_decks(prefix: str = "decks", processed_dir: Path | None = None) -> None:
    """
    Main entry:
    - Finds raw .npy chunks named prefix_XXXX.npy in candidate dirs
    - Skips files already recorded in meta
    - Loads and normalizes each new chunk and scores every 8x8 matchup per deck
    - Updates summary matrices and writes state + meta

    Keep this simple and easy to read.
    """
    if processed_dir is None:
        processed_dir = PROCESSED_DIR_DEFAULT

    # Load previous state (if any)
    wins, draws, total, processed_files = load_state(processed_dir)

    # Locate raw chunks
    chunks = find_raw_chunks(prefix=prefix)
    new_chunks = [p for p in chunks if p.name not in processed_files]

    print(f"[PROCESS] Candidate raw dirs: {[str(p) for p in CANDIDATE_RAW_DIRS]}")
    print(f"[PROCESS] Found {len(chunks)} chunk file(s); {len(new_chunks)} new to process.")
    print(f"[PROCESS] Previously processed decks total: {total}")

    if not new_chunks:
        print("[PROCESS] No new .npy chunks to process. Exiting.")
        return

    # For each new chunk, load, normalize, and process decks
    for chunk in new_chunks:
        print(f"\n[PROCESS] Loading chunk: {chunk}")
        raw = np.load(chunk, allow_pickle=False)  # may be string or numeric

        decks = _normalize_deck_array(raw)  # shape (m, 52), dtype uint8
        print(f"[PROCESS] Chunk normalized shape: {decks.shape}")

        # process decks one by one
        for deck in decks:
            # evaluate every matchup (row = strategy i as "me", column = strategy j as opponent)
            for i, a in enumerate(STRATEGY_BITS):
                for j, b in enumerate(STRATEGY_BITS):
                    if i == j:
                        # players are expected to choose different sequences; mark diagonal as draw
                        draws[i, j] += 1
                        continue

                    ta, tb = play_deck_tricks(deck, a, b)
                    if ta > tb:
                        wins[i, j] += 1
                    elif ta == tb:
                        draws[i, j] += 1
                    # else: B wins, no increment to A's wins/draws

            total += 1

        # only mark chunk processed after successful processing
        processed_files.add(chunk.name)
        print(f"[PROCESS] Finished {chunk.name} — total decks processed now: {total}")

    # Save updated state
    save_state(processed_dir, wins, draws, total, processed_files)

    print("\n[PROCESS] Saved state and meta to", processed_dir)
    print(f"[CHECK] wins sum: {int(wins.sum())}, draws sum: {int(draws.sum())}")
    print(f"[PROCESS] Final total decks processed: {total}")


# ----------------------
# CLI-style quick-run
# ----------------------
if __name__ == "__main__":
    # Run with default prefix "decks" and default processed dir (data/processed)
    process_new_raw_decks(prefix="decks")
