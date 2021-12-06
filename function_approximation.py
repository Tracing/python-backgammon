from mcts import get_mcts_move
from state import State
import csv
import copy
import itertools
import math
import numpy as np
import random

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, cross_validate

def state_to_vector(state):
    board = state.get_board()
    bar = state.get_bar()
    beared_off = state.get_beared_off()
    x = np.empty(26, dtype=np.float32)
    for i in range(24):
        x[i] = board[0, i] - board[1, i]
    x[24] = bar[0] - bar[1]
    x[25] = beared_off[0] - beared_off[1]
    return list(x)

def create_dataset(n_games, positions_per_game, mcts_c, mcts_t, out_filename):
    positions = []
    values = []

    for i in range(n_games):
        print("{}/{}".format(i + 1, n_games))
        states = []
        state = State()
        while not state.game_ended():
            states.append(copy.copy(state))
            moves = state.get_moves()
            state.do_move(random.choice(moves))
        states = random.sample(states, positions_per_game)
        for state in states:
            positions.append(state_to_vector(state))
            #Saves probability of white winning
            values.append(get_mcts_move(state, mcts_t, mcts_c, return_value=True)[0])

    with open("{}".format(out_filename), "w") as f:
        writer = csv.writer(f)
        for (i, position) in enumerate(positions):
            writer.writerow(itertools.chain(position, [values[i]]))
    #xs = np.concatenate(positions, axis=0)
    #ys = np.asarray(values, dtype=np.float32)
    
    #np.save(filename_xs, xs)
    #np.save(filename_ys, ys)

create_dataset(4000, 1, math.sqrt(2), 1, "train2.csv")