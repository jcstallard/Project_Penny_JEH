from __future__ import annotations

"""
process_tricks.py

This module does the "processing side" of the project for the ORIGINAL
Humble–Nishiyama game scored by TRICKS.

What it handles:
- Loading raw decks stored as JSONL chunk files (append-only)
- Scoring each deck for all 8x8 strategy matchups (row = "me"/Player A)
- Updating summary matrices incrementally (only new raw chunks are processed)
- Saving processed summaries to data/processed/ so future runs are fast

Deck encoding:
- Each deck is a list of 52 strings: "1" (red) or "0" (black)

Strategy encoding:
- Patterns are length-3 strings over {"0","1"}.
- We also provide labels like "RRB" for plotting/README convenience.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

import numpy as np


# ----------------------------
# Strategy ordering (MUST match instructor heatmap ordering)
# ----------------------------
# Labels for humans (plots / README)
STRATEGY_LABELS: list[str] = [
    "RRR",
    "RRB",
    "RBR",
    "RBB",
    "BRR",
    "BRB",
    "BBR",
    "BBB",
]

# Same order, but encoded as bits where:
#   R -> "1", B -> "0"
STRATEGY_BITS: list[str] = [
    "111",
    "110",
    "101",
    "100",
    "011",
    "010",
    "001",
    "000",
]

N_STRATS = 8
DECK_LEN = 52

STATE_FILENAME = "hn_tricks_state.npz"
META_FILENAME = "hn_tricks_meta.json"


# ----------------------------
# Data containers
# ----------------------------
@dataclass
class TricksState:
    """
    wins[i,j]  = number of decks where row strategy i (Player A / "me") wins vs column strategy j
    draws[i,j] = number of decks where that matchup ended in a draw
    total      = number of decks processed so far
    """
    wins: np.ndarray  # shape (8,8), int
    draws: np.ndarray  # shape (8,8), int
    total: int


def new_state() -> TricksState:
    return TricksState(
        wins=np.zeros((N_STRATS, N_STRATS), dtype=np.int64),
        draws=np.zeros((N_STRATS, N_STRATS), dtype=np.int64),
        total=0,
    )


# ----------------------------
# Raw deck loading (JSONL)
# ----------------------------
def iter_decks_jsonl(files: Iterable[Path]) -> Iterator[list[str]]:
    """
    Stream decks from JSONL chunk files.

    Each line is a JSON list of length 52 containing "0"/"1" strings.
    We validate lightly because debugging corrupted data later is painful.
    """
    for fp in files:
        with fp.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                deck = json.loads(line)

                if len(deck) != DECK_LEN:
                    raise ValueError(f"{fp.name}: expected {DECK_LEN} cards, got {len(deck)}")

                if any(c not in ("0", "1") for c in deck):
                    raise ValueError(f"{fp.name}: deck contains non 0/1 values")

                yield deck


# ----------------------------
# Game logic: Original H-N scored by tricks
# ----------------------------
def _validate_pattern(p: str) -> str:
    p = p.strip()
    if len(p) != 3:
        raise ValueError("Patterns must be length 3.")
    if any(ch not in ("0", "1") for ch in p):
        raise ValueError("Patterns must contain only '0' and '1'.")
    return p


def play_deck_tricks(deck: list[str], pattern_a: str, pattern_b: str) -> tuple[int, int]:
    """
    Play one deck and return (tricks_a, tricks_b).

    Rules:
    - Reveal one card at a time to the table.
    - As soon as the last 3 table cards match a player's pattern, that player wins a trick.
    - Winning a trick clears the table.
    - Leftover cards at the end that never complete a pattern do not count as a trick.
    """
    a = _validate_pattern(pattern_a)
    b = _validate_pattern(pattern_b)

    if a == b:
        raise ValueError("Players must choose different patterns (original H-N game).")

    table: list[str] = []
    tricks_a = 0
    tricks_b = 0

    for card in deck:
        table.append(card)

        if len(table) >= 3:
            last3 = "".join(table[-3:])

            if last3 == a:
                tricks_a += 1
                table.clear()
            elif last3 == b:
                tricks_b += 1
                table.clear()

    return tricks_a, tricks_b


# ----------------------------
# Processed state I/O
# ----------------------------
def load_state(processed_dir: Path) -> tuple[TricksState, set[str]]:
    """
    Load the processed state and the set of raw chunk filenames already processed.

    If this is the first run, return an empty state and empty processed set.
    """
    processed_dir.mkdir(parents=True, exist_ok=True)

    state_path = processed_dir / STATE_FILENAME
    meta_path = processed_dir / META_FILENAME

    if not state_path.exists() or not meta_path.exists():
        return new_state(), set()

    data = np.load(state_path, allow_pickle=True)
    state = TricksState(
        wins=data["wins"].astype(np.int64),
        draws=data["draws"].astype(np.int64),
        total=int(data["total"][0]),
    )

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    processed_files = set(meta.get("processed_files", []))

    return state, processed_files


def save_state(processed_dir: Path, state: TricksState, processed_files: set[str]) -> None:
    """
    Save summary matrices + metadata.

    This is what makes re-runs fast: we don't re-score old decks.
    """
    processed_dir.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        processed_dir / STATE_FILENAME,
        wins=state.wins,
        draws=state.draws,
        total=np.array([state.total], dtype=np.int64),
    )

    (processed_dir / META_FILENAME).write_text(
        json.dumps({"processed_files": sorted(processed_files)}, indent=2),
        encoding="utf-8",
    )


# ----------------------------
# Main incremental processor
# ----------------------------
def list_raw_chunks(raw_dir: Path, prefix: str = "raw_decks") -> list[Path]:
    """
    Return all raw chunk files sorted in a stable order.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    return sorted(raw_dir.glob(f"{prefix}_*.jsonl"))


