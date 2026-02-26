from pathlib import Path
import numpy as np

# red is 1, black is 0


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

def load_decks(raw_dir_path="data/raw_decks") -> list[list[str]]:
    """
    Load decks from .npy files in the specified directory.
    Returns a list of decks, where each deck is a list of "1"/"0" strings.
    """
    return [
        list(row)
        for path in sorted(Path(raw_dir_path).glob("*.npy"))
        for row in np.load(path, allow_pickle=False)
    ]

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

def process_ron(raw_dir_path="data/raw_decks", out_dir_path="data/processed") -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Process the raw decks and save the results in a structured format."""
    Path(out_dir_path).mkdir(parents=True, exist_ok=True)
    state_path = Path(out_dir_path) / "ron_state.npz"

    # Check if there's a saved state to resume from

    if state_path.exists():
        saved = np.load(state_path)
        n_done = int(saved["decks_processed"])
        wins1, wins2, draws = saved["wins1"], saved["wins2"], saved["draws"]
    
    else:
        n_done = 0
        wins1 = np.zeros((8,8), dtype=int)
        wins2 = np.zeros((8,8), dtype=int)
        draws = np.zeros((8,8), dtype=int)
    
    decks = load_decks(raw_dir_path)[n_done:]

    # Process each deck and update the win/draw counts

    for deck in decks:
        for i, s1 in enumerate(STRATEGIES):
            for j, s2 in enumerate(STRATEGIES):
                if i == j: continue
                sc1, sc2 = score_ron(deck, s1, s2)
                if sc1 > sc2:   wins1[i,j] += 1
                elif sc2 > sc1: wins2[i,j] += 1
                else:           draws[i,j] += 1
        
    # Save the updated state and results after processing the new decks

    total = n_done + len(decks)
    np.savez(state_path, wins1=wins1, wins2=wins2, draws=draws, decks_processed=total)
    np.save(Path(out_dir_path) / "ron_win_pct.npy", wins1 / total)
    np.save(Path(out_dir_path) / "ron_draw_pct.npy", draws / total)
    
    print(f"Done: {len(decks)} new decks processed ({total} total)")
    return wins1, wins2, draws

