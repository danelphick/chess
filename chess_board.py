from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QColorConstants
from PySide6.QtWidgets import QLabel, QWidget

import chess
import chess.pgn
from game import Game

SQUARE_SIZE = 80
LEFT_MARGIN = 20
RIGHT_MARGIN = 20
TOP_MARGIN = 20
BOTTOM_MARGIN = 20
WIDTH = SQUARE_SIZE * 8 + LEFT_MARGIN + RIGHT_MARGIN
HEIGHT = SQUARE_SIZE * 8 + TOP_MARGIN + TOP_MARGIN
ANIMATION_DURATION = 200


def squarePositionFromRankAndFile(rank: int, file: int):
    return QtCore.QPoint(
        SQUARE_SIZE * file + LEFT_MARGIN,
        (7 - rank) * SQUARE_SIZE + TOP_MARGIN,
    )


def squarePosition(square: int):
    rank = chess.square_rank(square)
    file = chess.square_file(square)
    return squarePositionFromRankAndFile(rank, file)


class Piece:
    def createPixmap(piece_name: str):
        return QtGui.QIcon("pieces/" + piece_name + ".svg").pixmap(
            SQUARE_SIZE, SQUARE_SIZE
        )

    IMAGE_MAP = None

    def image_map(type, color):
        if Piece.IMAGE_MAP is None:
            Piece.IMAGE_MAP = {
                (chess.PAWN, chess.WHITE): Piece.createPixmap("white_pawn"),
                (chess.BISHOP, chess.WHITE): Piece.createPixmap("white_bishop"),
                (chess.KNIGHT, chess.WHITE): Piece.createPixmap("white_knight"),
                (chess.ROOK, chess.WHITE): Piece.createPixmap("white_rook"),
                (chess.QUEEN, chess.WHITE): Piece.createPixmap("white_queen"),
                (chess.KING, chess.WHITE): Piece.createPixmap("white_king"),
                (chess.PAWN, chess.BLACK): Piece.createPixmap("black_pawn"),
                (chess.BISHOP, chess.BLACK): Piece.createPixmap("black_bishop"),
                (chess.KNIGHT, chess.BLACK): Piece.createPixmap("black_knight"),
                (chess.ROOK, chess.BLACK): Piece.createPixmap("black_rook"),
                (chess.QUEEN, chess.BLACK): Piece.createPixmap("black_queen"),
                (chess.KING, chess.BLACK): Piece.createPixmap("black_king"),
            }

        a = Piece.IMAGE_MAP[(type, color)]
        return a

    def __init__(
        self,
        parent: QWidget,
        type: int,
        color: bool,
        rank: int,
        file: int,
    ):
        self.color = color
        self.rank = rank
        self.file = file
        self.widget = QLabel(parent)
        self.widget.resize(SQUARE_SIZE, SQUARE_SIZE)
        self.widget.move(squarePositionFromRankAndFile(rank, file))
        self.changeType(type)

    def changeType(self, newType):
        self.type = newType
        self.widget.setPixmap(Piece.image_map(newType, self.color))


