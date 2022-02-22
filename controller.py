import chess
from chess_board import ChessBoard
from game import Game
from move_list import MoveList
from PySide6.QtWidgets import QPushButton


class Controller:
    game: Game
    chess_board: ChessBoard
    currentTurnAndNumber: tuple[chess.Color, int]

    def __init__(
        self,
        game: Game,
        chess_board: ChessBoard,
        move_list: MoveList,
        previous: QPushButton,
        next: QPushButton,
    ):
        self.game = game
        self.chess_board = chess_board
        self.move_list = move_list
        self.previous = previous
        self.next = next
        self.currentTurnAndNumber = (chess.WHITE, 0)

        self.previous.clicked.connect(self.previousMove)
        self.next.clicked.connect(self.nextMove)

        self.move_list.setMoves(game.getMoves())
        self.updateMoveListPosition()
        self.chess_board.setupBoard(game.board)

    def updateMoveListPosition(self):
        new = self.game.getTurnAndNumber()
        self.move_list.setCurrentMove(new, self.currentTurnAndNumber)
        self.currentTurnAndNumber = new

    def nextMove(self):
        self.chess_board.cancelAnimation()

        if not self.game.hasMoreMoves():
            return

        (fromPos, toPos) = self.game.getFromSquare(), self.game.getToSquare()
        captureSquare = self.game.getCapturedSquare()

        if captureSquare is not None:
            self.chess_board.capturePiece(captureSquare)
        self.chess_board.movePiece(
            fromPos, toPos, promoteTo=self.game.getPromotionPiece()
        )

        castlingRookMove = self.game.getCastlingRookMove()
        if castlingRookMove is not None:
            self.chess_board.movePiece(castlingRookMove[0], castlingRookMove[1])

        self.chess_board.startAnimation()

        self.game.advance()

        self.chess_board.drawBoard(
            checkSquare=self.game.getKingCheckSquare(), move=(fromPos, toPos)
        )

        self.updateMoveListPosition()

    def previousMove(self):
        self.chess_board.cancelAnimation()
        if not self.game.goBack():
            return

        (fromPos, toPos) = self.game.getFromSquare(), self.game.getToSquare()

        self.chess_board.drawBoard(
            checkSquare=self.game.getKingCheckSquare(),
            move=self.game.getPreviousMove(),
        )

        if self.game.getPromotionPiece() is not None:
            self.chess_board.changePiece(toPos, chess.PAWN)

        captureSquare = self.game.getCapturedSquare()

        self.chess_board.movePiece(fromPos, toPos, reverse=True)
        if captureSquare is not None:
            self.chess_board.addPiece(
                captureSquare, self.game.board.piece_at(captureSquare), fadeIn=True
            )

        castlingRookMove = self.game.getCastlingRookMove()
        if castlingRookMove is not None:
            self.chess_board.movePiece(
                castlingRookMove[0], castlingRookMove[1], reverse=True
            )

        self.chess_board.startAnimation()

        self.updateMoveListPosition()
