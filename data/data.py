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


def save_decks_np_chunked(decks: list[list[str]], output_dir: str | Path = None, chunk_size: int = 1000, prefix: str = "decks") -> list[Path]:
    """
    Save decks in multiple .npy files, each containing up to chunk_size decks.
    Returns a list of saved file paths.
    """
    if output_dir is None:
        output_dir = Path(__file__).parent / "raw_decks"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_files = []
    total = len(decks)
    for i, start in enumerate(range(0, total, chunk_size), 1):
        chunk = decks[start:start+chunk_size]
        file_path = output_dir / f"{prefix}_{i:04d}.npy"
        np.save(file_path, np.array(chunk))
        saved_files.append(file_path)
    return saved_files

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
    total_decks = 3_000_000
    chunk_size = 10_000
    output_dir = Path(__file__).parent / "raw_decks"

    decks = generate_decks(total_decks)
    saved_files = save_decks_np_chunked(decks, output_dir, chunk_size=chunk_size)
    print(f"Saved {total_decks} decks in {len(saved_files)} .npy files (chunk size: {chunk_size}) to {output_dir}")