from __future__ import annotations

import io
from typing import Optional

import chess
import chess.pgn
from chess import Square


class Game:
    board: chess.Board
    pgn: chess.pgn
    game: chess.pgn.Game
    ply: int

    def __init__(self, board: chess.Board, pgn: chess.pgn.Game):
        self.board = board
        self.pgn = pgn
        self.game = self.pgn.game()
        self.ply = 0

    def fromPgnText(pgn_text) -> Game:
        if isinstance(pgn_text, str):
            pgn_text = io.StringIO(pgn_text)
        pgn = chess.pgn.read_game(pgn_text)
        return Game(chess.Board(), pgn)

    def hasMoreMoves(self) -> bool:
        return not self.game.is_end()

    def getFromSquare(self) -> Square:
        return self.game.next().move.from_square

    def getToSquare(self) -> Square:
        return self.game.next().move.to_square

    def advance(self, plies: int = 1) -> None:
        """
        Advance the position.

        Args:
            plies (int, optional): Number of plies from the pgn to apply.
            Defaults to 1.

        Returns:
            Boolean: True if the position could be advanced as requested and False
            if there were game ended before that (leaving the position where it
            ended).
        """
        while self.game.next() is not None and plies > 0:
            self.game = self.game.next()
            self.board.push(self.game.move)
            plies = plies - 1
            self.ply = self.ply + 1
        return plies == 0

    def goToStart(self):
        self.game = self.game.root()
        self.ply = 0
        self.board = self.game.board()

    def goToEnd(self):
        self.game = self.game.end()
        self.ply = self.game.ply()
        self.board = self.game.board()

    def goBack(self) -> bool:
        """
        Go back a single move.

        Returns:
            bool: True if it wasn't already at the start of the game.
        """
        if self.game.parent is None:
            return False

        self.game = self.game.parent
        self.ply = self.ply - 1

        self.board = self.game.board()
        return True

    def getCapturedSquare(self) -> Optional[Square]:
        """
        Gets position of captured piece or None if not a capturing move. (Handles en
        passant)
        """
        move = self.game.next().move
        if self.board.is_capture(move):
            if self.board.piece_at(move.to_square) is None:
                assert self.board.ep_square == move.to_square
                if chess.square_rank(move.to_square) == 5:
                    return move.to_square - 8
                else:
                    return move.to_square + 8
            else:
                return move.to_square
        else:
            return None

    def getPromotionPiece(self) -> Optional[chess.PieceType]:
        """
        Gets promotion piece type or None if not a promotion move.
        """
        return self.game.next().move.promotion

    def getCastlingRookMove(self) -> Optional[tuple[Square, Square]]:
        """
        If the current move is a castling move then gets the movement of the rook or
        None otherwise.
        """
        move = self.game.next().move
        if self.board.is_castling(move):
            if self.board.is_queenside_castling(move):
                return (move.to_square - 2, move.to_square + 1)
            else:
                return (move.to_square + 1, move.to_square - 1)
        else:
            return None

    def getKingCheckSquare(self) -> Optional[Square]:
        """
        Gets the position of king that is currently in check.

        Returns:
            Optional(Square): If it is check, then this is the king's square.
            If it's not check then None.
        """
        if self.board.is_check():
            return self.board.king(self.board.turn)
        else:
            return None

    def getPreviousMove(self) -> Optional[tuple[Square, Square]]:
        if self.game.move is None:
            return None
        return (self.game.move.from_square, self.game.move.to_square)

    def getMoves(self) -> chess.pgn.Mainline[chess.pgn.ChildNode]:
        return self.game.mainline()

    def getTurnAndNumber(self) -> Optional[tuple[chess.Color, int]]:
        if self.game.parent is None:
            return None
        else:
            parent = self.game.parent
            return (parent.turn(), parent.board().fullmove_number)

    def replaceNextMove(self, move) -> None:
        if not self.game.is_end():
            self.game.remove_variation(0)
        self.game.add_main_variation(move)

    def getValidMoves(self, square) -> list[Square]:
        return [
            move
            for move in self.board.legal_moves
            if move.from_square == square
        ]
