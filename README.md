# Project_Penny_JEH (Hakan, Eric, and Jacob)

This project simulates and visualizes results from **two versions** of the **Humble–Nishiyama (H‑N) Randomness Game**, using a playing-card variation of **Penney’s Game**.

- **Original H‑N game (by tricks)**: score = number of **tricks** won.
- **“Ron’s” version (by cards)**: score = total number of **cards** won.

We treat a standard 52‑card deck as a sequence of **Red/Black** draws (encoded as `1` for red and `0` for black). For every ordered matchup of two 3‑card patterns, we simulate many decks and summarize results as **heatmaps**.

References (background reading):
- Penney’s Game (Wikipedia): `https://en.wikipedia.org/wiki/Penney%27s_game`
- Humble & Nishiyama paper: `https://mathwo.github.io/assets/files/penney_game/humble-nishiyama_randomness_game-a_new_variation_on_penneys_coin_game.pdf`

## What is Penney’s Game?

In the classic coin version, Player 1 chooses a length‑3 sequence of Heads/Tails (e.g., `HTH`), Player 2 chooses another length‑3 sequence, and a fair coin is flipped until one of the sequences appears first as a consecutive block.

## What is the Humble–Nishiyama Randomness Game?

Humble & Nishiyama propose a card‑deck version using **Red/Black** instead of Heads/Tails:

- Shuffle a standard 52‑card deck.
- View it only by color: **Red = 1**, **Black = 0**.
- Each player chooses a fixed **3‑card color pattern** for the whole game (one of `RRR, RRB, RBR, RBB, BRR, BRB, BBR, BBB`).

### The table mechanic (core gameplay, same for both versions)

Cards are revealed one at a time and appended to a running “table” (a growing sequence). After each card:

1. Look at the **last 3 cards** on the table.
2. If those 3 cards match **either** player’s 3‑card pattern, that player wins and the table is cleared.

So the **trigger event** is always “the last 3 cards match my pattern”, but what gets counted for the scoreboard depends on the version.

## Version A: Original H‑N (“counting tricks”)

- When my pattern matches, I win **one trick event**.
- The table is cleared (same as above).
- Final score is the total number of trick events won.

Implementation detail: trick scoring counts **+1 per match event**, even though the table may contain more than 3 cards at the moment of the match.

## Version B: Ron’s version (“counting cards”)

- Same gameplay and table clearing.
- When my pattern matches, I win **all cards currently on the table**.
- Final score is the total number of cards won across the whole deck.

This means the “cards” payout per match event can be **greater than 3**, depending on how long the table has grown since the last clear.

## Repo structure

- **`main.py`** (root): the only script you run. It lets you:
  - generate additional shuffled decks (append-only),
  - score any unprocessed decks, update arrays, and regenerate the heatmaps.
- **`src/`**
  - `src/combined_current.py`: incremental scoring for both games and writing processed results.
  - `src/heatmaps.py`: generates SVG heatmaps from processed arrays.
  - `src/ron.py`: kept for reference (older/separate Ron-only logic).
  - `src/H_N.py`: kept for reference (older/separate H‑N logic).
- **`data/`**
  - `data/data.py`: deck generation + chunked saving helpers.
  - `data/raw_decks/`: randomly generated decks saved as chunked `.npy` files (created by running `main.py`).
  - `data/processed/`: processed arrays and saved cumulative state (created by running `main.py`).
- **`figures/`**
  - `figures/ByTricks.svg`: final heatmap for the original H‑N game (“by tricks”).
  - `figures/ByRon.svg`: final heatmap for Ron’s version (“by cards”).

## How to run

From the repository root:

```bash
uv run main.py
```

You’ll see a prompt:

- Enter a **positive integer** to generate that many **new decks** and save them under `data/raw_decks/` (existing decks are never overwritten).
- Enter **0** to:
  - score any unscored decks,
  - update the processed outputs under `data/processed/`,
  - print matchup summary tables and the win/draw matrices,
  - regenerate the two heatmaps in `figures/`.

### Incremental behavior (important requirement)

If you already have \(N\) decks on disk and you generate \(k\) more, the project appends new `.npy` deck chunks and then only scores the **new** decks when you choose `0`. Previously processed data is kept via `data/processed/state.npz`.

## Outputs

### Heatmaps

The main deliverables are:

- `figures/ByTricks.svg`: “My Chance of Win(Draw) by Tricks”
- `figures/ByRon.svg`: “My Chance of Win(Draw) by Ron”

