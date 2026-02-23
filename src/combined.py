# how do i load the deck from the data file? do I need to? 


def score_ron(deck: list[str], player1_choice: list[str], player2_choice: list[str]) -> tuple[int, int]:
    """
    This function will score a single deck. 
    Players will win cards in groups of 3 when their chosen sequence appears at the current
    position. Finally, the player with more cards at the end wins. 
    
    The function will return a tuple of (player1_score, player2_score).
    """

    # pull up some sort of raw data and partially processed data. 


    player1_score = 0
    player2_score = 0

    i = 0

    while i <= len(deck) - 3:
        grab_cards = deck[i:i+3] # grabs the next 3 cards of the deck

        if grab_cards == player1_choice:
            player1_score += 3
            i += 3
        elif grab_cards == player2_choice:
            player2_score += 3
            i += 3
        else:
            i += 1

    return player1_score, player2_score

def simulate_ron_game(decks: list[list[str]], player1_choice: list[str], player2_choice: list[str]) -> list[tuple[int, int]]:
    """
    Simulate the game across many decks. 
    It returns wins for player1, draws, wins for player2.
    """

    wins1 = 0
    wins2 = 0
    draws = 0

    for deck in decks:
        score1, score2 = score_ron(deck, player1_choice, player2_choice ) # here I am using the previous score_ron for only one deck of cards.

        if score1 > score2:
            wins1 += 1
        elif score2 > score1:
            wins2 += 1
        else:
            draws += 1

        # add Eric's logic 

    return wins1, draws, wins2
    



# save them to processed data. The scores for each deck. 