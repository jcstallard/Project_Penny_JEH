
"""
heatmaps.py

This script generates SVG heatmaps for both the H-N tricks and Ron games using processed results.
Each cell is formatted as Win(Draw) in percent, colored by win percentage, and labeled as required.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Any

# Strategy labels in the required order for both axes
STRATEGY_LABELS: list[str] = [
    "BBB", "BBR", "BRB", "BRR", "RBB", "RBR", "RRB", "RRR"
]

# Output and data directories
FIGURES_DIR: Path = Path("figures")
PROCESSED_DIR: Path = Path("data/processed")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def format_cell(win: float, draw: float) -> str:
    """
    Format a cell as Win(Draw), both as integer percentages.
    """
    return f"{int(round(win))}({int(round(draw))})"

def plot_heatmap(
    win_pct: np.ndarray,
    draw_pct: np.ndarray,
    title: str,
    filename: str
) -> None:
    """
    Plot and save a heatmap for win/draw percentages.
    Args:
        win_pct: 2D array of win percentages (0-1)
        draw_pct: 2D array of draw percentages (0-1)
        title: Title for the plot
        filename: Output SVG filename
    """
    win_pct_100 = win_pct * 100
    draw_pct_100 = draw_pct * 100
    annot: np.ndarray[Any, np.dtype[str]] = np.empty(win_pct.shape, dtype=object)
    for i in range(win_pct.shape[0]):
        for j in range(win_pct.shape[1]):
            annot[i, j] = format_cell(win_pct_100[i, j], draw_pct_100[i, j])

    plt.figure(figsize=(8, 8))
    ax = sns.heatmap(
        win_pct_100,
        annot=annot,
        fmt="",
        cmap="Blues",
        cbar=True,
        linewidths=1,
        linecolor="#eeeeee",
        square=True,
        xticklabels=STRATEGY_LABELS,
        yticklabels=STRATEGY_LABELS,
        annot_kws={"fontsize": 11, "weight": "bold"}
    )
    ax.set_xlabel("My Choice", fontsize=13)
    ax.set_ylabel("Opponent Choice", fontsize=13)
    ax.set_title(title, fontsize=15, weight="bold", pad=20)
    plt.yticks(rotation=0)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / filename, format="svg")
    plt.close()

def main() -> None:
    """
    Main function to load processed results and generate heatmaps for both games.
    """
    # Load processed win/draw percentage arrays
    hn_win_pct: np.ndarray = np.load(PROCESSED_DIR / "hn_win_pct.npy")
    hn_draw_pct: np.ndarray = np.load(PROCESSED_DIR / "hn_draw_pct.npy")
    ron_win_pct: np.ndarray = np.load(PROCESSED_DIR / "ron_win_pct.npy")
    ron_draw_pct: np.ndarray = np.load(PROCESSED_DIR / "ron_draw_pct.npy")

    # Remap from STRATEGIES order (RRR..BBB) to STRATEGY_LABELS order (BBB..RRR)
    # and transpose so rows=opponent, cols=me shows "my" win percentage
    hn_win_pct  = hn_win_pct[::-1, ::-1].T
    hn_draw_pct = hn_draw_pct[::-1, ::-1].T
    ron_win_pct = ron_win_pct[::-1, ::-1].T
    ron_draw_pct = ron_draw_pct[::-1, ::-1].T

    # Get number of decks processed for the title
    state = np.load(PROCESSED_DIR / "state.npz")
    N: int = int(state["decks_processed"])

    # Generate and save heatmap for H-N tricks
    plot_heatmap(
        hn_win_pct,
        hn_draw_pct,
        f"My Chance of Win(Draw)\nby Tricks\nN={N:,}",
        "ByTricks.svg"
    )
    # Generate and save heatmap for Ron
    plot_heatmap(
        ron_win_pct,
        ron_draw_pct,
        f"My Chance of Win(Draw)\nby Ron\nN={N:,}",
        "ByRon.svg"
    )
    print(f"Heatmaps saved to {FIGURES_DIR.resolve()}")

if __name__ == "__main__":
    main()