Each heatmap is an 8×8 grid:

- rows = “My Choice” (the row player’s 3‑card pattern)
- columns = “Opponent Choice” (the column player’s 3‑card pattern)
- each cell is labeled **Win(Draw)** in percent (example: `80(8)`).

### Processed arrays

When you score decks, these arrays are written to `data/processed/`:

- `hn_win_pct.npy`, `hn_draw_pct.npy` (H‑N tricks version)
- `ron_win_pct.npy`, `ron_draw_pct.npy` (Ron cards version)
- `state.npz` (cumulative counts + `decks_processed`)

The heatmap generator reads these files to build the SVGs in `figures/`.

## Findings (from our simulation results)

For the heatmaps currently in `figures/`, the simulation size is **N = 3,000,100** simulated decks (as shown in the titles embedded in `ByTricks.svg` and `ByRon.svg`).

### 1) Second-player advantage is very strong (both games)
In both heatmaps, the best “response” pattern for the responding player creates cells where the response player wins a large majority of the time, while the same response is very bad when switched with different opponent choices. You can see this directly from the contrast between the “top” cells in each row/column matchup vs the “bottom” cells (single-digit win probabilities).

Example (Tricks heatmap):
- If the opponent uses `BBB`, the strongest response is `RBB` with **99(0)**.
- If the opponent uses `BBR`, the strongest response is `RBB` with **94(4)**, while several other responses are dramatically worse (e.g., `BRR` gives **5(7)** and `RRR` gives **1(2)**).

Example (Ron-by-cards heatmap):
- If the opponent uses `BBR`, the strongest response is again `RBB` with **100(0)**.

### 2) Best response patterns (Tricks vs Ron)
Because the heatmap shows “My Chance of Win(Draw)”, we can treat the “best response” for a given opponent pattern as the `My Choice` giving the highest win percentage against that opponent choice.

#### By tricks (original H-N, scoring by tricks)
Strong best responses visible in `ByTricks.svg` include:
- Opponent `BBB` -> `RBB` **99(0)** (also strong: `RRB` **97(2)**)
- Opponent `BBR` -> `RBB` **94(4)**
- Opponent `BRB` -> `BBR` **80(8)** (also strong: `RRB` **79(9)**)
- Opponent `BRR` -> `BBR` **88(7)**
- Opponent `RBB` -> `RRB` **88(7)**
- Opponent `RBR` -> `RRB` **80(8)** (close competitor: `BBR` **79(9)**)
- Opponent `RRB` -> `BRR` **94(4)**
- Opponent `RRR` -> `BRR` **99(0)** (also strong: `BBR` **97(2)**)

#### By Ron (same gameplay, scoring by total cards won)
In `ByRon.svg`, the best responses are very similar, but the “winner” can switch in a couple cases and the best cells often become more extreme (more near-100% wins, often with 0 draws):
- Opponent `BBB` -> `RBB` **100(0)** (also strong: `RRB` **99(0)**)
- Opponent `BBR` -> `RBB` **100(0)**
- Opponent `BRB` -> `RRB` **92(1)** (note: this beats the top `BBR` value **86(1)**)
- Opponent `BRR` -> `BBR` **96(1)**
- Opponent `RBB` -> `RRB` **96(1)**
- Opponent `RBR` -> `BBR` **92(1)** (note: this flips the “best response” compared to the tricks heatmap)
- Opponent `RRB` -> `BRR` **100(0)**
- Opponent `RRR` -> `BRR` **100(0)** (also strong: `BBR` **99(0)**)

### 3) What changes when scoring by cards?
Overall, switching from “by tricks” to “by cards” does not remove the nontransitive structure, but it does affect details:
- **More extreme outcomes**: the “best response” cells often increase toward 100% wins and draws become rarer (many top cells show **(0)** or **(1)** draws).
- **Sometimes the optimal response switches**: in the data above, the best response to `BRB` and to `RBR` changes when you switch scoring (tricks prefers `BBR` vs `BRB`, and `RRB` vs `RBR`, while Ron-by-cards prefers `RRB` vs `BRB` and `BBR` vs `RBR`).

### 4) How to re-check with the latest run
To confirm the newest numbers yourself:
1. Run `uv run main.py`
2. Enter `0`
3. Use the printed matrices and open `figures/ByTricks.svg` and `figures/ByRon.svg`

