from salon.automata.interface import Action, PlayCard
from salon.engine.events import CardPlayed, CardsDiscarded, EnergyChanged, Event, TabActivated, Damage, BattleEnded , ShieldChanged, CardsDrawn
from salon.engine.rules import legal_actions, matching_tabs
from salon.engine.state import BattleState, RowCard, BattleResult
from salon.cards import Color
from salon.engine.battle import TURN_DRAW, TURN_ENERGY, draw_cards


def apply(state: BattleState, action: Action) -> tuple[BattleState, list[Event]]:
    
    if action not in legal_actions(state):
        raise ValueError(f"illegal action: {action}")
    
    clone_state = state.clone_state() # we work on a copy, so `state` stays untouched
    events = [] #type list[Event]

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
    enemy = state.inactive_side

    damage = shield = 0
    draw = TURN_DRAW

    for row_card in state.row:
        effects = row_card.card.instance.card
        shield += effects.shield
        damage += effects.damage
        draw += effects.draw

        tab = row_card.tab
        if tab is not None:
            if tab.color == Color.RED:
                damage += tab.value
            if tab.color == Color.GREEN:
                shield += tab.value
            if tab.color == Color.BLUE:
                draw += tab.value

    if damage > 0:
        absorbed = min(enemy.shield, damage)
        enemy.shield -= absorbed
        enemy.hp = max(0, enemy.hp - (damage - absorbed))
        events.append(Damage(to_player=not player, amount=damage, absorbed=absorbed))
        if enemy.hp == 0:
            state.result = BattleResult.WON if player else BattleResult.LOST
            events.append(BattleEnded(state.result))
            return

    if shield > 0:
        side.shield += shield
        events.append(ShieldChanged(player=player, value=side.shield))

    drawn = draw_cards(state, side, draw)
    if drawn:
        events.append(CardsDrawn(player=player, count=len(drawn)))

    discarded = tuple(entry.card.uid for entry in state.row)
    side.discard.extend(entry.card for entry in state.row)
    state.row = []
    if discarded:
        events.append(CardsDiscarded(player=player, card_uids=discarded))

    state.player_turn = not player  # side switch
    if state.player_turn:
        state.round += 1

    new_side = state.active_side
    if new_side.shield > 0:
        new_side.shield = 0
        events.append(ShieldChanged(player=state.player_turn, value=0))
    new_side.energy = TURN_ENERGY
    events.append(EnergyChanged(player=state.player_turn, value=TURN_ENERGY))