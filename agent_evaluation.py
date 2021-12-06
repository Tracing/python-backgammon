import copy
import elo
import numpy as np
import random
from mcts import get_mcts_move, get_linear_default_policy
from state import State, Move

#Best Vanilla paramters for t=0.1 -> c=0.25
#Best Linear paramters for t=0.1 -> c=1.0, depth=1300

WHITE = 0
BLACK = 1

def get_random_non_starting_state():
    state = State()
    all_states = []
    while not state.game_ended():
        state.do_move(random.choice(state.get_moves()))
        all_states.append(copy.copy(state))
    return random.choice(all_states)

class Agent:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    def get_move(self, state: State):
        raise NotImplementedError()

    def get_state_value(self, state: State):
        raise NotImplementedError()

    def setup(self):
        pass

    def teardown(self):
        pass

    def post_move_hook(self):
        pass

class MCTSAgent(Agent):
    def __init__(self, name: str, c: float, t: float):
        self.c = c
        self.t = t
        super().__init__(name)

    def get_move(self, state: State):
        return get_mcts_move(state, self.t, c=self.c)

    def get_state_value(self, state: State):
        return get_mcts_move(state, self.t, c=self.c, return_value=True)[0]

class MCTSLinearApproximationAgent(Agent):
    def __init__(self, name: str, c: float, t: float, depth: int):
        self.c = c
        self.t = t
        self.depth = depth
        self._default_policy = get_linear_default_policy(depth)
        super().__init__(name)

    def get_move(self, state: State):
        return get_mcts_move(state, self.t, c=self.c, default_policy=self._default_policy)

    def get_state_value(self, state: State):
        return get_mcts_move(state, self.t, c=self.c, default_policy=self._default_policy, return_value=True)[0]

class RandomAgent(Agent):
    def get_move(self, state: State):
        return random.choice(state.get_moves())

class Tournament:
    def __init__(self, agents: list):
        self.agents = agents
        self._elo = elo.setup(k_factor=100)
        self.ratings = [elo.Rating(1200) for _ in agents]
        self.n_games_played = [0 for _ in agents]

    def _play_game(self, agent1_index: int, agent2_index: int):
        assert agent1_index != agent2_index
        agent1 = self.agents[agent1_index]
        agent2 = self.agents[agent2_index]
        state = State()
        while not state.game_ended():
            if state.is_nature_turn():
                move = random.choice(state.get_moves())
            elif state.get_player_turn() == WHITE:
                move = agent1.get_move(state)
            else:
                assert state.get_player_turn() == BLACK
                move = agent2.get_move(state)
            state.do_move(move)
        self.n_games_played[agent1_index] += 1
        self.n_games_played[agent2_index] += 1
        if state.get_winner() == WHITE:
            (self.ratings[agent1_index], self.ratings[agent2_index]) = self._elo.rate_1vs1(self.ratings[agent1_index], self.ratings[agent2_index])
        else:
            (self.ratings[agent2_index], self.ratings[agent1_index]) = self._elo.rate_1vs1(self.ratings[agent2_index], self.ratings[agent1_index])

    def do_tournament(self, n_games: int):
        self.print_status()
        for i in range(n_games):
            print("Game {}/{}".format(i+1, n_games))

            n_agents = len(self.agents)
            agent1_index = random.randint(0, n_agents - 1)
            agent2_index = random.choice([i for i in range(n_agents) if i != agent1_index])
            self._play_game(agent1_index, agent2_index)
            if i % 50 == 0:
                self.print_status
        self.print_status()
    
    def print_status(self):
        for (i, agent) in enumerate(self.agents):
            rating = self.ratings[i]
            n_games_played = self.n_games_played[i]
            print("{} - {} - {} games played".format(agent, int(rating), n_games_played))

class Evaluator: 
    def __init__(self, states: State, values: float):
        self.state_values = values
        self.states = states

    def evaluate(self, agent: Agent, i: int, j: int):
        state = copy.copy(self.states[j])
        agent_value = agent.get_state_value(state)
        return -abs(self.state_values[j] - agent_value)

    def evaluate_agents(self, agents: list):
        scores = [0 for _ in agents]
        for (i, agent) in enumerate(agents):
            for (j, _) in enumerate(self.states):
                scores[i] += self.evaluate(agent, i, j)
            scores[i] /= len(self.states)

        indices = sorted(list(range(len(scores))), key=lambda x: scores[x], reverse=True)
        agents = [agents[i] for i in indices]
        scores = [scores[i] for i in indices]
        for (i, agent) in enumerate(agents):
            print("{} {:.4f}".format(agent, scores[i]))
            
random.seed(1)
states = [State()] + [get_random_non_starting_state() for _ in range(10)]
e = Evaluator(states, 
              [0.5] + [get_mcts_move(states[i], 200000, return_value=True, max_rollouts=50000, verbose=True)[0] for i in range(1, len(states))])
agents = []
for c in np.linspace(0.0, 3.5, 10, endpoint=True):
    for depth in np.arange(0, 80, 10):
        agents.append(MCTSLinearApproximationAgent("Linear MCTS {:.4f}-{}".format(c, depth), c, 0.1, depth))
agents.append(MCTSAgent("MCTS", 1.00, 0.1))
e.evaluate_agents(agents)