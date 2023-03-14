import numpy as np
from enum import Enum
import random
import networkx as nx
import world
import math
import copy
    
class PandemicMDP:
    def __init__(self):
        self.n = 48
        self.k = 9
        self.map = nx.read_graphml('world_simple.graphml')
        self.actions = ["MOVE", "FLY", "TREAT", "BUILD", "CURE"]
        self.disease_counts = np.zeros((self.n), dtype=int)
        # TODO: if we want to play with limited disease cubes & colors, would need this:
        # self.disease_spread = np.array([24, 24, 24, 24])
        self.color_map = world.color_map
        self.research_stations = np.zeros((self.n), dtype=bool)
        self.research_stations[world.City.ATLANTA.value] = True
        self.current_city = world.City.ATLANTA.value
        self.cure_status = np.zeros((4), dtype=bool)
        self.draw_pile = [i for i in range(self.n)] + [-1]*4 # -1 is the placeholder for EPIDEMIC cards
        self.infect_pile = [i for i in range(self.n)]
        self.infect_discarded = []
        self.player_cards = []
        self.outbreak_count = 0
        self.game_over = False
        self.m = 20
        self.d = 2 #depth of rollouts
        self.c = 100 #exploration param
        self.discount = 0.9

        # START OF GAME
        random.shuffle(self.draw_pile)
        random.shuffle(self.infect_pile)
        for _ in range(4): self.player_cards.append(self.draw_pile.pop())
        for _ in range(self.k): self._infect(1)
    
    def _get_neighbors(self, city):
        return [n for n in self.map.neighbors(world.City(city).name)]

    def _infect(self, count):
        card = self.infect_pile.pop()
        self.infect_discarded.append(card)
        self.disease_counts[card] += count
        print("Now infecting: ", world.City(card).name)
        if self.disease_counts[card] > 3:
            self._outbreak(card)
    
    def _epidemic(self):
        print('You drew an EPIDEMIC card!! >:)')
        random.shuffle(self.infect_discarded)
        self.infect_pile = self.infect_pile + self.infect_discarded
        self.infect_discarded = []
        self._infect(3)

    def _outbreak(self, city):
        # handle outbreaks in the given city
        outbreak_cities = []
        already_outbreak = []

        def add_neighbors(c):
            self.outbreak_count += 1
            if self.outbreak_count == 10:
                print('Too many outbreaks, you lost.')
                self.game_over = True
                return True
            neighbors = self._get_neighbors(c)
            for neighbor in neighbors:
                n = world.City[neighbor].value
                if n not in already_outbreak:
                    outbreak_cities.append(n)
            return False
        
        add_neighbors(city)
        for c in outbreak_cities:
            if self.disease_counts[c] >= 3:
                self.disease_counts[c] = 3
                if add_neighbors(c): return
                already_outbreak.append(c)
            else:
                self.disease_counts[c] += 1
    
    def move(self, new_city):
        self.current_city = new_city
    
    def fly(self, new_city):
        self.player_cards.remove(new_city)
        self.current_city = new_city
    
    def treat(self, reward):
        color = self.color_map[self.current_city]
        if self.disease_counts[self.current_city] > 0:
            if self.cure_status[color] == True:
                self.disease_counts[self.current_city] = 0 
                reward += 30
            else:
                self.disease_counts[self.current_city] -= 1
                reward += 5
        else:
            reward -= 30
    
    def build(self):
        if self.research_stations[self.current_city] == False and self.player_cards.count(self.current_city) > 0: 
            self.player_cards.remove(self.current_city)
            self.research_stations[self.current_city] = True
    
    def cure(self, reward):
        color = self.color_map[self.current_city]
        if self.cure_status[color] == False and self.research_stations[self.current_city] == True:
            card_indices = [i for i in range(len(self.player_cards)) if self.color_map[self.player_cards[i]] == color]
            if len(card_indices) >= 4:
                for i in sorted(card_indices, reverse=True)[:4]:
                    del self.player_cards[i]
                self.cure_status[color] = True
                if all(self.cure_status):
                    reward += 100 # game ends when all cured
                    print('Congrats, you cured all the diseases!')
                    self.game_over = True
                else:
                    reward += 10


    def step(self, action):
        reward = 0

        if action == "MOVE":
            neighbors = self._get_neighbors(self.current_city)
            new_city = world.City[np.random.choice(neighbors)].value
            self.move(new_city)
        elif action == "FLY":
            new_city = self.player_cards[np.random.choice(len(self.player_cards))]
            self.fly(new_city)
        elif action == "TREAT":
            self.treat(reward)
        elif action == "BUILD":
            self.build()
        elif action == "CURE":
            self.cure(reward)
            if self.game_over: return reward
        else:
            raise ValueError("Invalid action")

        print('INFECTING TWO CITIES:')
        for _ in range(2):
            if len(self.infect_pile) <= 0:
                print('Ran out of infect cards, you lost.')
                self.game_over = True
                return reward
            self._infect(1)
            if self.game_over:
                return reward

        # Draw two cards from DRAW_PILE
        for _ in range(2):
            if len(self.draw_pile) <= 0:
                print('Ran out of draw cards, you lost.')
                self.game_over = True
                return reward
            card = self.draw_pile.pop()
            # Check for epidemic
            if card == -1:
                self._epidemic()
                reward -= 50
                continue
            if len(self.player_cards) < 7:
                self.player_cards.append(card)
            else:
                # Player must discard cards if they have too many
                discard_indices = np.random.choice(7, 2, replace=False)
                for index in sorted(discard_indices, reverse=True):
                    del self.player_cards[index]
        return reward


    def bonus(self, n_sum, n):
        return np.inf if n == 0 else math.sqrt(math.log(n_sum)/n)

    def explore(self, s, N, Q):
        n_values = [N[(s, a)] for a in self.actions]
        print(s, n_values)
        n_sum = sum(n_values)
        ucb = np.array([Q[(s, a)] + self.c * self.bonus(n_sum, N[(s, a)]) for a in self.actions])
        print(ucb)
        action_idx = np.argmax(ucb)
        return self.actions[action_idx]
            
    def simulate(self, s, d, N, Q):
        print('Depth:', d)
        original_state = s
        if d <= 0:
            print('1')
            return 0
        if not (s, self.actions[0]) in N.keys():
            for a in self.actions:
                Q[(s, a)] = 0.0
                N[(s, a)] = 0
            print('2')
            # return 0
        if self.game_over:
            print('GAME OVER')
            return 0
        rollout = copy.deepcopy(self)
        a = rollout.explore(s, N, Q)
        print('Take sim action:', a)
        r = rollout.step(a)
        q = r + self.discount * rollout.simulate(tuple(rollout.disease_counts), d-1, N, Q)
        N[(original_state, a)] += 1
        Q[(original_state, a)] += (q - Q[(original_state, a)]) / N[(original_state, a)]
        return q

def main():
    pandemic = PandemicMDP()

    N = {}
    Q = {}
    while not pandemic.game_over:
        original_pandemic = copy.deepcopy(pandemic)

        print('------------------Simulate')
        for i in range(pandemic.m):
            pandemic.simulate(tuple(pandemic.disease_counts), pandemic.d, N, Q)
        
        original_state = tuple(original_pandemic.disease_counts)
        a = np.argmax(np.array([Q[(original_state, a)] for a in pandemic.actions]))
        action = pandemic.actions[a]
        print(f'----------------Take action {action}.')

        pandemic = original_pandemic
        print(pandemic.step(action))

    
if __name__ == "__main__":
    main()
    

#play_game()