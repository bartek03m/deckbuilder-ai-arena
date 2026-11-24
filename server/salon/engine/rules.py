from salon.automata.interface import Action, EndTurn, PlayCard
from salon.engine.state import BattleResult, BattleState, RowCard, GameCard
from salon.cards import Tab

def matching_tabs(previous: RowCard, card: GameCard) -> list[Tab]:
    colors = card.instance.card.colors                          # card can have multiple colors
    return [tab for tab in previous.card.instance.tabs if tab.color in colors]

def legal_actions(state: BattleState) ->list[Action]:
    if state.result != BattleResult.ONGOING:
        return []
    side = state.active_side
    actions = [] # type -> list[Action]
    previous = state.row[-1] if state.row else None
    for card in side.hand:
        cost = card.instance.card.cost
        if side.energy >= cost:
            actions.append(PlayCard(card_uid=card.uid, connect = False)) 
        
        # those two if make sense together because even if a tab and card match player always can start new combination for card's full price

        if previous is not None and max(0, cost-1) <= side.energy:
            tabs = matching_tabs(previous=previous, card=card)
            if len(tabs) == 1:
                actions.append(PlayCard(card_uid=card.uid, connect = True))
            else:
                for tab in tabs:
                    actions.append(PlayCard(card_uid=card.uid, connect = True, tab_color=tab.color))
    actions.append(EndTurn())
    return actions