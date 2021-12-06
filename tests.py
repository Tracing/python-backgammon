from constants import WHITE, BLACK, NONE
from mcts import get_mcts_move
from state import State
import copy
import numpy as np
import random
import unittest

def to_tuple(move):
    if move.is_movement_move:
        return (move.src, move.dst, move.n)
    else:
        return (move.i, move.j)

def get_moves(state):
    return [to_tuple(move) for move in state.get_moves()]

class TestMCTS(unittest.TestCase):
    def test_nocrash(self):
        random.seed(1)
        state = State()
        while not state.game_ended():
            if state.is_nature_turn():
                move = random.choice(state.get_moves())
            else:
                move = get_mcts_move(state, 0.01)
            state.do_move(move)

    def better_than_random(self, color):
        n_games = 30
        t = 0.01
        score = 0
        threshold = 20
        for seed in range(1, n_games + 1, 1):
            random.seed(seed)
            state = State()
            while not state.game_ended():
                moves = state.get_moves()
                if state.get_player_turn() == color and not state.is_nature_turn():
                    move = get_mcts_move(state, t)
                else:
                    move = random.choice(moves)
                state.do_move(move)
            if state.get_winner() == color:
                score += 1
        self.assertGreaterEqual(score, threshold)

    def test_better_than_random(self):
        self.better_than_random(WHITE)
        self.better_than_random(BLACK)

