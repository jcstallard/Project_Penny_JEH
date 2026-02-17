from data.data import generate_deck

def score_ron(seq1, seq2):
    player1_score = 0
    player2_score = 0

    player1_choice = seq1
    player2_choice = seq2

    for _ in range(1000000):
        deck = generate_deck()
        i = 0
        while i < len(deck) - 3: 
            if deck [i:i+3] == player1_choice:
                player1_score +=1
                i += 3
            elif deck [i:i+3] == player2_choice:
                player2_score +=1
                i += 3
            else:
                i += 1

    print(player1_score, player2_score)
