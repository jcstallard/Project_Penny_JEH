import random
import itertools

def generate_deck():
    deck = ['1'] * 26 + ['0'] * 26
    random.shuffle(deck)
    return deck

print(generate_deck())

