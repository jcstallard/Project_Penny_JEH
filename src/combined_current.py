from __future__ import annotations

from pathlib import Path
import numpy as np

STRATEGIES = [
    ["1","1","1"], 
    ["1","1","0"], 
    ["1","0","1"], 
    ["1","0","0"], 
    ["0","1","1"], 
    ["0","1","0"], 
    ["0","0","1"], 
    ["0","0","0"], 
]

# Loading decks

def load_decks(raw_dir_path="data/raw_decks", max_files: int | None = None) -> list[list[str]]:
    """
    Load decks from .npy files in the specified directory.
    Returns a list of decks, where each deck is a list of "1"/"0" strings.
    """
    files = sorted(Path(raw_dir_path).glob("*.npy"))[:max_files] # delete this for full game
    return [
        list(row)
        for path in files
        for row in np.load(path, allow_pickle=False)
    ]


# Rons version
def score_ron(deck: list, p1: list, p2: list) -> tuple[int, int]:
    "Basic scoring function for the Ron game. Counts how many times each player's pattern appears in the deck."
    s1, s2, i = 0, 0, 0
    while i <= len(deck) - 3:
        chunk = deck[i:i+3]
        if chunk == p1:
            s1 += 3; i += 3
        elif chunk == p2:
            s2 += 3; i += 3
        else:
            i += 1
    return s1, s2

# Original version
def score_tricks(deck: list[str], p1: list[str], p2: list[str]) -> tuple[int, int]:
    """
    Score one deck under the original H-N tricks version.
    Cards accumulate on the table until a sequence is matched, then that player wins the trick.
    Returns (tricks won by p1, tricks won by p2).
    """
    table = []
    t1 = t2 = 0

    for card in deck:
        table.append(card)

        if len(table) >= 3:
            window = table[-3:]

            if window == p1:
                t1 += 1
                table.clear()
            elif window == p2:
                t2 += 1
                table.clear()

    return t1, t2

# Process both games

def process_both_games(raw_dir: str | Path = "data/raw_decks", out_dir: str | Path = "data/processed") -> None:
    """
    Process all decks for both games and save the results for the heatmaps.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    state_path = out_path / "state.npz"


    # Load previous state if it exists
    if state_path.exists():
        saved = np.load(state_path)
        n_done      = int(saved["decks_processed"])
        ron_wins1   = saved["ron_wins1"]
        ron_wins2   = saved["ron_wins2"]
        ron_draws   = saved["ron_draws"]
        hn_wins1    = saved["hn_wins1"]
        hn_wins2    = saved["hn_wins2"]
        hn_draws    = saved["hn_draws"]
    else:
        n_done = 0
        ron_wins1 = np.zeros((8,8), dtype=int)
        ron_wins2 = np.zeros((8,8), dtype=int)
        ron_draws = np.zeros((8,8), dtype=int)
        hn_wins1  = np.zeros((8,8), dtype=int)
        hn_wins2  = np.zeros((8,8), dtype=int)
        hn_draws  = np.zeros((8,8), dtype=int)

    # Load only decks we haven't processed yet

    all_decks = load_decks(raw_dir, max_files=5) # delete max_files for full game. Right now its 5,000 decks (5 files x 1,000 decks each)
    new_decks = all_decks[n_done:]
    print(f"Loaded {len(new_decks)} new decks ({n_done} already processed)")

    # Single pass over all new decks, scoring both games at once
    for deck in new_decks:
        for i, s1 in enumerate(STRATEGIES):
            for j, s2 in enumerate(STRATEGIES):
                if i == j:
                    continue

                # Ron's version
                sc1, sc2 = score_ron(deck, s1, s2)
                if sc1 > sc2:       ron_wins1[i,j] += 1
                elif sc2 > sc1:     ron_wins2[i,j] += 1
                else:               ron_draws[i,j] += 1

                # H-N tricks version
                ta, tb = score_tricks(deck, s1, s2)
                if ta > tb:         hn_wins1[i,j] += 1
                elif tb > ta:       hn_wins2[i,j] += 1
                else:               hn_draws[i,j] += 1

    # Save updated state
    total = n_done + len(new_decks)
    np.savez(
        state_path,
        ron_wins1=ron_wins1, ron_wins2=ron_wins2, ron_draws=ron_draws,
        hn_wins1=hn_wins1,   hn_wins2=hn_wins2,   hn_draws=hn_draws,
        decks_processed=total
    )

    # Save win/draw percentages for heatmap generation
    np.save(out_path / "ron_win_pct.npy",  ron_wins1 / total)
    np.save(out_path / "ron_draw_pct.npy", ron_draws  / total)
    np.save(out_path / "hn_win_pct.npy",   hn_wins1  / total)
    np.save(out_path / "hn_draw_pct.npy",  hn_draws   / total)

    print(f"Done. {total} total decks processed. Results saved to {out_path}")