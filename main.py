from pathlib import Path
import numpy as np

from pathlib import Path
from src.combined_current import process_both_games

# Show raw deck format and data

raw_dir = Path("data/raw_decks")
raw_files = sorted(raw_dir.glob("*.npy"))

print(f"Found {len(raw_files)} raw deck files:")


first_file = raw_files[0]

sample = np.load(first_file, allow_pickle=False)

print(f"\nFile: {first_file.name}")
print(f"Shape: {sample.shape}  (rows=decks, cols=cards)")
print(f"\nFirst 3 decks:")
for i, deck in enumerate(sample[:3]):
    print(f"  Deck {i+1}: {list(deck)}")


def main() -> None:
    '''
    Main function to process raw decks for both H-N tricks and Ron games, and print the results.
    '''
    raw_dir = Path("data/raw_decks")
    processed_dir = Path("data/processed")

    process_both_games(raw_dir=raw_dir, out_dir=processed_dir)

    hn_win_pct  = np.load(processed_dir / "hn_win_pct.npy")
    hn_draw_pct = np.load(processed_dir / "hn_draw_pct.npy")
    ron_win_pct  = np.load(processed_dir / "ron_win_pct.npy")
    ron_draw_pct = np.load(processed_dir / "ron_draw_pct.npy")

    # display the results in a readable format

    print(f"\nH-N tricks win % matrix (8x8):")
    print(np.round(hn_win_pct * 100, 1))

    print(f"\nH-N tricks draw % matrix (8x8):")
    print(np.round(hn_draw_pct * 100, 1))

    print(f"\nRon win % matrix (8x8):")
    print(np.round(ron_win_pct * 100, 1))

    print(f"\nRon draw % matrix (8x8):")
    print(np.round(ron_draw_pct * 100, 1))


if __name__ == "__main__":
    main()