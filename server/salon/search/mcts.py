"""Monte Carlo Tree Search (UCT) prototype.

Works with any perfect-information game state that provides `legal_moves()`,
`play(move)`, `is_terminal()`, `player_to_move` and `reward(player)`.
"""
from __future__ import annotations

import math
import random
from collections.abc import Sequence
from typing import Any, Protocol

DEFAULT_C = 1.41

# A move is whatever the game uses (an int cell index in tic-tac-toe).
Move = Any


class GameState(Protocol):
    """What MCTS needs from a game state."""

    @property
    def player_to_move(self) -> int: ...

    def legal_moves(self) -> Sequence[Move]: ...

    def play(self, move: Move) -> GameState: ...

    def is_terminal(self) -> bool: ...

    def reward(self, player: int) -> float: ...


class Node:
    """Search tree node: a game state plus visit statistics.

    `value` is the sum of results from the perspective of `player_just_moved`,
    the player whose move led to this node (None for the root).
    """

    def __init__(self, state: GameState, parent: Node | None = None, move: Move = None):
        self.state = state
        self.parent = parent
        self.move = move
        self.children: list[Node] = []
        self.untried_moves: list[Move] = list(self.state.legal_moves())
        self.visits = 0
        self.value = 0.0
        self.player_just_moved: int | None = parent.state.player_to_move if parent is not None else None

    def is_fully_expanded(self) -> bool:
        """Return True when every legal move already has a child."""
        return len(self.untried_moves) == 0

    def expand(self, rng: random.Random) -> Node:
        """Remove one random untried move, add its child and return it."""
        idx = rng.randint(0, len(self.untried_moves) - 1)
        move = self.untried_moves.pop(idx)
        child = Node(self.state.play(move), parent=self, move=move)
        self.children.append(child)
        return child

    def update(self, result: float) -> None:
        """Record one visit with the given result."""
        self.visits += 1
        self.value += result

    def ucb1(self, c: float) -> float:
        """Return average result plus exploration bonus. Requires visits > 0."""
        average = self.value / self.visits
        uncertainty = math.sqrt(math.log(self.parent.visits) / self.visits)
        return average + c * uncertainty

    def best_child(self, c: float) -> Node:
        """Return the child with the highest UCB1 (first one on a tie)."""
        return max(self.children, key=lambda ch: ch.ucb1(c))


def select(node: Node, c: float) -> Node:
    """Descend by UCB1 until a node with untried moves or a terminal state."""
    while not node.state.is_terminal() and node.is_fully_expanded():
        node = node.best_child(c)
    return node


def rollout(state: GameState, rng: random.Random) -> GameState:
    """Play random moves until the game ends and return the final state."""
    while not state.is_terminal():
        state = state.play(rng.choice(state.legal_moves()))
    return state


def backpropagate(node: Node, final_state: GameState) -> None:
    """Update `node` and all its ancestors with the result of `final_state`.

    Each node gets the reward of its own `player_just_moved`; the root only
    gets a visit.
    """
    current: Node | None = node
    while current is not None:
        if current.player_just_moved is not None:
            current.update(final_state.reward(current.player_just_moved))
        else:
            current.visits += 1
        current = current.parent


def build_tree(state: GameState, iterations: int, rng: random.Random, c: float = DEFAULT_C) -> Node:
    """Run `iterations` MCTS iterations from `state` and return the root."""
    root = Node(state)
    for _ in range(iterations):
        node = select(root, c)
        if not node.state.is_terminal():
            node = node.expand(rng)
        final = rollout(node.state, rng)
        backpropagate(node, final)
    return root


def best_move(root: Node) -> Move:
    """Return the move of the most visited root child."""
    return max(root.children, key=lambda ch: ch.visits).move


def search(state: GameState, iterations: int, rng: random.Random, c: float = DEFAULT_C) -> Move:
    """Return the best move found by MCTS. Raises ValueError on a terminal state."""
    if state.is_terminal():
        raise ValueError("cannot search from a terminal state")
    return best_move(build_tree(state, iterations, rng, c))
