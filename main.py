from pathlib import Path
import numpy as np
from pathlib import Path
from data.data import generate_decks, save_decks_np_chunked
from src.combined_current import process_both_games
from src.heatmaps import main as generate_heatmaps


LABELS = ["RRR", "RRB", "RBR", "RBB", "BRR", "BRB", "BBR", "BBB"]

def print_results_table(processed_dir: Path) -> None:
    """
    Print a table of wins and ties for each matchup across both games.
    """
    saved     = np.load(processed_dir / "state.npz")
    ron_wins1 = saved["ron_wins1"]
    ron_draws = saved["ron_draws"]
    hn_wins1  = saved["hn_wins1"]
    hn_draws  = saved["hn_draws"]

    print(f"\n{'Choices':<12} {'HN Wins':>10} {'HN Ties':>10} {'Ron Wins':>10} {'Ron Ties':>10}")
    print("-" * 55)

    for i, label1 in enumerate(LABELS):
        for j, label2 in enumerate(LABELS):
            if i == j:
                continue
            print(
                f"{label1} vs {label2:<6}"
                f"{int(hn_wins1[i,j]):>10}"
                f"{int(hn_draws[i,j]):>10}"
                f"{int(ron_wins1[i,j]):>10}"
                f"{int(ron_draws[i,j]):>10}"
            )

def main() -> None:
    '''
    Main function to process raw decks for both H-N tricks and Ron games, and print the results.
    '''
    raw_dir = Path("data/raw_decks")
    processed_dir = Path("data/processed")

    state_path = processed_dir / "state.npz"

    # count already processed decks
    if state_path.exists():
        already_processed = int(np.load(state_path)["decks_processed"])
    else:
        already_processed = 0

    
    # Count total raw decks available on disk
    total_raw = sum(
        len(np.load(p, allow_pickle=False))
        for p in sorted(raw_dir.glob("*.npy"))
    )

    unscored = total_raw - already_processed

    print(f"There are currently {already_processed:,} decks that have been analyzed.")
    print(f"There are {unscored:,} decks that need to be scored.")
    print("If you would like to create additional decks, enter a positive integer.")
    print("Enter 0 to update all scores and figures and quit.")

    choice = int(input("Please enter your selection:").strip())

    if choice > 0:
        print(f"Generating {choice:,} new decks...")
        new_decks = generate_decks(choice)
        save_decks_np_chunked(new_decks, raw_dir)
        print(f"Done. {choice:,} new decks saved.")
        main()

    elif choice == 0:
        print("Updating scores...")
        process_both_games(raw_dir=raw_dir, out_dir=processed_dir)
        print_results_table(processed_dir)

        hn_win_pct   = np.load(processed_dir / "hn_win_pct.npy")
        hn_draw_pct  = np.load(processed_dir / "hn_draw_pct.npy")
        ron_win_pct  = np.load(processed_dir / "ron_win_pct.npy")
        ron_draw_pct = np.load(processed_dir / "ron_draw_pct.npy")

        print(f"\nH-N tricks win % matrix (8x8):")
        print(np.round(hn_win_pct * 100, 1))

        print(f"\nH-N tricks draw % matrix (8x8):")
        print(np.round(hn_draw_pct * 100, 1))

        print(f"\nRon win % matrix (8x8):")
        print(np.round(ron_win_pct * 100, 1))

        print(f"\nRon draw % matrix (8x8):")
        print(np.round(ron_draw_pct * 100, 1))

        generate_heatmaps()
        print("\nDone! Updated heatmaps are located in figures/")


if __name__ == "__main__":
    main()