def process_new_raw_decks(
    raw_dir: Path,
    processed_dir: Path,
    prefix: str = "raw_decks",
    verbose: bool = True,
) -> TricksState:
    """
    Incrementally process raw decks and update summaries.

    - Loads existing state (wins/draws/total + which files already processed)
    - Finds new raw chunk files
    - Scores only new files
    - Saves updated state back to disk

    verbose=True prints enough info to prove the program is actually
    loading, processing, and storing data.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    state, already_processed = load_state(processed_dir)

    all_chunks = list_raw_chunks(raw_dir, prefix=prefix)
    new_chunks = [p for p in all_chunks if p.name not in already_processed]

    if verbose:
        print("\n[PROCESS] Raw dir:", raw_dir)
        print(f"[PROCESS] Found {len(all_chunks)} raw chunk file(s).")
        print(f"[PROCESS] Already processed: {len(already_processed)} file(s).")
        print(f"[PROCESS] New to process: {len(new_chunks)} file(s).")

    if not new_chunks:
        if verbose:
            print("[PROCESS] No new raw files. Nothing to do.")
            print(f"[PROCESS] Total decks processed: {state.total}\n")
        return state

    patterns = STRATEGY_BITS

    for chunk_path in new_chunks:
        if verbose:
            print(f"\n[PROCESS] Processing chunk: {chunk_path.name}")

        decks_read = 0

        for deck in iter_decks_jsonl([chunk_path]):
            decks_read += 1

            # For this deck, evaluate every matchup (row i vs col j).
            for i, a in enumerate(patterns):
                for j, b in enumerate(patterns):
                    if i == j:
                        # Original rules want different sequences. To keep the heatmap full,
                        # we treat diagonal as draw by definition.
                        state.draws[i, j] += 1
                        continue

                    ta, tb = play_deck_tricks(deck, a, b)

                    if ta > tb:
                        state.wins[i, j] += 1
                    elif ta == tb:
                        state.draws[i, j] += 1
                    # If B wins, we don't increment A's win/draw.

            state.total += 1

        if verbose:
            print(f"[PROCESS] Decks read from {chunk_path.name}: {decks_read}")

        # Only mark chunk as processed AFTER we successfully read it completely.
        already_processed.add(chunk_path.name)

    save_state(processed_dir, state, already_processed)

    if verbose:
        print("\n[PROCESS] Saved processed summaries:")
        print("         ", processed_dir / STATE_FILENAME)
        print("         ", processed_dir / META_FILENAME)
        print(f"[PROCESS] Total decks processed: {state.total}")
        print(f"[CHECK] wins sum:  {int(state.wins.sum())}")
        print(f"[CHECK] draws sum: {int(state.draws.sum())}\n")

    return state


# ----------------------------
# Optional: export percent arrays (nice for plotting/debugging)
# ----------------------------
def export_final_arrays(processed_dir: Path, state: TricksState) -> None:
    """
    Save win% and draw% arrays separately so plotting code can load them quickly.
    """
    processed_dir.mkdir(parents=True, exist_ok=True)

    if state.total <= 0:
        win_pct = np.zeros((N_STRATS, N_STRATS), dtype=float)
        draw_pct = np.zeros((N_STRATS, N_STRATS), dtype=float)
    else:
        win_pct = 100.0 * state.wins / float(state.total)
        draw_pct = 100.0 * state.draws / float(state.total)

    np.save(processed_dir / "hn_tricks_win_pct.npy", win_pct)
    np.save(processed_dir / "hn_tricks_draw_pct.npy", draw_pct)


# ----------------------------
# Optional: quick CLI-style run for debugging
# ----------------------------
if __name__ == "__main__":
    # This is here for quick debugging:
    #   python -m src.process_tricks
    #
    # In the actual project, main.py should call process_new_raw_decks instead.
    raw = Path("data/raw_decks")
    processed = Path("data/processed")

    st = process_new_raw_decks(raw, processed, prefix="raw_decks", verbose=True)
    export_final_arrays(processed, st)

    print(f"Done. Total decks processed: {st.total}")