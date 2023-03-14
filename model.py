import numpy as np
from enum import Enum
import random
import networkx as nx
import world
    
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
        self.m = 10
        self.d = 10 #depth of rollouts
        self.c = 100 #exploration param
        self.Q = {}
        self.N = {}
        self.discount = 0.9

        random.shuffle(self.draw_pile)
        random.shuffle(self.infect_pile)
        # Player starts the game drawing 4 cards
        for _ in range(4): self.player_cards.append(self.draw_pile.pop())
        # Game starts with k cities infected
        for _ in range(self.k):
            self._infect(1) #did we change this to infect w one disease cube instead of 3 of 3, 3 of 2, 3 of 1?
    
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
        self.outbreak_count += 1
        if self.outbreak_count == 10:
            print('Too many outbreaks, you lost.')
            self.game_over = True
            return
        
        neighbors = self._get_neighbors(city)
        for neighbor in neighbors:
            n = world.City[neighbor].value
            if self.disease_counts[n] < 3:
                self.disease_counts[n] += 1
            elif self.disease_counts[n] == 3:
                self.disease_counts[n] = 0 #Why is disease counts 0 now after outbreak? doesnt it stay 3?
                self._outbreak(n)
        self.disease_counts[city] = 3
    
    def move(self, new_city):
        self.current_city = new_city
    
    def fly(self, new_city):
        self.player_cards.remove(new_city)
        self.current_city = new_city
    
    def treat(self, reward):
        if self.disease_counts[self.current_city] > 0:
            if self.cure_status[color] == True:
                self.disease_counts[self.current_city] = 0 
                reward += 5
            else:
                self.disease_counts[self.current_city] -= 1
                reward += 1
    
    def build():
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
                if all(self.cure_status.values()):
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
        else:
            raise ValueError("Invalid action")

        for i in range(2):
            self._infect(1)

        # Draw two cards from DRAW_PILE
        for i in range(2):
            card = self.draw_pile.pop()
            if len(self.draw_pile) <= 0:
                print('Ran out of draw cards, you lost.')
                self.game_over = True
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
        return np.inf if n == 0 else sqrt(log(n_sum)/n)

    def explore(self, s):
            n_values = [self.N[(s, a)] for a in self.actions]
            n_sum = sum(n_values)
            ucb = np.array([self.Q[(s, a)] + self.c * self.bonus(n_sum, self.N[(s, a)]) for a in self.actions])
            action_idx = np.argmax(ucb)
            return self.actions[action_idx]
            
    def simulate(self, s, d):
        original_state = s
        if self.d <= 0:
            return 0
        if not (s, self.actions[0]) in self.N.keys():
            for a in self.actions:
                self.Q[(s, a)] = 0.0
                self.N[(s, a)] = 0
            return 0
        a = self.explore(s)
        r = self.step(a)
        q = r + self.discount*self.simulate(tuple(self.disease_counts), d-1)
        self.N[(original_state, a)] += 1
        self.Q[(original_state, a)] += (q-self.Q[(original_state, a)]) / self.N[(original_state, a)]
        return q

        



    """
    def step(self, action):

        if action == "MOVE":
            neighbors = self._get_neighbors(self.current_city)
            self.current_city = world.City[np.random.choice(neighbors)].value
        elif action == "FLY":
            new_city = self.player_cards[np.random.choice(len(self.player_cards))]
            self.player_cards.remove(new_city)
            self.current_city = new_city
        #elif action == "CHARTER_FLIGHT":
        #    if self.current_city in self.player_cards:
        #        self.player_cards.remove(self.current_city)
        #        self.current_city = self.player_cards[np.random.choice(len(self.player_cards))]
        elif action == "TREAT":
            if self.disease_counts[self.current_city] > 0:
                if self.cure_status[color] == True:
                    self.disease_counts[self.current_city] = 0 
                    reward += 5
                else:
                    self.disease_counts[self.current_city] -= 1
                    reward += 1
        elif action == "BUILD":
            if self.research_stations[self.current_city] == False and self.player_cards.count(self.current_city) > 0: #why do we check if player_cards count > 0
                self.player_cards.remove(self.current_city)
                self.research_stations[self.current_city] = True
        elif action == "CURE":
            color = self.color_map[self.current_city]
            if self.cure_status[color] == False and self.research_stations[self.current_city] == True:
                card_indices = [i for i in range(len(self.player_cards)) if self.color_map[self.player_cards[i]] == color]
                if len(card_indices) >= 4:
                    for i in sorted(card_indices, reverse=True)[:4]:
                        del self.player_cards[i] #does this do in place deletion? change this to pop
                    self.cure_status[color] = True
                    if all(self.cure_status.values()):
                        reward += 100 # game ends when all cured
                        print('Congrats, you cured all the diseases!')
                        self.game_over = True
                    else:
                        reward += 10
            
        else:
            raise ValueError("Invalid action")

        # Draw two cards from INFECT_PILE
        for i in range(2):
            self._infect(1)

        # Draw two cards from DRAW_PILE
        for i in range(2):
            card = self.draw_pile.pop()
            if len(self.draw_pile) == 0:
                print('Ran out of draw cards, you lost.')
                self.game_over = True
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

        return self.current_city
        """



