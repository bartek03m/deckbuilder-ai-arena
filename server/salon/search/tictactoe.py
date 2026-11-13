"""Tic-tac-toe used as a simple test game for the MCTS prototype.

Cell indexes:
     0 | 1 | 2
    ---+---+---
     3 | 4 | 5
    ---+---+---
     6 | 7 | 8
"""
from __future__ import annotations

from dataclasses import dataclass

# winning lines
LINES: tuple[tuple[int, int, int], ...] = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))


@dataclass(frozen=True)
class TicTacToeState:
    """Immutable game state: `play()` returns a new state."""

    board: tuple[int | None, ...]
    player_to_move: int  # X=0 (starts), O=1

    @classmethod
    def initial(cls) -> TicTacToeState:
        """Return an empty board with X to move."""
        return cls((None,) * 9, player_to_move=0)

    def winner(self) -> int | None:
        """Return the player who has three in a line, or None."""
        for a, b, c in LINES:
            if self.board[a] is not None and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a]
        return None

    def is_terminal(self) -> bool:
        """Return True when someone has won or the board is full."""
        result = self.winner()
        if result is None:
            for cell in self.board:
                if cell is None:
                    return False
            return True
        return True

    def legal_moves(self) -> list[int]:
        """Return the indexes of empty cells, or [] when the game is over."""
        if self.is_terminal():
            return []
        moves = []
        for i, cell in enumerate(self.board):
            if cell is None:
                moves.append(i)
        return moves

    def play(self, move: int) -> TicTacToeState:
        """Return the state after the current player marks `move`."""
        if move not in self.legal_moves():
            raise ValueError(f"illegal move: {move}")
        cells = list(self.board)
        cells[move] = self.player_to_move
        return TicTacToeState(board=tuple(cells), player_to_move=1 - self.player_to_move)

    def reward(self, player: int) -> float:
        """Return 1.0 for a win, 0.5 for a draw and 0.0 for a loss of `player`."""
        if not self.is_terminal():
            raise ValueError("game is not over")
        result = self.winner()
        if result is None:
            return 0.5
        if result == player:
            return 1.0
        return 0.0
