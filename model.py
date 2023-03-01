import numpy as np
from enum import Enum
import random

class City(Enum):
    ATLANTA = 0
    # TODO: Add more cities here & build NetworkX graph
    
class Disease(Enum):
    BLACK = 0
    BLUE = 1
    RED = 2
    YELLOW = 3
    
class PandemicMDP:
    def __init__(self, n, k):
        self.n = n
        self.k = k
        self.map = np.zeros((n, n))
        self.disease_counts = np.zeros((n), dtype=int)
        # TODO: add array for city colors
        self.research_stations = np.zeros((n), dtype=bool)
        self.current_city = City.ATLANTA.value
        self.cure_status = np.zeros((4), dtype=bool)
        self.draw_pile = np.array([i for i in range(n)] + [-1]*4) # -1 is the placeholder for EPIDEMIC cards
        self.infect_pile = np.array([i for i in range(n)])
        self.player_cards = []
        np.random.shuffle(self.draw_pile)
        np.random.shuffle(self.infect_pile)
        self.deck_pos = 0
        self.outbreak_count = 0
    
    def _draw_card(self, deck):
        if self.deck_pos == len(deck):
            self.deck_pos = 0
        card = deck[self.deck_pos]
        self.deck_pos += 1
        return card
    
    def _draw_cards(self, deck, num_cards):
        return [self._draw_card(deck) for _ in range(num_cards)]
    
    def _epidemic(self):
        bottom_card = self.infect_pile[0]
        self.infect_pile = np.delete(self.infect_pile, 0)
        self.infect_pile = np.concatenate((self.infect_pile, [bottom_card]))
        np.random.shuffle(self.infect_pile)
        card = self._draw_card(self.infect_pile)
        self.disease_counts[card][random.randint(0, 3)] += 3
        self._outbreak(card)
    
    def _outbreak(self, city):
        # handle outbreaks in the given city
        neighbors = self.map[city]
        for neighbor in neighbors:
            if self.disease_counts[neighbor] < 3:
                self.disease_counts[neighbor] += 1
            elif self.disease_counts[neighbor] == 3:
                self.disease_counts[neighbor] = 0
                self._outbreak(neighbor)
        self.disease_counts[city] = 3
        self.outbreak_count += 1

    def step(self, action):
        if action == "MOVE":
            neighbors = self.map[self.current_location]
            self.current_location = np.random.choice(neighbors)
            # TODO: change to select random neighbor from NetworkX graph
        elif action == "FLY":
            if self.current_location in self.player_cards:
                self.player_cards.remove(self.current_location)
                self.current_location = self.player_cards[np.random.choice(len(self.player_cards))]
        elif action == "TREAT":
            if self.disease_counts[self.current_location] > 0:
                self.disease_counts[self.current_location] -= 1
        elif action == "BUILD":
            if self.research_stations[self.current_location] == False and self.player_cards.count(self.current_location) > 0:
                self.player_cards.remove(self.current_location)
                self.research_stations[self.current_location] = True
        elif action == "CURE":
            color = self.color_map[self.current_location]
            if self.cure_status[color] == False and self.research_stations[self.current_location] == True:
                card_indices = [i for i in range(len(self.player_cards)) if self.color_map[self.player_cards[i]] == color]
                if len(card_indices) >= 4:
                    for i in sorted(card_indices, reverse=True)[:4]:
                        del self.player_cards[i]
                    self.cure_status[color] = True
                    if all(self.cure_status.values()):
                        return self.disease_counts, self.research_stations, self.current_location, self.cure_status, self.draw_pile, self.infect_pile, 10, True
                    else:
                        return self.disease_counts, self.research_stations, self.current_location, self.cure_status, self.draw_pile, self.infect_pile, 0, False
        else:
            raise ValueError("Invalid action")

        # Draw two cards from INFECT_PILE
        for i in range(2):
            card = self.infect_pile.pop()
            self.disease_counts[card] += 1
            if self.disease_counts[card] > 3:
                self._outbreak(card)
                return self.disease_counts, self.research_stations, self.current_location, self.cure_status, self.draw_pile, self.infect_pile, -50, True

        # Draw two cards from DRAW_PILE
        for i in range(2):
            card = self.draw_pile.pop()
            # Check for epidemic
            if card == "EPIDEMIC":
                self._epidemic()
                continue
            if len(self.player_cards) < 7:
                self.player_cards.append(card)
            else:
                # Player must discard cards if they have too many
                discard_indices = np.random.choice(7, 2, replace=False)
                for index in sorted(discard_indices, reverse=True):
                    del self.player_cards[index]

        return self.disease_counts, self.research_stations, self.current_location, self.cure_status, self.draw_pile, self.infect_pile

