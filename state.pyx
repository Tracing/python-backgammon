# cython: profile=False
import array
import copy
import numpy as np
import numpy.random as np_random
cimport numpy as np
cimport numpy.random as np_random
cimport cython
from libc.stdlib cimport rand, srand, RAND_MAX
from cpython cimport array

cdef int WHITE = 0
cdef int BLACK = 1
cdef int NONE = 2

np.import_array()

cdef class Move:
    cdef public bint is_movement_move
    cdef public signed char src, dst, n, i, j
    
    def __hash__(self):
        if self.is_movement_move:
            return hash((self.src, self.dst, self.n))
        else:
            return hash((self.i, self.j))

cdef class State:
    cdef signed char [:, ::1] board
    cdef signed char [::1] bar, beared_off
    cdef int turn, turn_number, winner
    cdef bint _is_nature_turn, game_has_started
    cdef list legal_moves, _piece_moves_left
    cdef array.array _array_template
    
    def __init__(self):
        self.board = np.zeros((2, 24), dtype=np.int8)
        self.bar = np.zeros((2,), dtype=np.int8)
        self.beared_off = np.zeros((2,), dtype=np.int8)
        self.turn = NONE
        self.turn_number = 1
        self.winner = NONE
        self._is_nature_turn = True
        self.game_has_started = False
        self.legal_moves = []
        self._piece_moves_left = []
        self._array_template = array.array('i', [])
        self.reset()

    cpdef void reset(self):
        self._reset()
        self.generate_pre_game_2d6_moves()
        
    cpdef void debug_reset_board(self, signed char [:, ::1] board, signed char [::1] bar=np.zeros((2,), dtype=np.int8), signed char [::1] beared_off=np.zeros((2,), dtype=np.int8)):
        self._reset()
        self.board = np.copy(board)
        self.bar = np.copy(bar)
        self.beared_off = np.copy(beared_off)
        self.generate_pre_game_2d6_moves()

    @cython.wraparound(False)
    @cython.boundscheck(False)
    @cython.initializedcheck(False)
    def __copy__(self):
        cdef State state
        cdef Move move 
        cdef signed char x
        cdef int i, j
        state = State()
        for i in range(2):
            for j in range(24):
                state.board[i, j] = self.board[i, j]
            state.bar[i] = self.bar[i]
            state.beared_off[i] = self.beared_off[i]
        state.turn = self.turn
        state.turn_number = self.turn_number
        state.winner = self.winner
        state._is_nature_turn = self._is_nature_turn
        state.game_has_started = self.game_has_started
        if self.is_nature_turn():
            state.legal_moves = state.get_roll_2d6_moves()
        else:
            state.legal_moves = [self._new_movement_move(move.src, move.dst, move.n) for move in self.legal_moves]
        state._piece_moves_left = [x for x in self._piece_moves_left]
        return state

    cdef Move _new_movement_move(self, signed char src, signed char dst, signed char n):
        cdef Move move = Move()
        move.src = src
        move.dst = dst
        move.n = n
        move.is_movement_move = True
        return move
    
    cdef void _reset(self):
        self.board = np.zeros((2, 24), dtype=np.int8)
        self.bar = np.zeros((2,), dtype=np.int8)
        self.beared_off = np.zeros((2,), dtype=np.int8)
        self.turn = NONE
        self.turn_number = 1
        self._is_nature_turn = True
        self.game_has_started = False
        self._piece_moves_left = []
        self.winner = NONE
        #Place white pieces
        self.board[WHITE, 23] = 2
        self.board[WHITE, 12] = 5
        self.board[WHITE, 7] = 3
        self.board[WHITE, 5] = 5
        #Place black pieces
        self.board[BLACK, 0] = 2
        self.board[BLACK, 11] = 5
        self.board[BLACK, 16] = 3
        self.board[BLACK, 18] = 5

    def get_board(self):
        return np.asarray(self.board)

    def get_bar(self):
        return np.asarray(self.bar)

    def get_beared_off(self):
        return np.asarray(self.beared_off)

    cpdef int get_player_turn(self):
        return self.turn

    cpdef list get_moves(self):
        return self.legal_moves

    cpdef int get_winner(self):
        return self.winner

    cpdef bint is_nature_turn(self):
        return self._is_nature_turn

    cpdef bint has_game_started(self):
        return self.game_has_started

    cpdef void set_nature_turn(self, bint is_nature_turn):
        self._is_nature_turn = is_nature_turn

    cpdef void set_turn(self, int player):
        self.turn = player

    @cython.wraparound(False)
    @cython.boundscheck(False)    
    @cython.nonecheck(False)
    cpdef int play_game_to_end(self):
        cdef int i, n_moves
        cdef list moves
        while not self.game_ended():
            moves = self.get_moves()
            n_moves = len(moves)
            i = int(rand() / RAND_MAX * n_moves)
            self.do_move(moves[i])
        return self.get_winner()

    @cython.wraparound(False)
    @cython.boundscheck(False)    
    @cython.nonecheck(False)
    cpdef int play_game_to_depth(self, int depth):
        cdef int i, ply, n_moves
        cdef list moves
        ply = 0
        while not self.game_ended() and ply < depth:
            moves = self.get_moves()
            n_moves = len(moves)
            i = int(rand() / RAND_MAX * n_moves)
            self.do_move(moves[i])
            ply += 1
        return self.get_winner()

    @cython.wraparound(False)
    @cython.boundscheck(False)
    @cython.initializedcheck(False)
    cdef bint _has_piece(self, int point) nogil:
        """Returns True if point has a piece belonging to the player whose turn it is"""
        return self.board[self.turn, point] > 0
    
    @cython.wraparound(False)
    @cython.boundscheck(False)
    @cython.initializedcheck(False)
    cdef int _forward(self, int point, int n) nogil:
        cdef int new_point
        """Gets point n steps forward from point from the perspective of the player whose turn it is. Returns -1 if no such point exists or is unmovable"""
        new_point = point - n if self.turn == WHITE else point + n
        new_point = new_point if new_point >= 0 and new_point < 24 else -1
        if new_point != -1:
            new_point = new_point if self.board[self._other_player(), new_point] <= 1 else -1
        return new_point

    cpdef int bar_point(self):
        return -1 if self.turn == BLACK else 24

    cpdef int bearing_off_point(self):
        return -1 if self.turn == WHITE else 24

    cdef int _bar_point(self) nogil:
        return -1 if self.turn == BLACK else 24

    cdef int _bearing_off_point(self) nogil:
        return -1 if self.turn == WHITE else 24

    @cython.wraparound(False)
    @cython.boundscheck(False)
    cdef array.array _get_points_with_pieces(self):
        cdef array.array points = array.clone(self._array_template, 0, False)
        cdef int i, point
        i = 0
        for point in range(24):
            if self._has_piece(point):
                array.resize_smart(points, i + 1)
                points[i] = point
                i += 1
        return points

    @cython.wraparound(False)
    @cython.boundscheck(False)
    @cython.initializedcheck(False)
    cpdef list get_movement_moves(self):
        """Returns a list of all possible moves that can be made using the rolls from numbers obtained from a particular pair of dice"""
        cdef list legal_moves = []
        cdef int i, src, dest, n
        cdef array.array points_with_pieces = self._get_points_with_pieces()#[point for point in range(24) if self._has_piece(point)]
        for n in set(self._piece_moves_left):
            if self.bar[self.turn] > 0:
                dest = self._forward(self._bar_point(), n)
                if dest > -1:
                    legal_moves.append(self._new_movement_move(self._bar_point(), dest, n))
            else:
                if self._can_bear_off():
                    if self._has_piece(n - 1 if self.turn == WHITE else 24 - n):
                        legal_moves.append(self._new_movement_move(n - 1 if self.turn == WHITE else 24 - n, self._bearing_off_point(), n))
                for i in range(len(points_with_pieces)):
                    src = points_with_pieces[i]
                    dest = self._forward(src, n)
                    if dest > -1:
                        legal_moves.append(self._new_movement_move(src, dest, n))

        return legal_moves

    cdef void _generate_piece_moves_from_dice(self, Move dice):
        self._piece_moves_left.clear()
        if dice.i == dice.j:
            self._piece_moves_left = [dice.i] * 4
        else:
            self._piece_moves_left = [dice.i, dice.j]

    cpdef void generate_movement_moves(self):
        self.legal_moves = self.get_movement_moves()

    cpdef int other_player(self):
        return WHITE if self.turn == BLACK else BLACK if self.turn == WHITE else NONE

    cdef int _other_player(self) nogil:
        return WHITE if self.turn == BLACK else BLACK if self.turn == WHITE else NONE

    cpdef bint can_bear_off(self):
        return self._can_bear_off()

    @cython.wraparound(False)
    @cython.boundscheck(False)
    @cython.initializedcheck(False)
    cdef bint _can_bear_off(self) nogil:
        """Returns True if current player can bear off pieces"""
        cdef int lower, upper, i
        if self.turn == WHITE:
            lower = 6
            upper = 24
        else:
            lower = 0
            upper = 18

        for i in range(lower, upper, 1):
            if self.board[self.turn, i] > 0:
                return False
        return True

    @cython.wraparound(False)
    @cython.boundscheck(False)
    @cython.initializedcheck(False)
    cpdef void do_move(self, Move move):
        if self.is_nature_turn():
            if self.has_game_started():
                self._generate_piece_moves_from_dice(move)
                self.generate_movement_moves()
                self.set_nature_turn(False)
                if len(self.legal_moves) == 0:
                    self._goto_next_turn()
            else:
                if move.i == move.j:
                    self.generate_pre_game_2d6_moves()
                else:
                    if move.i > move.j:
                        self.set_turn(WHITE)
                    else:
                        self.set_turn(BLACK)
                    self.game_has_started = True
                    self._generate_piece_moves_from_dice(move)
                    self.generate_movement_moves()
                    self.set_nature_turn(False)
                    if len(self.legal_moves) == 0:
                        self._goto_next_turn()
        else:
            #Move piece
            #Moving off bar
            if move.src in [-1, 24]:
                self.bar[self.turn] -= 1
            #Movement
            else:
                self.board[self.turn, move.src] -= 1
            #Bearing off
            if move.dst in [-1, 24]:
                self.beared_off[self.turn] += 1
            #Movement
            else:
                if self.board[self._other_player(), move.dst] == 1:
                    self.bar[self._other_player()] += 1
                    self.board[self._other_player(), move.dst] = 0
                self.board[self.turn, move.dst] += 1
            self._piece_moves_left.remove(move.n)
            if len(self._piece_moves_left) == 0:
                self._goto_next_turn()
            else:
                self.generate_movement_moves()
                if len(self.legal_moves) == 0:
                    self._goto_next_turn()

    cdef void _goto_next_turn(self):
        self.check_for_winner()
        if not self.game_ended():
            self.turn = BLACK if self.turn == WHITE else WHITE
            self.set_nature_turn(True)
            self._piece_moves_left = []
            self.generate_nature_moves()
            if self.turn == WHITE:
                self.turn_number += 1

    cpdef bint game_ended(self):
        return self.winner != NONE

    cpdef bint check_for_winner(self):
        if self.n_beared_off_pieces(self.turn) == 15:
            self.winner = self.turn

    cpdef signed char n_pieces_on_bar(self, int player):
        return self.bar[player]

    cpdef signed char n_pieces_on_board(self, int player):
        return np.sum(self.board[player]) + self.bar[player]

    cpdef signed char n_beared_off_pieces(self, int player):
        return self.beared_off[player]

    cpdef void generate_pre_game_2d6_moves(self):
        self.legal_moves = self.get_roll_2d6_moves()

    cpdef void generate_nature_moves(self):
        """Generates all possible rollings of a 2d6 as the possible legal moves"""
        self.legal_moves = self.get_roll_2d6_moves()

    cpdef list get_roll_2d6_moves(self):
        """Generates all possible rollings of a 2d6."""
        cdef int i, j
        cdef Move move
        cdef list moves = []
        for i in range(1, 7):
            for j in range(1, 7):
                move = Move()
                move.i = i
                move.j = j
                move.is_movement_move = False
                moves.append(move)
        return moves
