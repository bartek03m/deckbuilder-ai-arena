"""Common interface for all automatons.

An automaton gets an Observation (only what its side can see) and the list
of legal actions, and returns one action. Nothing here imports gRPC code.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Union

from salon.cards import Color, Tab


@dataclass(frozen=True)
class CardView:
    """Fully visible card (own hand, row, opponent's deck list)."""
    uid: int
    def_id: str
    name: str
    colors: tuple[Color, ...]
    cost: int
    damage: int
    shield: int
    draw: int
    tabs: tuple[Tab, ...]


@dataclass(frozen=True)
class SideView:
    hp: int
    max_hp: int
    shield: int
    energy: int
    deck_count: int
    discard_count: int


@dataclass(frozen=True)
class Observation:
    me: SideView
    opponent: SideView
    hand: tuple[CardView, ...]                     # own hand
    row: tuple[CardView, ...]                      # own row this turn
    opponent_hand: tuple[tuple[Color, ...], ...]   # opponent card backs: colors only
    opponent_deck_list: tuple[CardView, ...]       # public opponent deck list
    round: int


@dataclass(frozen=True)
class PlayCard:
    card_uid: int
    connect: bool = True             # False = start a new chain, do not connect
    tab_color: Color | None = None   # when the card matches two tabs


@dataclass(frozen=True)
class EndTurn:
    """The "Attack!" button: resolve the row and end the turn."""


Action = Union[PlayCard, EndTurn]


class Automaton(Protocol):
    name: str

    def choose_action(self, obs: Observation, legal: list[Action]) -> Action:
        """Return one action from `legal`."""
        ...