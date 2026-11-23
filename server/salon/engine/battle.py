"""creating a battle and drawing cards | randomness goes through state.rng"""

from __future__ import annotations
import itertools
import random
from salon.cards import CardInstance
from .state import BattleState, GameCard, SideState

START_HAND = 5
MAX_HAND = 7
FIRST_TURN_ENERGY = 2

def create_battle(
    seed: int,
    player_deck: list[CardInstance],
    enemy_deck: list[CardInstance],
    player_hp: int = 50,
    enemy_hp: int = 30,    
) -> BattleState:
    
    rng = random.Random(seed)
    next_uid = itertools.count()    # one counter will provide unique uids
    player = SideState(hp=player_hp, max_hp=player_hp)
    enemy = SideState(hp=enemy_hp, max_hp=enemy_hp)
    
    player.deck = [GameCard(next(next_uid), c) for c in player_deck]
    enemy.deck = [GameCard(next(next_uid), c) for c in enemy_deck]
    rng.shuffle(player.deck)
    rng.shuffle(enemy.deck)

    state = BattleState(player=player, enemy=enemy, row=[], round=1, rng=rng)
    draw_cards(state, player, START_HAND)
    draw_cards(state, enemy, START_HAND)
    player.energy = FIRST_TURN_ENERGY
    return state


def draw_cards(state: BattleState, side: SideState, count: int) -> list[GameCard]:
    drawn = []
    for i in range(count):
        if len(side.hand) >= MAX_HAND:
            break
        if not side.deck:                   # if deck is empty
            if not side.discard:            
                break
            side.deck = side.discard        
            side.discard = []
            state.rng.shuffle(side.deck)    # shuffled with rng in our BattleState
        card = side.deck.pop()              # default pop arg is -1
        side.hand.append(card)
        drawn.append(card)
    return drawn