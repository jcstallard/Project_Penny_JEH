# Project_Penny_JEH (Hakan, Eric, and Jacob)

This repo is for our DATA 440 project on **Penney’s Game** and the **Humble–Nishiyama Randomness Game** using a standard 52‑card deck.

We simulate a lot of random decks, run **two different scoring rules**, and visualize the results as heatmaps:

- **Original H‑N game (“by tricks”)** – score = number of tricks you win  
- **Ron’s version (“by cards”)** – score = total number of cards you win  

In both versions, players choose fixed 3‑card color patterns like `RBB` or `BRR`, and we look at how often “my” pattern beats the opponent’s pattern.

---

## 1. Background

### 1.1 Penney’s Game (coin version)

Penney’s Game is a probability game with a fair coin:

- Player 1 picks a sequence of 3 flips, like `HHT`.
- Player 2 then picks a *different* sequence of 3 flips, like `THH`.
- We flip a coin repeatedly and write down the sequence.
- Whoever’s pattern shows up **first** as a consecutive block wins.

The surprising fact is that this game is **nontransitive**:  
for any sequence Player 1 chooses, Player 2 can respond with a different sequence that’s actually **more likely** to appear first. So going second is a real advantage.

For background:
- Penney’s Game (Wikipedia): `https://en.wikipedia.org/wiki/Penney%27s_game`

### 1.2 Humble–Nishiyama Randomness Game (card version)

Humble and Nishiyama move the idea to playing cards. Instead of coins, we use **Red/Black**:

- Shuffle a standard 52‑card deck.
- Ignore suits/ranks; just use color:
  - Red = `1`
  - Black = `0`
- Each player locks in a **3‑card color pattern** for the entire game. We use:
  - `RRR, RRB, RBR, RBB, BRR, BRB, BBR, BBB`
- Turn over cards one at a time, forming a color sequence.
- Whenever the last 3 cards match a player’s pattern, that player wins a **trick**:
  - Those 3 cards are removed from the table and go into that player’s pile.
  - Then we keep going with the remaining undealt cards.
- We repeat until the deck is exhausted.

This is the **original H‑N scoring**: whoever has more tricks wins.

The short paper is here:
- Humble & Nishiyama:  
  `https://mathwo.github.io/assets/files/penney_game/humble-nishiyama_randomness_game-a_new_variation_on_penneys_coin_game.pdf`

### 1.3 Ron’s version (by cards)

Our project also studies a second scoring rule that we call **Ron’s version**:

- Pattern detection and tricks are the same as above.
- The only change is **how we score**:
  - we count **cards**, not tricks.
  - each trick is still 3 cards, so your score is total cards collected.

So:

- **Trick version (original H‑N)**: “I got 7 tricks vs 3 tricks.”
- **Card version (Ron)**: “I got 21 cards vs 9 cards.”

We want to see if this simple change in scoring makes any difference in who has the advantage.

---

## 2. Repo structure

- **`main.py`**  
  Entry point for the whole project. This is the **only** `.py` file in the repo root. It:
  - lets you generate more random decks,
  - scores all unprocessed decks for **both** games,
  - and then regenerates the heatmaps.

- **`src/`**
  - `src/combined_current.py` – main simulation logic:
    - loads decks from `data/raw_decks/`,
    - scores all 8×8 pattern matchups,
    - does both H‑N (tricks) and Ron (cards) at the same time,
    - saves running totals + percentages.
  - `src/heatmaps.py` – reads processed arrays and makes the two SVG heatmaps.
  - `src/ron.py` – older/separate Ron‑only processor (kept for reference).
  - `src/H_N.py` – older/separate H‑N (tricks) processor (also kept for reference).