class ChessBoard(QLabel):
    anim: QtCore.QAbstractAnimation
    game: Game
    positions: dict[int, Piece]
    pieces: list[Piece]

    def __init__(self):
        super().__init__()

        self.anim = None
        self.positions = {}

        canvas = QtGui.QPixmap(WIDTH, HEIGHT)
        canvas.fill(Qt.gray)
        self.setPixmap(canvas)
        self.drawBoard()

    def setupBoard(self, board: chess.Board):
        # TODO: this should work for an already set up board
        for color in (chess.WHITE, chess.BLACK):
            for type in (
                chess.PAWN,
                chess.KNIGHT,
                chess.BISHOP,
                chess.ROOK,
                chess.QUEEN,
                chess.KING,
            ):
                squares = board.pieces(type, color)
                for square in squares:
                    self.addPiece(square, chess.Piece(type, color))

    def addAnimation(self, anim):
        if self.anim is None:
            self.anim = QtCore.QParallelAnimationGroup()

        self.anim.addAnimation(anim)

    def movePiece(
        self,
        fromPos: int,
        toPos: int,
        reverse: bool = False,
        promoteTo: chess.PieceType = None,
    ):
        if reverse:
            fromPos, toPos = toPos, fromPos
        piece = self.positions[fromPos]
        self.positions[toPos] = self.positions.pop(fromPos)
        anim = QPropertyAnimation(piece.widget, b"pos")
        anim.setEndValue(squarePosition(toPos))
        anim.setDuration(ANIMATION_DURATION)
        anim.setEasingCurve(QtCore.QEasingCurve.InOutCubic)
        self.addAnimation(anim)
        if promoteTo:
            anim.finished.connect(lambda: self.changePiece(toPos, promoteTo))

    def changePiece(self, toPos: int, type: chess.PieceType):
        self.positions[toPos].changeType(type)

    def createPieceFadeAnimation(self, piece: Piece, reverse: bool = False):
        effect = QtWidgets.QGraphicsOpacityEffect(self)
        piece.widget.setGraphicsEffect(effect)
        piece.widget.lower()
        fadeAnim = QPropertyAnimation(effect, b"opacity")
        if reverse:
            fadeAnim.setStartValue(0)
            fadeAnim.setEndValue(1)
            fadeAnim.setEasingCurve(QEasingCurve.OutQuad)
        else:
            fadeAnim.setStartValue(1)
            fadeAnim.setEndValue(0)
            fadeAnim.setEasingCurve(QEasingCurve.InQuad)
        fadeAnim.setDuration(ANIMATION_DURATION)
        return fadeAnim

    def capturePiece(self, pos: int):
        piece = self.positions[pos]
        self.addAnimation(self.createPieceFadeAnimation(piece))
        del self.positions[pos]

    def addPiece(self, pos: int, chess_piece: chess.Piece, fadeIn=False):
        piece = Piece(
            self,
            chess_piece.piece_type,
            chess_piece.color,
            chess.square_rank(pos),
            chess.square_file(pos),
        )
        self.positions[pos] = piece
        piece.widget.lower()
        piece.widget.show()
        if fadeIn:
            self.addAnimation(self.createPieceFadeAnimation(piece, reverse=True))

    def drawBoard(self, checkSquare=None, move=None):
        canvas = self.pixmap()
        painter = QtGui.QPainter(canvas)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        for y in range(0, 8):
            for x in range(0, 8):
                # This draws the board upside down hence 7-y
                square = chess.square(x, 7 - y)
                if move is not None and (square == move[0] or square == move[1]):
                    color = (
                        QColorConstants.Svg.darkolivegreen
                        if (x + y) % 2 == 1
                        else QColorConstants.Svg.lightgreen
                    )
                else:
                    color = (
                        QColorConstants.Svg.darkslategray
                        if (x + y) % 2 == 1
                        else QColorConstants.Svg.antiquewhite
                    )
                painter.fillRect(
                    x * SQUARE_SIZE + LEFT_MARGIN,
                    y * SQUARE_SIZE + TOP_MARGIN,
                    SQUARE_SIZE,
                    SQUARE_SIZE,
                    color,
                )

                if square == checkSquare:
                    # Create a red halo emanating from behind the king fading to the
                    # square color actual.
                    HALF_SQUARE_SIZE = SQUARE_SIZE / 2
                    gradient = QtGui.QRadialGradient(
                        QtCore.QPointF(
                            x * SQUARE_SIZE + LEFT_MARGIN + HALF_SQUARE_SIZE,
                            y * SQUARE_SIZE + TOP_MARGIN + HALF_SQUARE_SIZE,
                        ),
                        HALF_SQUARE_SIZE * 1.414,
                    )
                    gradient.setColorAt(0, QColorConstants.Red)
                    gradient.setColorAt(1, QtGui.QColor(255, 0, 0, 0))
                    painter.fillRect(
                        QtCore.QRectF(
                            x * SQUARE_SIZE + LEFT_MARGIN,
                            y * SQUARE_SIZE + TOP_MARGIN,
                            SQUARE_SIZE,
                            SQUARE_SIZE,
                        ),
                        gradient,
                    )

        painter.end()
        self.setPixmap(canvas)

    def cancelAnimation(self):
        if self.anim is not None:
            if self.anim.state() == QtCore.QAbstractAnimation.State.Running:
                self.anim.setCurrentTime(self.anim.duration())
            self.anim = None

    def startAnimation(self):
        if self.anim is not None:
            self.anim.start()
