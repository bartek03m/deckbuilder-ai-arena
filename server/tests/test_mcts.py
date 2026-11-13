import math
import random

import pytest

from salon.search.mcts import (
    Node,
    backpropagate,
    best_move,
    build_tree,
    rollout,
    search,
    select,
)
from salon.search.tictactoe import TicTacToeState


SYMBOLS = {"X": 0, "O": 1, ".": None}


def make(cells: str, to_move: int) -> TicTacToeState:
    """'XX.OO....' -> state. X=0, O=1, '.'=empty."""
    return TicTacToeState(board=tuple(SYMBOLS[c] for c in cells), player_to_move=to_move)


@pytest.fixture
def root() -> Node:
    return Node(TicTacToeState.initial())


# 2.1 Node.__init__

def test_root_initial_fields(root):
    assert root.visits == 0
    assert root.value == 0.0
    assert root.children == []
    assert root.parent is None
    assert root.move is None
    assert len(root.untried_moves) == 9
    assert root.player_just_moved is None


def test_child_created_by_hand(root):
    child = Node(root.state.play(4), parent=root, move=4)

    assert child.parent is root
    assert child.move == 4
    assert child.player_just_moved == 0
    assert len(child.untried_moves) == 8
    assert 4 not in child.untried_moves


# 2.2 is_fully_expanded

def test_root_is_not_fully_expanded(root):
    assert not root.is_fully_expanded()


# 2.3 expand

def test_expand_once(root):
    child = root.expand(random.Random(0))

    assert root.children == [child]
    assert len(root.untried_moves) == 8
    assert child.parent is root
    assert child.move not in root.untried_moves


def test_expand_all_moves(root):
    rng = random.Random(0)
    for _ in range(9):
        root.expand(rng)

    assert root.is_fully_expanded()
    assert {child.move for child in root.children} == set(range(9))


@pytest.mark.parametrize("seed", range(20))
def test_expand_all_moves_any_seed(seed):
    root = Node(TicTacToeState.initial())
    rng = random.Random(seed)
    for _ in range(9):
        root.expand(rng)

    assert {child.move for child in root.children} == set(range(9))


# 2.4 update

def test_update_accumulates(root):
    root.update(1.0)
    root.update(0.5)
    root.update(0.0)

    assert root.visits == 3
    assert root.value == pytest.approx(1.5)


# 2.5 ucb1

def test_ucb1_matches_hand_calculation(root):
    child = Node(root.state.play(4), parent=root, move=4)
    root.visits = 10
    child.visits = 2
    child.value = 1.0

    # 1.0 / 2 + c * sqrt(ln(10) / 2)
    assert child.ucb1(0.0) == pytest.approx(0.5)
    assert child.ucb1(1.0) == pytest.approx(1.5729830)
    assert child.ucb1(math.sqrt(2)) == pytest.approx(2.0174271)


# 2.6 best_child

def _two_children(root: Node) -> tuple[Node, Node]:
    weak = Node(root.state.play(0), parent=root, move=0)
    strong = Node(root.state.play(4), parent=root, move=4)
    root.children = [weak, strong]
    root.visits = 20
    weak.visits, weak.value = 10, 3.0      # average 0.3
    strong.visits, strong.value = 10, 7.0  # average 0.7
    return weak, strong


def test_best_child_greedy_picks_higher_average(root):
    _, strong = _two_children(root)

    assert root.best_child(0.0) is strong


def test_best_child_exploration_prefers_rarely_visited(root):
    rare = Node(root.state.play(0), parent=root, move=0)
    frequent = Node(root.state.play(4), parent=root, move=4)
    root.children = [rare, frequent]
    root.visits = 101
    rare.visits, rare.value = 1, 0.0          # average 0.0, big bonus
    frequent.visits, frequent.value = 100, 60.0  # average 0.6, small bonus

    assert root.best_child(0.0) is frequent
    assert root.best_child(1.41) is rare


def test_best_child_tie_returns_first(root):
    first, second = _two_children(root)
    second.value = first.value

    assert root.best_child(1.41) is first


# 3.1 select

