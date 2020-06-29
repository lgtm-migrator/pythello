from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Callable, Dict, Optional, Set, Union

import numpy as np

from pythello.board.board import Board
from pythello.utils.validate import Condition, check

if TYPE_CHECKING:
    from pythello.utils.typing import Move, ValidMoves

DIRECTIONS = [(i, j) for i in [-1, 0, 1] for j in [-1, 0, 1] if (i != 0 or j != 0)]
ArrayPredicate = Callable[[Optional[np.ndarray]], bool]


class GridBoard(Board):
    BOARD_SQUARE: ArrayPredicate = lambda board: board is None or (
        len(board.shape) == 2 and board.shape[0] == board.shape[1]
    )

    @check(Condition(BOARD_SQUARE, 'Board must be square'))
    def __init__(self, size: int = 8, board: Optional[np.ndarray] = None):
        super().__init__(size if board is None else board.shape[0])
        self._valid: Dict[int, Dict[Move, ValidMoves]] = defaultdict(dict)

        if board is None:
            self._board = np.zeros((self._size, self._size), dtype=np.int8)
            self.reset()
        else:
            self._board = board.copy()

    def __mul__(self, other: Union[Board, int]) -> Board:
        return GridBoard(board=self._board * other)

    def captured(self, player: int, move: Move) -> Set[Move]:
        return self._valid[player][move]

    def get_pieces(self, player: int) -> Set[Move]:
        pieces = np.nonzero(self._board == player)
        return {(row, col) for row, col in zip(*pieces)}

    @property
    def num_empty(self) -> int:
        return int(np.count_nonzero(self._board == 0))

    def place_piece(self, piece: Move, player: int) -> None:
        for p in self._valid[player][piece]:
            self._board[p] = player

    def player_score(self, player: int) -> int:
        return int(np.count_nonzero(self._board == player))

    def reset(self) -> None:
        mid = int(self._size / 2)
        self._board.fill(0)
        self._board[mid, mid - 1] = 1
        self._board[mid - 1, mid] = 1
        self._board[mid, mid] = -1
        self._board[mid - 1, mid - 1] = -1

    def score(self) -> int:
        return int(self._board.sum())

    def valid_moves(self, player: int) -> ValidMoves:
        valid = defaultdict(set)

        for pt in zip(*np.where(self._board == player)):
            for dir in DIRECTIONS:
                index = [x if d == 0 else slice(x, None, d) for x, d in zip(pt, dir)]
                line = self._board[tuple(index)]

                if len(line.shape) == 2:
                    line = line.diagonal()

                n = np.argmax(line == 0)

                if np.all(line[1:n] == -player) and n > 1:
                    pieces = [
                        (pt[0] + i * dir[0], pt[1] + i * dir[1])
                        for i in range(1, n + 1)
                    ]
                    valid[pieces[-1]].update(pieces)

        self._valid[player] = valid
        return set(valid.keys())
