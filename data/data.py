from __future__ import annotations


import random
from pathlib import Path
import numpy as np


def generate_deck() -> list[str]:
    """
    Generate a shuffled 52-card red/black
    deck encoded as 1s and 0s.
    """
    deck: list[str] = ["1"] * 26 + ["0"] * 26
    random.shuffle(deck)
    return deck


def generate_decks(count: int) -> list[list[str]]:
    """
    Generate multiple shuffled decks in memory.
    """
    if count <= 0:
        raise ValueError("count must be a positive integer")
    return [generate_deck() for _ in range(count)]



# --- NumPy save/load utilities ---
def save_decks_np(decks: list[list[str]], output_path: str | Path = None) -> Path:
    """
    Save decks as a single NumPy array file (.npy).
    Each deck is a list of "1"/"0" strings.
    """
    if output_path is None:
        output_path = Path(__file__).parent / "raw_decks" / "decks.npy"
    else:
        output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.array(decks)
    np.save(output_path, arr)
    return output_path

def load_decks_np(input_path: str | Path = None) -> np.ndarray:
    """
    Load decks from a NumPy .npy file.
    Returns a NumPy array of decks.
    """
    if input_path is None:
        input_path = Path(__file__).parent / "raw_decks" / "decks.npy"
    else:
        input_path = Path(input_path)
    return np.load(input_path, allow_pickle=False)

if __name__ == "__main__":
    # Number of decks to generate
    total_decks = 1000000
    output_path = Path(__file__).parent / "raw_decks" / "decks.npy"

    decks = generate_decks(total_decks)
    save_decks_np(decks, output_path)
    print(f"Saved {total_decks} decks as a NumPy array to {output_path}")