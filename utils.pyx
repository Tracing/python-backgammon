from state import State
cimport cython
import numpy as np

@cython.wraparound(False)
@cython.boundscheck(False)
@cython.initializedcheck(False)
cpdef float [:, :] state_to_vector(object state):
    cdef float [:, ::1] board
    cdef float [::1] bar, beared_off

    board = np.asarray(state.get_board(), dtype=np.float32)
    bar = np.asarray(state.get_bar(), dtype=np.float32)
    beared_off = np.asarray(state.get_beared_off(), dtype=np.float32)
    return np.reshape(np.concatenate([board[0], board[1], bar, beared_off], axis=0), (1, -1))
