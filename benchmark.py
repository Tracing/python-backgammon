from state import State
from mcts import get_mcts_move, get_linear_default_policy
import random
import time

if __name__ == "__main__":
    random.seed(1)
    state = State()
    while state.is_nature_turn():
        state.do_move(random.choice(state.get_moves()))
    #get_mcts_move(state, 20, verbose=True, default_policy=get_linear_default_policy(1300))
    get_mcts_move(state, 20, verbose=True)
