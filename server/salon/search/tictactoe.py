# indexes
#  0 | 1 | 2
# ---+---+---
#  3 | 4 | 5
# ---+---+---
#  6 | 7 | 8

from dataclasses import dataclass

# winning lines
LINES: tuple[tuple[int, int, int], ...] = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6))

@dataclass(frozen=True)
class TicTacToeState:
    board: tuple[int | None, ...]
    player_to_move: int # O=0 X=1

    @classmethod
    def initial(cls) -> "TicTacToeState":
        return cls((None, ) * 9, player_to_move=0)
    
    def winner(self) -> int | None:
        for a, b, c in LINES:
            if self.board[a] is not None and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a]
        
    def is_terminal(self) -> bool:
        result = self.winner()
        if result is None:
            for cell in self.board:
                if cell is None:
                    return False
            return True
        return True
    
    def legal_moves(self) -> list[int]:
        if self.is_terminal():
            return []
        moves = []
        for i, cell in enumerate(self.board):
            if cell is None:
                moves.append(i)
        return moves
    
    def play(self, move: int) -> "TicTacToeState":
        if move not in self.legal_moves():
            raise ValueError(f"illegal move: {move}")
        cells = list(self.board)
        cells[move] = self.player_to_move
        return TicTacToeState(board=tuple(cells), player_to_move=1 - self.player_to_move)

    def reward(self, player: int) -> float:
        if not self.is_terminal():
            raise ValueError("game is not over")
        result = self.winner()
        if result is None:
            return 0.5
        if result == player:
            return 1.0
        return 0.0
