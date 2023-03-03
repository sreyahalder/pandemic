import numpy as np
from enum import Enum
import random
import networkx as nx
import world
    
class PandemicMDP:
    def __init__(self):
        self.n = 48
        self.k = 10
        self.map = nx.read_graphml('world_simple.graphml')
        self.disease_counts = np.zeros((self.n), dtype=int)
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

        random.shuffle(self.draw_pile)
        random.shuffle(self.infect_pile)
        # Player starts the game drawing 2 cards
        self.player_cards.append(self.draw_pile.pop())
        self.player_cards.append(self.draw_pile.pop())
        # Game starts with k cities infected
        for _ in range(self.k):
            self._infect(1)
    
    def _get_neighbors(self, city):
        return [n for n in self.map.neighbors(world.City(city).name)]

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
                self.disease_counts[n] = 0
                self._outbreak(n)
        self.disease_counts[city] = 3

    def step(self, action):
        reward = 0
        if action == "MOVE":
            neighbors = self._get_neighbors(self.current_city)
            self.current_city = world.City[np.random.choice(neighbors)].value
        elif action == "FLY":
            if self.current_city in self.player_cards:
                self.player_cards.remove(self.current_city)
                self.current_city = self.player_cards[np.random.choice(len(self.player_cards))]
        elif action == "TREAT":
            if self.disease_counts[self.current_city] > 0:
                self.disease_counts[self.current_city] -= 1
                reward += 1
        elif action == "BUILD":
            if self.research_stations[self.current_city] == False and self.player_cards.count(self.current_city) > 0:
                self.player_cards.remove(self.current_city)
                self.research_stations[self.current_city] = True
        elif action == "CURE":
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
            elif self.cure_status[color] == True:
                self.disease_counts[self.current_city] = 0
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

def play_game():
    pandemic = PandemicMDP()
    actions = ["MOVE", "FLY", "BUILD", "CURE"]
    print(f'Start of game. Start in ATLANTA. Current cards: {pandemic.player_cards}. Cure status: {pandemic.cure_status}')
    while not pandemic.game_over:
        a = random.choice(actions)
        print(f'----------------\nTake action {a}.')
        print(f'Now in: {world.City(pandemic.step(a)).name}. Current cards: {pandemic.player_cards}')
    
    print(f'GAME OVER. Cure status: {pandemic.cure_status}')

play_game()