def play_game():
    pandemic = PandemicMDP()
    #actions = ["MOVE", "FLY", "TREAT", "BUILD", "CURE"]
    print(f'Start of game. Start in ATLANTA. Current cards: {[world.City(i).name for i in pandemic.player_cards if i >= 0]}. Cure status: {pandemic.cure_status}')
    while not pandemic.game_over:
        a = random.choice(self.actions)
        print(f'----------------\nTake action {a}.')
        print(f'Now in: {world.City(pandemic.step(a)).name}. Current cards: {[world.City(i).name for i in pandemic.player_cards if i >= 0]}')
        disease_dict = {}
        for i in range(len(pandemic.disease_counts)):
            disease_dict[world.City(i).name] = pandemic.disease_counts[i]
        print(f'Disease counts: {disease_dict}')
    
    print(f'GAME OVER. Cure status: {pandemic.cure_status}')

"""
def bonus(n_sum, n):
    return np.inf if n == 0 else sqrt(log(n_sum)/n)

def explore(s):
        n_values = [N[(s, a)] for a in actions]
        n_sum = sum(n_values)
        ucb = np.array([Q[(s, a)] + self.c*bonus(n_sum, N[(s, a)]) for a in actions])
        action_idx = np.argmax(ucb)
        return self.actions[action_idx]
        
def simulate(s, d=self.d):
    original_state = s
    if self.d <= 0:
        return 
    if not (s, actions[0]) in N.keys():
        for a in actions:
            Q[(s, a)] = 0.0
            N[(s, a)] = 0
        return
    a = explore(s)
    r = randstep()
    q = r + self.discount*simulate(self.disease_counts, d-1)
    N[(original_state, a)] += 1
    Q[(original_state, a)] += (q-Q[(original_state, a)]) / N[(original_state, a)]
    return q

def select_action():
    for i in range(mcts.m):
        simulate()
    idx = np.argmax([Q[(self.disease_counts, a)] for a in self.actions])
    return self.action[idx]
"""

def main():
    pandemic = PandemicMDP()
    
    while not pandemic.game_over:
        original_pandemic = pandemic

        for i in range(pandemic.m):
            pandemic.simulate(tuple(pandemic.disease_counts), pandemic.d)
        
        original_state = tuple(original_pandemic.disease_counts)
        a = np.argmax(np.array([pandemic.Q[(original_state, a)] for a in pandemic.actions]))
        action = pandemic.actions[a]

        pandemic = original_pandemic
        pandemic.step(action)

    
if __name__ == "__main__":
    main()
    

#play_game()