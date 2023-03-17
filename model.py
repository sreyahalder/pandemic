import numpy as np
from enum import Enum
import random
import networkx as nx
import world
import math
import copy

ACTIONS = ["TREAT", "CURE"]

def return_action(action_idx, actions, move, fly):
    if action_idx < 2:
        return -1, actions[action_idx]
    elif action_idx < len(move) + 2:
        return actions[action_idx], "MOVE"
    else:
        return actions[action_idx], "FLY"

class PandemicMDP:
    def __init__(self):
        self.n = 48
        self.k = 9
        self.map = nx.read_graphml('world_simple.graphml')
        # self.actions = ["TREAT", "CURE"]
        self.disease_counts = np.zeros((self.n), dtype=int)
        # TODO: if we want to play with limited disease cubes & colors, would need this:
        # self.disease_spread = np.array([24, 24, 24, 24])
        self.color_map = world.color_map
        self.current_city = world.City.ATLANTA.value
        self.cure_status = np.zeros((4), dtype=bool)
        self.draw_pile = [i for i in range(self.n)] + [-1]*4 # -1 is the placeholder for EPIDEMIC cards
        self.infect_pile = [i for i in range(self.n)]
        self.infect_discarded = []
        self.player_cards = []
        self.outbreak_count = 0
        self.game_over = False
        self.m = 200
        self.d = 4 # depth of rollouts
        self.c = 100 # xploration param
        self.discount = 0.9

        # START OF GAME
        random.shuffle(self.draw_pile)
        random.shuffle(self.infect_pile)
        for _ in range(4):
            card = self.draw_pile.pop()
            if card != -1:
                self.player_cards.append(card)
            else:
                self.draw_pile.append(-1)
                random.shuffle(self.draw_pile)
        for _ in range(self.k): self._infect(1)
    
    def get_actions(self):
        move = self._get_neighbors(self.current_city)
        fly = self.player_cards
        return move, fly
    
    
    def _get_neighbors(self, city):
        return [world.City[n].value for n in self.map.neighbors(world.City(city).name)]

    def _infect(self, count):
        card = self.infect_pile.pop()
        self.infect_discarded.append(card)
        self.disease_counts[card] += count
        if self.disease_counts[card] > 3:
            self._outbreak(card)
    
    def _epidemic(self):
        random.shuffle(self.infect_discarded)
        self.infect_pile = self.infect_pile + self.infect_discarded
        self.infect_discarded = []
        self._infect(3)

    def _outbreak(self, city):
        # handle outbreaks in the given city
        outbreak_cities = [city] # cities that need to be infected
        already_outbreak = [] # cities that already experienced an outbreak

        def add_neighbors(c):
            self.outbreak_count += 1
            if self.outbreak_count == 10:
                # print('Too many outbreaks, you lost.')
                self.game_over = True
                return True
            for n in self._get_neighbors(c):
                if n not in already_outbreak:
                    outbreak_cities.append(n)
            return False
        
        for c in outbreak_cities:
            if self.disease_counts[c] >= 3:
                self.disease_counts[c] = 3
                if add_neighbors(c): return
                already_outbreak.append(c)
            else:
                self.disease_counts[c] += 1
    
    def move(self, new_city):
        self.current_city = new_city
        return self.disease_counts[new_city] * 10
    
    def fly(self, new_city):
        self.player_cards.remove(new_city)
        self.current_city = new_city
        return self.disease_counts[new_city] * 7
    
    def treat(self):
        color = self.color_map[self.current_city]
        if self.disease_counts[self.current_city] > 0:
            if self.cure_status[color] == True:
                self.disease_counts[self.current_city] = 0 
                return 50
            else:
                self.disease_counts[self.current_city] -= 1
                return 300
        else:
            return -100
    
    def cure(self):
        color = self.color_map[self.current_city]
        if self.cure_status[color] == False:
            card_indices = [i for i in range(len(self.player_cards)) if self.color_map[self.player_cards[i]] == color]
            if len(card_indices) >= 2:
                for i in sorted(card_indices, reverse=True)[:2]:
                    del self.player_cards[i]
                self.cure_status[color] = True
                if all(self.cure_status):
                    print('Congrats, you cured all the diseases!')
                    self.game_over = True
                    return 1000 # game ends when all cured
                else:
                    return 100
            else:
                return -50
        else:
            return -200

    def step(self, city, action):
        reward = 0

        if action == "MOVE":
            reward += self.move(city)
        elif action == "FLY":
            reward += self.fly(city)
        elif action == "TREAT":
            reward += self.treat()
        elif action == "CURE":
            reward += self.cure()
            if self.game_over: return reward
        else:
            raise ValueError("Invalid action")
        return reward
    
    def end_turn(self):
        for _ in range(1):
            if len(self.infect_pile) <= 0:
                # print('Ran out of infect cards, you lost.')
                self.game_over = True
                return
            self._infect(1)
            if self.game_over:
                return

        # Draw two cards from DRAW_PILE
        for _ in range(1):
            if len(self.draw_pile) <= 0:
                # print('Ran out of draw cards, you lost.')
                self.game_over = True
                return
            card = self.draw_pile.pop()
            # Check for epidemic
            if card == -1:
                self._epidemic()
                continue
            if len(self.player_cards) < 7:
                self.player_cards.append(card)
            else:
                # Player must discard cards if they have too many
                discard_indices = np.random.choice(7, 2, replace=False)
                for index in sorted(discard_indices, reverse=True):
                    del self.player_cards[index]

    def bonus(self, n_sum, n):
        return np.inf if n == 0 else math.sqrt(math.log(n_sum)/n)

    def explore(self, s, N, Q):
        move, fly = self.get_actions()
        actions = ACTIONS + move + fly
        n_values = [N.get((s, a), 0) for a in actions]
        n_sum = sum(n_values)
        ucb = np.array([Q.get((s, a),0) + self.c * self.bonus(n_sum, N.get((s, a),0)) for a in actions])
        action_idx = np.argmax(ucb)
        return return_action(action_idx, actions, move, fly)
            
    def simulate(self, s, d, N, Q):
        original_state = s
        if d <= 0:
            return 0
        if self.game_over:
            return 0
        rollout = copy.deepcopy(self)
        city, a = rollout.explore(s, N, Q)
        r = rollout.step(city, a)
        rollout.end_turn()
        q = r + self.discount * rollout.simulate(tuple(rollout.disease_counts), d-1, N, Q)
        if (original_state, a) not in N.keys():
            N[(original_state, a)] = 0
        if (original_state, a) not in Q.keys():
            Q[(original_state, a)] = 0
        N[(original_state, a)] += 1
        Q[(original_state, a)] += (q - Q[(original_state, a)]) / N[(original_state, a)]
        return q

def main():
    pandemic = PandemicMDP()

    N = {}
    Q = {}
    score = 0
    while not pandemic.game_over:
        original_pandemic = copy.deepcopy(pandemic)

        for i in range(pandemic.m):
            pandemic.simulate(tuple(pandemic.disease_counts), pandemic.d, N, Q)
        
        original_state = tuple(original_pandemic.disease_counts)
        move, fly = pandemic.get_actions()
        actions = ACTIONS + move + fly
        action_idx = np.argmax(np.array([Q.get((original_state, a),0) for a in actions]))
        city, action = return_action(action_idx, actions, move, fly)
        print(f'Currently in {original_pandemic.current_city}. Taking action {action}.')
        
        original_pandemic.step(city, action)
        original_pandemic.end_turn()
        score = -np.sum(original_pandemic.disease_counts) * original_pandemic.outbreak_count + \
            100 * np.sum(original_pandemic.cure_status)
        pandemic = copy.deepcopy(original_pandemic)
    print('Final score:', score)

    
if __name__ == "__main__":
    main()
    

#play_game()