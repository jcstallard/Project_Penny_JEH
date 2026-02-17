from __future__ import annotations

import json
import random
from pathlib import Path


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


def save_decks(
    decks: list[list[str]],
    output_dir: str | Path,
    chunk_size: int = 10_000,
    prefix: str = "raw_decks",
) -> list[Path]:
    """
    Save decks as JSONL files in chunked, 
    append-only batches. Each line is a JSON 
    array of "1"/"0" strings representing one 
    deck.New files are created sequentially 
    so existing data is never touched.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    existing = sorted(output_path.glob(f"{prefix}_*.jsonl"))
    next_index = len(existing) + 1

    saved_files: list[Path] = []
    for start in range(0, len(decks), chunk_size):
        chunk = decks[start : start + chunk_size]
        file_path = output_path / f"{prefix}_{next_index:04d}.jsonl"
        with file_path.open("w", encoding="utf-8") as handle:
            for deck in chunk:
                handle.write(json.dumps(deck))
                handle.write("\n")
        saved_files.append(file_path)
        next_index += 1

    return saved_files

