from salon.automata.interface import Action, PlayCard
from salon.engine.events import CardPlayed, CardsDiscarded, EnergyChanged, Event, TabActivated
from salon.engine.rules import legal_actions, matching_tabs
from salon.engine.state import BattleState, RowCard


def apply(state: BattleState, action: Action) -> tuple[BattleState, list[Event]]:
    
    if action not in legal_actions(state):
        raise ValueError(f"illegal action: {action}")
    
    clone_state = state.clone_state() # we work on a copy, so `state` stays untouched
    events = [] #type list[Action]

    if isinstance(action, PlayCard):
        _play_card(clone_state, action, events)
    else:
        _end_turn(clone_state, events)
    return clone_state, events

def _play_card(state: BattleState, action: PlayCard, events: list[Event]) -> None:
    player = state.player_turn
    side = state.active_side
    card = next(c for c in side.hand if c.uid == action.card_uid) # next stops at the first fitting element
    previous = state.row[-1] if state.row else None
    cost = card.instance.card.cost
    tab = None

    if action.connect:
        tabs = matching_tabs(previous=previous, card=card)
        if action.tab_color is None:
            tab = tabs[0]
        else:
            tab = next(t for t in tabs if t.color == action.tab_color)
        cost = max(0, cost-1)

    side.hand.remove(card)
    side.energy -= cost
    state.row.append(RowCard(card, connected=action.connect, tab=tab))

    events.append(CardPlayed(by_player=player, card=card))
    if tab is not None:
        events.append(TabActivated(card_uid=previous.card.uid, tab=tab))
    events.append(EnergyChanged(player=player, value=side.energy))

def _end_turn(state: BattleState, events: list[Event]) -> None:
    player = state.player_turn
    side = state.active_side

    # TODO attack (damage, shield, drawing), end of battle, shield disappearing and energy reset for the new turn
    discarded = tuple(entry.card.uid for entry in state.row)
    side.discard.extend(entry.card for entry in state.row)
    state.row = []
    if discarded:
        events.append(CardsDiscarded(player=player, card_uids=discarded))

    state.player_turn = not player  # side switch
    if state.player_turn:
        state.round += 1