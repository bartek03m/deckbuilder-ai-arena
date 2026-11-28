"""Translate engine objects into gRPC messages (and colors back). No game rules here."""

from __future__ import annotations

from salon_proto import game_pb2 as pb

from salon.cards import Color, Tab
from salon.engine import events as ev
from salon.engine.state import BattleResult, BattleState, GameCard, SideState

_COLOR_TO_PB = {
    Color.RED: pb.COLOR_RED,
    Color.GREEN: pb.COLOR_GREEN,
    Color.BLUE: pb.COLOR_BLUE,
    Color.PURPLE: pb.COLOR_PURPLE,
    Color.RAINBOW: pb.COLOR_RAINBOW,
}
_COLOR_FROM_PB = {value: color for color, value in _COLOR_TO_PB.items()}

_RESULT_TO_PB = {
    BattleResult.ONGOING: pb.BATTLE_RESULT_ONGOING,
    BattleResult.WON: pb.BATTLE_RESULT_WON,
    BattleResult.LOST: pb.BATTLE_RESULT_LOST,
}


def color_to_proto(color: Color) -> int:
    return _COLOR_TO_PB[color]


def color_from_proto(value: int) -> Color | None:
    """COLOR_UNSPECIFIED means no color was chosen - None."""
    if value == pb.COLOR_UNSPECIFIED:
        return None
    try:
        return _COLOR_FROM_PB[value]
    except KeyError:
        raise ValueError(f"unknown color: {value}") from None


def tab_to_proto(tab: Tab) -> pb.Tab:
    return pb.Tab(color=color_to_proto(tab.color), value=tab.value)


def card_to_proto(card: GameCard) -> pb.Card:
    d = card.instance.card
    return pb.Card(
        uid=card.uid,
        def_id=d.id,
        name=d.name,
        colors=[color_to_proto(c) for c in d.colors],
        cost=d.cost,
        damage=d.damage,
        shield=d.shield,
        draw=d.draw,
        tabs=[tab_to_proto(t) for t in card.instance.tabs],
    )


def card_back_to_proto(card: GameCard) -> pb.CardBack:
    """A hidden card - only its colors are visible."""
    return pb.CardBack(colors=[color_to_proto(c) for c in card.instance.card.colors])


def side_to_proto(side: SideState) -> pb.Side:
    return pb.Side(
        hp=side.hp,
        max_hp=side.max_hp,
        shield=side.shield,
        energy=side.energy,
        deck_count=side.deck_count,
        discard_count=side.discard_count,
    )


def state_to_proto(state: BattleState) -> pb.BattleState:
    """The client's view: own hand in full, the automaton's hand as card backs."""
    return pb.BattleState(
        player=side_to_proto(state.player),
        enemy=side_to_proto(state.enemy),
        hand=[card_to_proto(c) for c in state.player.hand],
        row=[card_to_proto(rc.card) for rc in state.row],
        enemy_hand=[card_back_to_proto(c) for c in state.enemy.hand],
        round=state.round,
        result=_RESULT_TO_PB[state.result],
    )


def event_to_proto(event: ev.Event) -> pb.Event:
    if isinstance(event, ev.CardPlayed):
        return pb.Event(card_played=pb.CardPlayed(
            by_player=event.by_player, card=card_to_proto(event.card)))
    if isinstance(event, ev.TabActivated):
        return pb.Event(tab_activated=pb.TabActivated(
            card_uid=event.card_uid, tab=tab_to_proto(event.tab)))
    if isinstance(event, ev.Damage):
        return pb.Event(damage=pb.Damage(
            to_player=event.to_player, amount=event.amount, absorbed=event.absorbed))
    if isinstance(event, ev.ShieldChanged):
        return pb.Event(shield_changed=pb.ShieldChanged(player=event.player, value=event.value))
    if isinstance(event, ev.CardsDrawn):
        return pb.Event(cards_drawn=pb.CardsDrawn(player=event.player, count=event.count))
    if isinstance(event, ev.EnergyChanged):
        return pb.Event(energy_changed=pb.EnergyChanged(player=event.player, value=event.value))
    if isinstance(event, ev.CardsDiscarded):
        return pb.Event(cards_discarded=pb.CardsDiscarded(
            player=event.player, card_uids=list(event.card_uids)))
    if isinstance(event, ev.BattleEnded):
        return pb.Event(battle_ended=pb.BattleEnded(result=_RESULT_TO_PB[event.result]))
    raise TypeError(f"unknown event: {event!r}")


def events_to_proto(events: list[ev.Event]) -> list[pb.Event]:
    return [event_to_proto(e) for e in events]