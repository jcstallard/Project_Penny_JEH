import random
import itertools

def generate_deck() -> list:
    deck = ['1'] * 26 + ['0'] * 26 # 1 for red, 0 for black
    random.shuffle(deck)
    return deck