- **`data/`**
  - `data/data.py` – helper functions for:
    - generating random decks (26 red, 26 black, shuffled),
    - saving them as chunked `.npy` files.
  - `data/raw_decks/` – all generated decks as:
    - `decks_0001.npy`, `decks_0002.npy`, …, up to `decks_0310.npy`, etc.
    - We never overwrite these files.
  - `data/processed/` – summary stats:
    - `state.npz` – running counts of wins/draws + `decks_processed`.
    - `hn_win_pct.npy`, `hn_draw_pct.npy`
    - `ron_win_pct.npy`, `ron_draw_pct.npy`

- **`figures/`**
  - `ByTricks.svg` – heatmap for **“My Chance of Win(Draw) by Tricks”**.
  - `ByRon.svg` – heatmap for **“My Chance of Win(Draw) by Ron”**.

---

## 3. How to run it

From the project root:

```bash
uv run main.py
```

The script will:

1. Count how many decks are already **analyzed** vs how many are just sitting in `data/raw_decks/`.
2. Ask you for an integer:

   - If you enter a **positive integer** (like `1000`):
     - it generates that many new random decks,
     - saves them into `data/raw_decks/` as new files,
     - then calls `main()` again so you can decide what to do next.

   - If you enter **`0`**:
     - it scores all **unprocessed** decks for:
       - original H‑N (by tricks),
       - Ron’s version (by cards),
     - updates everything in `data/processed/`,
     - prints out:
       - how many decks have been analyzed total,
       - a big table of wins and ties for both games,
       - the 8×8 win and draw percentage matrices,
     - and regenerates the two heatmaps in `figures/`.

### Incremental behavior (no wasted work)

The project is designed to **never throw away** work:

- Raw decks in `data/raw_decks/` are append‑only.
- `state.npz` remembers how many decks have already been scored.
- When you add more decks and then choose `0`, we only score the **new** decks and update totals.

If we already have 3,000,000 decks processed and add 100 more, we end up with stats based on **3,000,100** decks without recomputing the first 3 million.

---

## 4. Outputs

### 4.1 Heatmaps

The main visuals are:

- `figures/ByTricks.svg` – original H‑N game (tricks).
- `figures/ByRon.svg` – Ron’s game (cards).

Each is an 8×8 grid:

- rows = “My Choice” (my 3‑card pattern),
- columns = “Opponent Choice” (their pattern),
- each cell label is `Win(Draw)` in percent, e.g. `80(8)`.

The titles of the SVGs show the number of decks used in the stats.  
In the versions checked in, both say:

- `N = 3,000,000`

So all percentages are based on 3 million simulated decks.

### 4.2 Processed arrays

Under `data/processed/`:

- `hn_win_pct.npy`, `hn_draw_pct.npy` – for the H‑N trick game.
- `ron_win_pct.npy`, `ron_draw_pct.npy` – for Ron’s card game.
- `state.npz` – all raw counts + `decks_processed`.

`src/heatmaps.py` reads these to build the figures.

---

## 5. What we found (high‑level summary)

Based on 3,000,000 decks:

- **Going second is very strong** in both scoring systems.  
  If Player 2 picks a “best response” pattern against Player 1’s choice (like in the Penney’s Game tables), their win percentage is often very high (frequently in the 70–95% range). This lines up with the Humble–Nishiyama paper.

- **Changing from tricks to cards doesn’t change the big picture.**  
  Switching from counting tricks to counting cards:
  - keeps the nontransitive structure,
  - keeps the strong second‑player advantage,
  - but does tweak the exact win and draw percentages in some matchups.

- **Some starting patterns are clearly bad.**  
  Looking across rows in the heatmaps, a few patterns consistently perform poorly when the opponent responds optimally, in both versions of the game.

To see exact numbers yourself:

1. Run `uv run main.py`.
2. Enter `0`.
3. Look at the printed matrices and open `figures/ByTricks.svg` and `figures/ByRon.svg`.

Overall, the project confirms the idea from the paper:  
the Humble–Nishiyama card game, like Penney’s Game, strongly favors the **second player**, and that advantage survives even when we change the scoring rule from tricks to cards.

