'''
from data.data import generate_deck
from src.ron import score_ron
'''



'''
from __future__ import annotations

from pathlib import Path
from src.combined1 import process_both_versions


def main() -> None:
    # Update these if your folders differ
    raw_dir = Path("data/raw_decks")      # where decks_0001.npy etc live
    processed_dir = Path("data/processed")   # where summary files will be written
    
    # Your generator uses prefix="decks" -> decks_0001.npy ...
    process_both_versions(raw_dir=raw_dir, processed_dir=processed_dir, prefix="raw_decks")


if __name__ == "__main__":
    main()
'''

from pathlib import Path
from src.combined import process_both_versions

def main() -> None:
    project_root = Path(__file__).parent.resolve()

    raw_dir = project_root / "data" / "raw_decks"
    processed_dir = project_root / "data" / "processed"

    process_both_versions(raw_dir=raw_dir, processed_dir=processed_dir, prefix="decks")

if __name__ == "__main__":
    main()