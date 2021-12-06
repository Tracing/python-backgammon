# cython: profile=False
from state import State, Move
from utils import state_to_vector
import copy
import numpy as np
import math
import random
import time

cdef int WHITE = 0
cdef int BLACK = 1

cdef float [::1] WEIGHTS = np.asarray([-4.353895,  -4.3358836, -4.335479,  -4.3396845, -4.347475,  -4.34851,
 -4.360351,  -4.3610826, -4.3669796, -4.367299,  -4.3697615, -4.3710756,
 -4.378976,  -4.379888,  -4.3795323, -4.3825936, -4.386671,  -4.385152,
 -4.3929653, -4.393645,  -4.3977103, -4.399828,  -4.393822,  -4.4069524,
 -2.7132945, -2.7219784, -2.7184718, -2.7213256, -2.7249715, -2.7252293,
 -2.7325342, -2.734557,  -2.7386386, -2.7372847, -2.7407897, -2.7411895,
 -2.7461195, -2.7476125, -2.7517653, -2.754874,  -2.7579384, -2.7590492,
 -2.769256,  -2.7723508, -2.7798846, -2.7839608, -2.7837057, -2.7644653,
 -4.399285,  -2.7201962, -4.2949524, -2.8242497], dtype=np.float32)
cdef float INTERCEPT = 107.28579

cdef dict new_node(object state, object parent=None, object move=None):
    cdef bint _is_chance
    s = copy.copy(state)
    _is_chance = s.is_nature_turn()
    if move is not None:
        s.do_move(move)
    return {'s': s, 'r': [0.0, 0.0], 'visits': 0, 'parent': parent, 'children': {}, 'n_moves': len(state.get_moves()), 'is_chance': _is_chance}

cdef bint is_terminal(dict v):
    return v['s'].game_ended()

cdef bint fully_expanded(dict v):
    return len(untried_actions(v)) == 0

cdef dict tree_policy(dict v, double c):
    while not is_terminal(v):
        if not fully_expanded(v):
            return expand(v)
        else:
            v = best_child(v, c)[0]
    return v
        
cdef bint is_chance(dict v):
    return v['is_chance']
    
cdef list untried_actions(dict v):
    cdef object move
    return [move for move in v['s'].get_moves() if not move in v['children']]

cdef dict add_child(dict v, object move):
    v['children'][move] = new_node(v['s'], v, move)
    return v['children'][move]

cdef dict expand(dict v):
    cdef object move, a
    cdef dict v_prime
    if is_chance(v):
        for move in v['s'].get_moves():
            add_child(v, move)
        return random.choice(list(v['children'].values()))
    else:
        a = random.choice(untried_actions(v))
        v_prime = add_child(v, a)
        return v_prime
    
cdef dict get_children(dict v):
    return v['children']

cdef tuple best_child(dict v, double c):
    cdef double x, highest_x
    cdef dict best
    cdef object best_move
    cdef int turn
    x = float('-inf')
    highest_x = float('-inf')
    best = None
    best_move = None
    turn = v['s'].get_player_turn()
    if is_chance(v):
        best_move = random.choice(list(get_children(v).keys()))
        best = v['children'][best_move]
    else:
        for move in get_children(v).keys():
            v_prime = v['children'][move]
            if v_prime['visits'] == 0:
                best = v_prime
                best_move = move
                highest_x = float('inf')
            else:
                x = v_prime['r'][turn] / v_prime['visits'] + c * math.sqrt((2 * math.log(v['visits'])) / v_prime['visits'])
                if x > highest_x:
                    best = v_prime
                    best_move = move
                    highest_x = x
    return (best, best_move)

cdef list default_policy(object s):
    cdef list r
    s = copy.copy(s)
    r = [0.0, 0.0]
    r[s.play_game_to_end()] += 1.0
    return r

def get_linear_default_policy(int depth):
    cdef float [:] weights = WEIGHTS
    cdef float intercept = INTERCEPT
    cdef float max_white_r = 0.9
    cdef float min_white_r = 0.1
    def default_policy(object s):
        cdef list r
        s = copy.copy(s)
        s.play_game_to_depth(depth)
        r = [0.0, 0.0]
        if s.game_ended():
            r[s.get_winner()] += 1.0
        else:
            vector = state_to_vector(s)
            r[WHITE] = min(max(min_white_r, intercept - np.dot(vector, weights)), max_white_r)
            r[BLACK] = 1.0 - r[WHITE]            
        return r
    return default_policy

cdef void backup(dict v, list rewards):
    while v is not None:
        v['visits'] += 1
        v['r'][0] += rewards[0]
        v['r'][1] += rewards[1]
        v = v['parent']

cpdef get_mcts_move(object state, double max_time, double c=0.250, bint verbose=False, bint return_value=False, object max_rollouts=float('inf'), object default_policy=default_policy):
    cdef dict v0, vl
    cdef double start_time
    cdef object move, most_visits_move, rollouts, most_visits
    v0 = new_node(state)
    start_time = time.time()
    rollouts = 0
    while time.time() - start_time < max_time and rollouts < max_rollouts:
        vl = tree_policy(v0,  c)
        reward = default_policy(vl['s'])
        backup(vl, reward)
        rollouts += 1
    if verbose:
        print("Made {} rollouts in {:.2f} seconds".format(rollouts, time.time() - start_time))
        print("White reward at root {:.2f}".format(v0['r'][0] / v0['visits']))
        print("Black reward at root {:.2f}".format(v0['r'][1] / v0['visits']))
    if not return_value:
        most_visits_move = random.choice(state.get_moves())
        most_visits = float('-inf')
        for move in v0['children'].keys():
            if v0['children'][move]['visits'] > most_visits:
                most_visits = v0['children'][move]['visits']
                most_visits_move = move
        return most_visits_move
    else:
        return (v0['r'][0] / v0['visits'], v0['r'][1] / v0['visits'])