class TestState(unittest.TestCase):
    """Application testing for the State class"""
    def assert_state(self, state: State):
        """Performs validation checks on game state"""
        #Check board
        board = state.get_board()
        bar = state.get_bar()
        beared_off = state.get_beared_off()
        n_white_pieces = np.sum(board[WHITE]) + np.sum(bar[WHITE]) + np.sum(beared_off[WHITE])
        n_black_pieces = np.sum(board[BLACK]) + np.sum(bar[BLACK]) + np.sum(beared_off[BLACK])
        self.assertEqual(n_white_pieces, 15)
        self.assertEqual(n_black_pieces, 15)
        self.assertGreaterEqual(np.min(board), 0)
        self.assertGreaterEqual(np.min(bar), 0)
        self.assertGreaterEqual(np.min(beared_off), 0)

    def assert_state_action(self, state: State, action: tuple):
        """Performs validation checks on action when applied to state 'state'"""
        #Check board
        if state.has_game_started():
            if state.is_nature_turn():
                self.assertGreaterEqual(action.i, 1)
                self.assertGreaterEqual(action.j, 1)
                self.assertLessEqual(action.i, 6)
                self.assertLessEqual(action.j, 6)
            else:
                self.assertGreaterEqual(action.src, -1)
                self.assertGreaterEqual(action.dst, -1)
                self.assertGreaterEqual(action.n, 1)
                self.assertLessEqual(action.src, 24)
                self.assertLessEqual(action.dst, 24)
                self.assertLessEqual(action.n, 6)
                #Movement
                #If no pieces on the bar, pieces must go off the bar
                if state.n_pieces_on_bar(state.get_player_turn()) > 0:
                    self.assertEqual(action.src, state.bar_point())
                    self.assertNotEqual(action.dst, state.bar_point())
                #Don't bear off if can't bear off
                if not state.can_bear_off():
                    self.assertNotEqual(action.dst, state.bearing_off_point)
                #piece must move forwards by the right amount of spaces
        else:
            if state.is_nature_turn():
                self.assertGreaterEqual(action.i, 1)
                self.assertGreaterEqual(action.j, 1)
                self.assertLessEqual(action.i, 6)
                self.assertLessEqual(action.j, 6)
            else:
                #Should never happen
                self.assertTrue(False)

    def assert_state_action_next_state(self, state: State, action: tuple):
        """Performs validation checks on the state that is produced when action is applied to state 'state'"""
        next_state = copy.copy(state)
        next_state.do_move(action)
        self.assertTrue(state != next_state)
        if state.has_game_started():
            self.assertTrue(next_state.has_game_started())
            if state.is_nature_turn():
                self.assertTrue((not next_state.is_nature_turn()) or (state.get_player_turn() != next_state.get_player_turn()))
            else:
                (src, dst, n) = (action.src, action.dst, action.n)
                #Moving off bar
                if src in [-1, 24]:
                    self.assertEqual(state.get_bar()[state.get_player_turn()], next_state.get_bar()[state.get_player_turn()] + 1)
                    self.assertEqual(state.get_board()[state.get_player_turn(), dst], next_state.get_board()[state.get_player_turn(), dst] - 1)
                #Bearing off
                elif dst in [-1, 24]:
                    #One less piece on src
                    self.assertEqual(state.get_board()[state.get_player_turn(), src], next_state.get_board()[state.get_player_turn(), src] + 1)
                    self.assertEqual(state.get_board()[state.get_player_turn(), src], next_state.get_board()[state.get_player_turn(), src] + 1)
                    self.assertEqual(state.get_beared_off()[state.get_player_turn()], next_state.get_beared_off()[state.get_player_turn()] - 1)
                #Movement
                else:
                    #One less piece on src
                    self.assertEqual(state.get_board()[state.get_player_turn(), src], next_state.get_board()[state.get_player_turn(), src] + 1)
                    #One more piece on dst square
                    self.assertEqual(state.get_board()[state.get_player_turn(), dst], next_state.get_board()[state.get_player_turn(), dst] - 1)
                    #If one piece
                    if state.get_board()[state.other_player(), dst] == 1:
                        self.assertEqual(next_state.get_board()[state.other_player(), dst], 0)
        else:
            if action.i != action.j:
                self.assertTrue(next_state.has_game_started())
                self.assertFalse(next_state.is_nature_turn())
            else:
                self.assertFalse(next_state.has_game_started())
                self.assertTrue(next_state.is_nature_turn())
                
    def assert_moves_are_dice_rolls(self, moves: list):
        self.assertEqual(len(moves), 36)
        for move in moves:
            self.assertEqual(len(move), 2)
            self.assertTrue(isinstance(move, tuple))
        moves_2 = [(x, y) for y in range(1, 7) for x in range(1, 7)]
        for move in moves_2:
            self.assertIn(move, moves)

    def test_game_nocrash(self):
        n_seeds = 20
        for seed in range(1, n_seeds + 1):
            random.seed(seed)
            #Succeeds if no exceptions raised
            state = State()
            while not state.game_ended():
                moves = state.get_moves()
                state.do_move(random.choice(moves))

    def test_random_game_statistics(self):
        n_seeds = 20000
        wins = [0, 0]
        for seed in range(1, n_seeds + 1):
            random.seed(seed)
            #Succeeds if no exceptions raised
            state = State()
            while not state.game_ended():
                moves = state.get_moves()
                state.do_move(random.choice(moves))
            wins[state.get_winner()] += 1
        ratio = max(wins) / sum(wins)
        self.assertGreaterEqual(ratio, 0.40)
        self.assertLessEqual(ratio, 0.60)

    def test_game_all_states(self):
        n_seeds = 20
        for seed in range(1, n_seeds + 1):
            random.seed(seed)
            state = State()
            while not state.game_ended():
                self.assert_state(state)
                moves = state.get_moves()
                state.do_move(random.choice(moves))
            self.assertEqual(state.game_ended(), True)

    def test_game_state_action(self):
        n_seeds = 20
        for seed in range(1, n_seeds + 1):
            random.seed(seed)
            state = State()
            while not state.game_ended():
                moves = state.get_moves()
                move = random.choice(moves)
                self.assert_state_action(state, move)
                state.do_move(move)

    def test_game_action_applied_to_state(self):
        n_seeds = 20
        for seed in range(1, n_seeds + 1):
            random.seed(seed)
            state = State()
            while not state.game_ended():
                moves = state.get_moves()
                move = random.choice(moves)
                self.assert_state_action_next_state(state, move)
                state.do_move(move)

    def test_game_move_generation(self):
        state = State()
        #Test blue sky pre-game
        #Test normal, blocked, black
        #Test blot, white
        #Test bar
        #Test bar, white
        board = np.zeros((2, 24), dtype=np.int8)
        board[0, 12] = 13
        board[1, 8] = 15
        bar = np.zeros((2,), dtype=np.int8)
        bar[0] = 2
        beared_off = np.zeros((2,), dtype=np.int8)
        state.debug_reset_board(board, bar, beared_off)
        state.do_move((6, 3))
        self.assertSequenceEqual(sorted(get_moves(state)), sorted([(state.bar_point(), 21, 3), (state.bar_point(), 18, 6)]))
        #Test bar, black
        board = np.zeros((2, 24), dtype=np.int8)
        board[1, 12] = 13
        board[0, 8] = 15
        bar = np.zeros((2,), dtype=np.int8)
        bar[1] = 2
        beared_off = np.zeros((2,), dtype=np.int8)
        state.debug_reset_board(board, bar, beared_off)
        state.do_move((3, 6))
        self.assertSequenceEqual(sorted(get_moves(state)), sorted([(state.bar_point(), 2, 3), (state.bar_point(), 5, 6)]))        
        #Test cant bear off, white
        board = np.zeros((2, 24), dtype=np.int8)
        board[0, 3] = 11
        board[0, 7] = 4
        board[1, 8] = 15
        bar = np.zeros((2,), dtype=np.int8)
        beared_off = np.zeros((2,), dtype=np.int8)
        state.debug_reset_board(board, bar, beared_off)
        state.do_move((4, 1))
        self.assertNotIn((3, -1, 4), get_moves(state))
        #Test cant bear off, black
        board = np.zeros((2, 24), dtype=np.int8)
        board[1, 21] = 11
        board[1, 7] = 4
        board[0, 8] = 15
        bar = np.zeros((2,), dtype=np.int8)
        beared_off = np.zeros((2,), dtype=np.int8)
        state.debug_reset_board(board, bar, beared_off)
        state.do_move((1, 3))
        self.assertNotIn((21, 24, 3), get_moves(state))
        #Test bear off, white
        board = np.zeros((2, 24), dtype=np.int8)
        board[0, 3] = 11
        board[1, 8] = 15
        bar = np.zeros((2,), dtype=np.int8)
        beared_off = np.zeros((2,), dtype=np.int8)
        beared_off[0] = 4
        state.debug_reset_board(board, bar, beared_off)
        state.do_move((4, 1))
        self.assertSequenceEqual([(3, -1, 4)], get_moves(state))
        #Test bear off, black
        board = np.zeros((2, 24), dtype=np.int8)
        board[0, 3] = 15
        board[1, 22] = 10
        bar = np.zeros((2,), dtype=np.int8)
        beared_off = np.zeros((2,), dtype=np.int8)
        beared_off[1] = 5
        state.debug_reset_board(board, bar, beared_off)
        state.do_move((1, 2))
        self.assertSequenceEqual([(22, 24, 2)], get_moves(state))
        #Test no moves
        board = np.zeros((2, 24), dtype=np.int8)
        board[0, 10] = 15
        board[1, 9] = 10
        board[1, 8] = 5
        bar = np.zeros((2,), dtype=np.int8)
        beared_off = np.zeros((2,), dtype=np.int8)
        state.debug_reset_board(board, bar, beared_off)
        state.do_move((2, 1))
        self.assert_moves_are_dice_rolls(get_moves(state))
        self.assertEqual(state.get_player_turn(), BLACK)
        self.assertTrue(state.is_nature_turn())
        #Test doubles

        #Test doubles pre-game

if __name__ == "__main__":
    unittest.main()
