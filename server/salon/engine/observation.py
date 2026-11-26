"""Build what one side can see from the full battle state."""

from __future__ import annotations

from salon.automata.interface import CardView, Observation, SideView
from salon.engine.state import BattleState, GameCard, SideState


def _card_view(c: GameCard) -> CardView:
    d = c.instance.card  # CardDef: the card definition
    return CardView(
        uid=c.uid,
        def_id=d.id,
        name=d.name,
        colors=d.colors,
        cost=d.cost,
        damage=d.damage,
        shield=d.shield,
        draw=d.draw,
        tabs=c.instance.tabs,
    )


def _side_view(s: SideState) -> SideView:
    return SideView(
        hp=s.hp,
        max_hp=s.max_hp,
        shield=s.shield,
        energy=s.energy,
        deck_count=s.deck_count,
        discard_count=s.discard_count,
    )


def _sorted(cards: list[GameCard]) -> tuple[CardView, ...]:
    """Sort cards by uid so the order leaks no hidden info, then convert them."""
    by_uid = sorted(cards, key=lambda c: c.uid)
    return tuple(_card_view(c) for c in by_uid)


def observe(state: BattleState, for_player: bool) -> Observation:
    """What one side can see. for_player=True -> player, False -> automaton."""
    me = state.player if for_player else state.enemy
    opp = state.enemy if for_player else state.player
    my_turn = state.player_turn == for_player
    row_cards = [rc.card for rc in state.row]
    my_row = row_cards if my_turn else []
    opp_row = [] if my_turn else row_cards
    return Observation(
        me=_side_view(me),
        opponent=_side_view(opp),
        hand=tuple(_card_view(c) for c in me.hand),
        row=tuple(_card_view(c) for c in my_row),
        deck_list=_sorted(me.deck + me.hand + me.discard + my_row),
        discard=_sorted(me.discard),
        opponent_hand=tuple(c.instance.card.colors for c in opp.hand),
        opponent_deck_list=_sorted(opp.deck + opp.hand + opp.discard + opp_row),
        opponent_discard=_sorted(opp.discard),
        round=state.round,
    )
