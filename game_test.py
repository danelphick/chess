from truth.truth import AssertThat

import chess
import chess.pgn
from game import Game

SCHOLARS_MATE_PGN = """
1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0
"""


def testFromPgnText():
    game = Game.fromPgnText(SCHOLARS_MATE_PGN)
    AssertThat(game.board).IsEqualTo(chess.Board())


def testHasMoreMoves():
    game = Game.fromPgnText(SCHOLARS_MATE_PGN)
    AssertThat(game.hasMoreMoves()).IsTrue()


def testAdvance():
    game = Game.fromPgnText(SCHOLARS_MATE_PGN)
    AssertThat(game.hasMoreMoves()).IsTrue()
    game.advance()
    AssertThat(game.ply).IsEqualTo(1)
    AssertThat(game.hasMoreMoves()).IsTrue()
    game.advance(5)
    AssertThat(game.ply).IsEqualTo(6)
    AssertThat(game.hasMoreMoves()).IsTrue()
    game.advance()
    AssertThat(game.ply).IsEqualTo(7)
    AssertThat(game.hasMoreMoves()).IsFalse()


def testGetSquares():
    game = Game.fromPgnText(SCHOLARS_MATE_PGN)

    # Ply 1
    AssertThat(game.getFromSquare()).IsEqualTo(chess.E2)
    AssertThat(game.getToSquare()).IsEqualTo(chess.E4)

    # Ply 2
    game.advance()
    AssertThat(game.getFromSquare()).IsEqualTo(chess.E7)
    AssertThat(game.getToSquare()).IsEqualTo(chess.E5)


def testGetCapturedSquareSimple():
    game = Game.fromPgnText(SCHOLARS_MATE_PGN)

    # 3. ... Nf6 is not a capture
    game.advance(5)
    AssertThat(game.getCapturedSquare()).IsNone()

    # 4. Qxf7# is a capture
    game.advance()
    AssertThat(game.getCapturedSquare()).IsEqualTo(chess.F7)


def testGetCapturedSquareEnPassant():
    game = Game.fromPgnText(
        """
        1. e4 d5 2. e5 f5 3. exf6 d4 4. c4 dxc3 5. d4 e5 6. d5 c5 7. dxc6 e4
        8. f4 exf3
        """
    )

    # 3. exf6 is en passant
    game.advance(4)
    AssertThat(game.getCapturedSquare()).IsEqualTo(chess.F5)

    # 4. c4 is not a capture
    game.advance(2)
    AssertThat(game.getCapturedSquare()).IsNone()

    # 4. ... dxc3 is en passant
    game.advance()
    AssertThat(game.getCapturedSquare()).IsEqualTo(chess.C4)

    # 7. dxc6 is en passant
    game.advance(5)
    AssertThat(game.getCapturedSquare()).IsEqualTo(chess.C5)

    # 8. ... exf3 is en passant
    game.advance(3)
    AssertThat(game.getCapturedSquare()).IsEqualTo(chess.F4)


def testGetPromotedPieces():
    game = Game.fromPgnText(
        "1. h4 f5 2. h5 f4 3. h6 f3 4. hxg7 fxg2 5. gxh8=Q e6 6. Qxg8 gxf1=B"
    )

    for _ in range(0, 8):
        AssertThat(game.getPromotionPiece()).IsNone()
        game.advance()

    AssertThat(game.getPromotionPiece()).IsEqualTo(chess.QUEEN)

    for _ in range(0, 2):
        game.advance()
        AssertThat(game.getPromotionPiece()).IsNone()

    game.advance()
    AssertThat(game.getPromotionPiece()).IsEqualTo(chess.BISHOP)


def testGetCastlingRookMove1():
    # Tests white king-side and black queen-side castling
    game = Game.fromPgnText("1. e4 d5 2. Be2 Qd6 3. Nf3 Bd7 4. O-O Nc6 5. d3 O-O-O")

    for _ in range(0, 6):
        AssertThat(game.getCastlingRookMove()).IsNone()
        game.advance()

    AssertThat(game.getCastlingRookMove()).IsEqualTo((chess.H1, chess.F1))

    for _ in range(0, 2):
        game.advance()
        AssertThat(game.getCastlingRookMove()).IsNone()

    game.advance()
    AssertThat(game.getCastlingRookMove()).IsEqualTo((chess.A8, chess.D8))


def testGetCastlingRookMove2():
    # Tests white queen-side and black king-side castling
    game = Game.fromPgnText("1. d4 e5 2. Qd3 Be7 3. Bd2 Nf6 4. Nc3 O-O 5. O-O-O")

    for _ in range(0, 7):
        AssertThat(game.getCastlingRookMove()).IsNone()
        game.advance()

    AssertThat(game.getCastlingRookMove()).IsEqualTo((chess.H8, chess.F8))
    game.advance()
    AssertThat(game.getCastlingRookMove()).IsEqualTo((chess.A1, chess.D1))


def testGetKingCheckSquare():
    game = Game.fromPgnText(SCHOLARS_MATE_PGN)

    for _ in range(0, 7):
        AssertThat(game.getKingCheckSquare()).IsNone()
        game.advance()

    AssertThat(game.getKingCheckSquare()).IsEqualTo(chess.E8)


def testGetPreviousMove():
    game = Game.fromPgnText(SCHOLARS_MATE_PGN)
    AssertThat(game.getPreviousMove()).IsNone()
    game.advance()
    AssertThat(game.getPreviousMove()).IsEqualTo((chess.E2, chess.E4))
    game.advance()
    AssertThat(game.getPreviousMove()).IsEqualTo((chess.E7, chess.E5))
    game.goBack()
    AssertThat(game.getPreviousMove()).IsEqualTo((chess.E2, chess.E4))

