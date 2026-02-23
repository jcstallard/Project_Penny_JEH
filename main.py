'''
from data.data import generate_deck
from src.ron import score_ron


seq1 = input("Player 1, enter your sequence: ")

seq2 = input("Player 2, enter your sequence: ")
'''


from pathlib import Path
from src.H_N import process_new_raw_decks, export_final_arrays

def main():
    raw_dir = Path("data/raw_decks")
    processed_dir = Path("data/processed")

    state = process_new_raw_decks(raw_dir, processed_dir, prefix="raw_decks")
    export_final_arrays(processed_dir, state)

    print(f"Total decks processed: {state.total}")

if __name__ == "__main__":
    main()