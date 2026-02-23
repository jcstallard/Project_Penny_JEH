"""
hn_tricks.py

This file contains the actual rules of the original
Humble–Nishiyama game (scored by number of tricks).

Quick summary of the game:
- Each player picks a 3-color pattern (like "RBR").
- We flip through a shuffled 52-card deck (R/B only).
- Cards go face-up onto the table one at a time.
- As soon as the last three cards match someone's pattern,
  that player wins a "trick" and takes all cards on the table.
- The table is cleared and we continue with the remaining deck.
- Whoever wins more tricks wins the game.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Literal

Player = Literal["A", "B", "DRAW"]


def _validate_seq(seq: str) -> str:
    """
    Make sure the sequence is exactly length 3 and contains only R or B.

    I validate early so that bugs don't silently propagate.
    """

    s = seq.strip().upper()

    if len(s) != 3:
        raise ValueError("Sequences must be length 3.")

    if any(ch not in ("R", "B") for ch in s):
        raise ValueError("Sequences must contain only 'R' or 'B'.")

    return s


@dataclass(frozen=True)
class TricksOutcome:
    """
    Stores how many tricks each player won for one deck.
    """

    tricks_a: int
    tricks_b: int

    @property
    def winner(self) -> Player:
        if self.tricks_a > self.tricks_b:
            return "A"
        if self.tricks_b > self.tricks_a:
            return "B"
        return "DRAW"


def play_deck_tricks(deck: Iterable[str], seq_a: str, seq_b: str) -> TricksOutcome:
    """
    Run the full game for one deck using trick scoring.
    """

    a = _validate_seq(seq_a)
    b = _validate_seq(seq_b)

    if a == b:
        raise ValueError("Players must choose different sequences.")

    table: list[str] = []
    tricks_a = 0
    tricks_b = 0

    for card in deck:
        table.append(card)

        # We only start checking once we have at least 3 cards
        if len(table) >= 3:
            last_three = "".join(table[-3:])

            if last_three == a:
                tricks_a += 1
                table.clear()  # winner takes all cards on table

            elif last_three == b:
                tricks_b += 1
                table.clear()

    # If the deck ends with leftover cards on the table,
    # they do NOT count as a trick.
    # A trick only happens when a pattern appears.

    return TricksOutcome(tricks_a=tricks_a, tricks_b=tricks_b)


    