def test_select_fresh_root_returns_root(root):
    assert select(root, 1.41) is root


def test_select_terminal_root_returns_root():
    terminal = Node(make("XXXOO....", to_move=1))

    assert select(terminal, 1.41) is terminal


# 3.2 rollout

def test_rollout_ends_in_terminal_state():
    final = rollout(TicTacToeState.initial(), random.Random(1))

    assert final.is_terminal()


def test_rollout_same_seed_same_result():
    start = TicTacToeState.initial()

    assert rollout(start, random.Random(1)) == rollout(start, random.Random(1))


def test_rollout_on_terminal_state_returns_it():
    terminal = make("XXXOO....", to_move=1)

    assert rollout(terminal, random.Random(1)) == terminal


# 3.3 backpropagate

def test_backpropagate_uses_each_node_perspective(root):
    child = Node(root.state.play(0), parent=root, move=0)      # X moved
    grandchild = Node(child.state.play(3), parent=child, move=3)  # O moved
    x_won = make("XXXOO....", to_move=1)

    backpropagate(grandchild, x_won)

    assert root.visits == child.visits == grandchild.visits == 1
    assert child.value == 1.0
    assert grandchild.value == 0.0


# 3.4 build_tree

@pytest.mark.parametrize("iterations", [1, 9, 50, 200])
def test_build_tree_visit_counts(iterations):
    root = build_tree(TicTacToeState.initial(), iterations, random.Random(0))

    assert root.visits == iterations
    assert sum(child.visits for child in root.children) == iterations


def test_build_tree_expands_all_root_moves():
    root = build_tree(TicTacToeState.initial(), 9, random.Random(0))

    assert len(root.children) == 9


# 3.5 best_move and search

def test_best_move_picks_most_visited(root):
    a = Node(root.state.play(0), parent=root, move=0)
    b = Node(root.state.play(4), parent=root, move=4)
    root.children = [a, b]
    a.visits, a.value = 3, 3.0   # better average, fewer visits
    b.visits, b.value = 10, 6.0

    assert best_move(root) == 4


def test_search_returns_legal_move():
    state = TicTacToeState.initial()

    assert search(state, 100, random.Random(0)) in state.legal_moves()


def test_search_on_terminal_state_raises():
    with pytest.raises(ValueError):
        search(make("XXXOO....", to_move=1), 100, random.Random(0))


# 4 behaviour

ITERATIONS = 1000


def play_game(choose_x, choose_o) -> TicTacToeState:
    """Play from the initial state until the end; choose_* map state -> move."""
    state = TicTacToeState.initial()
    while not state.is_terminal():
        choose = choose_x if state.player_to_move == 0 else choose_o
        state = state.play(choose(state))
    return state


@pytest.mark.parametrize(
    ("cells", "to_move", "expected"),
    [
        ("XX.OO....", 0, 2),  # win in one move
        ("XX..O....", 1, 2),  # block
        ("OO.XX...X", 1, 2),  # own win beats blocking
    ],
    ids=["wins", "blocks", "win-over-block"],
)
def test_search_finds_obvious_move(cells, to_move, expected):
    assert search(make(cells, to_move), ITERATIONS, random.Random(0)) == expected


def test_search_is_deterministic_for_same_seed():
    state = TicTacToeState.initial()

    assert search(state, ITERATIONS, random.Random(7)) == search(state, ITERATIONS, random.Random(7))


def test_mcts_never_loses_to_random_player():
    rng = random.Random(3)

    def random_player(state):
        return rng.choice(state.legal_moves())

    def mcts_player(state):
        return search(state, ITERATIONS, rng)

    as_x = [play_game(mcts_player, random_player).winner() for _ in range(20)]
    as_o = [play_game(random_player, mcts_player).winner() for _ in range(20)]

    assert 1 not in as_x
    assert 0 not in as_o


def test_mcts_vs_mcts_is_always_a_draw():
    rng = random.Random(5)

    def mcts_player(state):
        return search(state, ITERATIONS, rng)

    for _ in range(3):
        assert play_game(mcts_player, mcts_player).winner() is None
