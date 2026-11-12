import pytest
from hypothesis import given, strategies as st

from salon.search.tictactoe import LINES, TicTacToeState

SYMBOLS = {"X": 0, "O": 1, ".": None}


def make(cells: str, to_move: int) -> TicTacToeState:
    """'XX.OO....' -> state. X=0, O=1, '.'=empty."""
    return TicTacToeState(board=tuple(SYMBOLS[c] for c in cells), player_to_move=to_move)


DRAW = "XOXXOOOXX"


# initial


def test_initial_board_is_empty():
    s = TicTacToeState.initial()
    assert s.board == (None,) * 9
    assert s.player_to_move == 0


# winner


def test_no_winner_on_empty_board():
    assert TicTacToeState.initial().winner() is None


@pytest.mark.parametrize(
    "cells, expected",
    [
        ("XXX......", 0),
        ("O..O..O..", 1),
        ("X...X...X", 0),
        (DRAW, None),
    ],
)
def test_winner_examples(cells, expected):
    assert make(cells, 0).winner() == expected


@pytest.mark.parametrize("line", LINES)
def test_every_line_wins(line):
    board = tuple(0 if i in line else None for i in range(9))
    assert TicTacToeState(board=board, player_to_move=1).winner() == 0


# is_terminal


@pytest.mark.parametrize(
    "cells, expected",
    [
        (".........", False),
        ("XO.......", False),
        ("XXX......", True),
        (DRAW, True),
    ],
)
def test_is_terminal(cells, expected):
    assert make(cells, 0).is_terminal() is expected


# legal_moves


def test_legal_moves_on_empty_board():
    assert TicTacToeState.initial().legal_moves() == list(range(9))


def test_legal_moves_skip_taken_cells():
    assert make("X...O....", 0).legal_moves() == [1, 2, 3, 5, 6, 7, 8]


def test_no_legal_moves_after_win():
    assert make("XXXOO....", 1).legal_moves() == []


def test_no_legal_moves_on_full_board():
    assert make(DRAW, 0).legal_moves() == []


# play


def test_play_places_mark_and_switches_player():
    s = TicTacToeState.initial().play(4)
    assert s.board[4] == 0
    assert s.player_to_move == 1


def test_play_does_not_modify_original_state():
    s = TicTacToeState.initial()
    s.play(4)
    assert s.board[4] is None
    assert s.player_to_move == 0


def test_play_on_taken_cell_raises():
    s = TicTacToeState.initial().play(4)
    with pytest.raises(ValueError):
        s.play(4)


def test_play_after_game_over_raises():
    with pytest.raises(ValueError):
        make("XXXOO....", 1).play(8)


# reward


def test_reward_for_win():
    s = make("XXXOO....", 1)
    assert s.reward(0) == 1.0
    assert s.reward(1) == 0.0


def test_reward_for_draw():
    s = make(DRAW, 0)
    assert s.reward(0) == 0.5
    assert s.reward(1) == 0.5


def test_reward_while_game_in_progress_raises():
    with pytest.raises(ValueError):
        TicTacToeState.initial().reward(0)


# whole random games


@given(st.randoms(use_true_random=False))
def test_random_game_always_ends(rnd):
    s = TicTacToeState.initial()
    moves = 0
    while not s.is_terminal():
        s = s.play(rnd.choice(s.legal_moves()))
        moves += 1
    assert moves <= 9
    assert s.legal_moves() == []
