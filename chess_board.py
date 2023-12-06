from abc import ABC, abstractmethod
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QColorConstants
from PySide6.QtWidgets import QLabel, QWidget

import chess
import chess.pgn

SQUARE_SIZE = 80
HALF_SQUARE_SIZE = SQUARE_SIZE // 2
VALID_MOVE_CIRCLE_RADIUS = SQUARE_SIZE // 6
VALID_CAPTURE_CIRCLE_RADIUS = SQUARE_SIZE * 0.6
LEFT_MARGIN = 20
RIGHT_MARGIN = 20
TOP_MARGIN = 20
BOTTOM_MARGIN = 20
WIDTH = SQUARE_SIZE * 8 + LEFT_MARGIN + RIGHT_MARGIN
HEIGHT = SQUARE_SIZE * 8 + TOP_MARGIN + TOP_MARGIN
ANIMATION_DURATION = 200


class DragHandler(ABC):
    """Abstract piece drag handler."""

    @abstractmethod
    def dragStart(self, widget, pos: QtCore.QPoint) -> None:
        """Called when a drag on a piece starts.

        Args:
            pos (QtCore.QPoint): Position of the mouse when the drag started.
        """
        return NotImplemented

    @abstractmethod
    def dragMove(self, widget, pos: QtCore.QPoint) -> None:
        """Called during a drag on a piece, when the mouse moves.

        Args:
            pos (QtCore.QPoint): Position of the mouse during the update.
        """
        return NotImplemented

    @abstractmethod
    def dragEnd(self, pos: QtCore.QPoint) -> None:
        """Called when a drag on a piece end.

        Args:
            pos (QtCore.QPoint): Position of the mouse at the end of the mouse.
        """
        return NotImplemented


def rankAndFileFromCoords(x: int, y: int, colorPerspective: chess.Color):
    if colorPerspective == chess.WHITE:
        return (7 - (y - TOP_MARGIN) // SQUARE_SIZE, (x - LEFT_MARGIN) // SQUARE_SIZE)
    else:
        return ((y - TOP_MARGIN) // SQUARE_SIZE, 7 - (x - LEFT_MARGIN) // SQUARE_SIZE)


def fileAndRankFromCoords(x: int, y: int, colorPerspective: chess.Color):
    temp = rankAndFileFromCoords(x, y, colorPerspective)
    return temp[1], temp[0]


def squarePositionFromRankAndFile(rank: int, file: int, colorPerspective: chess.Color):
    if colorPerspective == chess.WHITE:
        return QtCore.QPoint(
            SQUARE_SIZE * file + LEFT_MARGIN,
            (7 - rank) * SQUARE_SIZE + TOP_MARGIN,
        )
    else:
        return QtCore.QPoint(
            SQUARE_SIZE * (7 - file) + LEFT_MARGIN,
            rank * SQUARE_SIZE + TOP_MARGIN,
        )


def squarePosition(square: int, colorPerspective: chess.Color):
    rank = chess.square_rank(square)
    file = chess.square_file(square)
    return squarePositionFromRankAndFile(rank, file, colorPerspective)


class PieceWidget(QLabel):
    def __init__(self, chess_board: QWidget):
        super().__init__(chess_board)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if not self.isVisible():
            return

        if event.button() != Qt.LeftButton:
            return

        self.parentWidget().dragStart(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if not (event.buttons() & Qt.LeftButton):
            return

        self.parentWidget().dragMove(event.globalPosition().toPoint())

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.parentWidget().dragEnd(event.globalPosition().toPoint())


class Piece:
    chess_board: QWidget
    color: chess.Color
    type: chess.PieceType
    rank: int
    file: int
    widget: PieceWidget

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
        chess_board: QWidget,
        type: chess.PieceType,
        color: chess.Color,
        rank: int,
        file: int,
        colorPerspective: chess.Color,
    ):
        self.color = color
        self.rank = rank
        self.file = file
        self.widget = PieceWidget(chess_board)
        self.widget.resize(SQUARE_SIZE, SQUARE_SIZE)
        self.widget.move(squarePositionFromRankAndFile(rank, file, colorPerspective))
        self.changeType(type)

    def changeType(self, newType):
        self.type = newType
        self.widget.setPixmap(Piece.image_map(newType, self.color))

    def rotate(self, colorPerspective):
        self.widget.move(
            squarePositionFromRankAndFile(self.rank, self.file, colorPerspective)
        )


class ChessBoard(QLabel):
    anim: QtCore.QAbstractAnimation
    positions: dict[int, Piece]
    firstClickSquare: Optional[int]
    dragPiece: Optional[Piece]
    validMoves: list[chess.Move]
    mouseOverSquare: Optional[chess.Square]

    def __init__(self):
        super().__init__()

        self.anim = None
        self.positions = {}
        self.dragPiece = None
        self.firstClickSquare = None
        self.moveHandler = None
        self.lastMove = None
        self.checkSquare = None
        self.validMoves = []
        self.mouseOverSquare = None
        self.colorPerspective = chess.WHITE

        canvas = QtGui.QPixmap(WIDTH, HEIGHT)
        canvas.fill(Qt.gray)
        self.setPixmap(canvas)
        self.setFixedSize(WIDTH, HEIGHT)
        # Draw the A-H and 1-8 indicators once as they will never be overdrawn
        self.drawRankAndFileIndicators()
        self.drawBoard()
        self.dragWidget = None

    # Methods overridden from DragHandler
    def dragStart(self, pos: QtCore.QPoint) -> None:
        pos = self.mapFromGlobal(pos)
        square = chess.square(
            *fileAndRankFromCoords(pos.x(), pos.y(), self.colorPerspective)
        )
        self.mouseOverSquare = square
        piece = self.positions[square]
        if self.moveHandler.whoseTurn() == piece.color:
            self.validMoves = self.moveHandler.getValidMoves(square)
            self.dragPiece = Piece(
                self,
                piece.type,
                piece.color,
                chess.square_rank(square),
                chess.square_file(square),
                self.colorPerspective,
            )
            self.dragPiece.widget.move(
                pos.x() - HALF_SQUARE_SIZE, pos.y() - HALF_SQUARE_SIZE
            )
            self.dragPiece.widget.show()

            self.firstClickSquare = square
            self.drawBoard()

            piece.widget.opacity = 0.5
            effect = QtWidgets.QGraphicsOpacityEffect(self)
            effect.setOpacity(0.5)
            piece.widget.setGraphicsEffect(effect)
        else:
            if self.firstClickSquare is not None:
                self.makeMove(self.firstClickSquare, square)

    def dragMove(self, pos: QtCore.QPoint) -> None:
        if self.dragPiece is None:
            return

        pos = self.mapFromGlobal(pos)
        self.dragPiece.widget.move(
            pos.x() - HALF_SQUARE_SIZE, pos.y() - HALF_SQUARE_SIZE
        )

        square = chess.square(
            *fileAndRankFromCoords(pos.x(), pos.y(), self.colorPerspective)
        )
        if square == self.mouseOverSquare:
            return
        if not any(square == move.to_square for move in self.validMoves):
            if self.mouseOverSquare is None:
                return
            self.mouseOverSquare = None
        else:
            self.mouseOverSquare = square
        self.drawBoard()

    def dragEnd(self, pos: QtCore.QPoint) -> None:
        if self.dragPiece is None:
            return

        piece_widget = self.positions[self.firstClickSquare].widget
        piece_widget.setGraphicsEffect(None)
        pos = self.mapFromGlobal(pos)
        square = chess.square(
            *fileAndRankFromCoords(pos.x(), pos.y(), self.colorPerspective)
        )
        if square != self.firstClickSquare:
            self.makeMove(self.firstClickSquare, square, instant=True)

        self.dragPiece.widget.setParent(None)
        self.dragPiece = None

    def setupBoard(self, board: chess.Board):
        for piece in self.positions.values():
            piece.widget.setParent(None)
        self.positions = {}
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
        piece.file, piece.rank = chess.square_file(toPos), chess.square_rank(toPos)
        self.positions[toPos] = self.positions.pop(fromPos)
        anim = QPropertyAnimation(piece.widget, b"pos")
        anim.setEndValue(squarePosition(toPos, self.colorPerspective))
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
            piece.widget.clickHandler = None
            fadeAnim.setStartValue(1)
            fadeAnim.setEndValue(0)
            fadeAnim.setEasingCurve(QEasingCurve.InQuad)
            fadeAnim.finished.connect(lambda: piece.widget.setParent(None))
        fadeAnim.setDuration(ANIMATION_DURATION)
        return fadeAnim

    def capturePiece(self, pos: int):
        piece = self.positions[pos]
        fadeAnim = self.createPieceFadeAnimation(piece)
        fadeAnim.finished.connect(lambda: piece.widget.setParent(None))
        self.addAnimation(fadeAnim)
        del self.positions[pos]

    def addPiece(self, pos: int, chess_piece: chess.Piece, fadeIn=False) -> Piece:
        piece = Piece(
            self,
            chess_piece.piece_type,
            chess_piece.color,
            chess.square_rank(pos),
            chess.square_file(pos),
            self.colorPerspective,
        )
        self.positions[pos] = piece
        piece.widget.lower()
        piece.widget.show()
        if fadeIn:
            self.addAnimation(self.createPieceFadeAnimation(piece, reverse=True))

    def clearClicks(self):
        """
        Clear any outstanding clicks (e.g. incomplete moves), but don't redraw
        the board.
        """
        self.firstClickSquare = None
        self.validMoves = []

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        if self.firstClickSquare is None:
            return

        rank, file = rankAndFileFromCoords(ev.x(), ev.y(), self.colorPerspective)

        if not self.makeMove(self.firstClickSquare, chess.square(file, rank)):
            self.clearClicks()
            self.drawBoard()

    DARK_SQUARE = QColorConstants.Svg.darkslategray
    LIGHT_SQUARE = QColorConstants.Svg.antiquewhite
    SELECTED_DARK_SQUARE = QColorConstants.Svg.darkslategray.darker(140)
    SELECTED_LIGHT_SQUARE = QColorConstants.Svg.antiquewhite.darker(140)
    CHECK_DARK_SQUARE = QColorConstants.Svg.darkolivegreen
    CHECK_LIGHT_SQUARE = QColorConstants.Svg.lightgreen

    def setLastMove(self, move: tuple[chess.Square, chess.Square], checkSquare=None):
        self.lastMove = move
        self.checkSquare = checkSquare

    def drawRankAndFileIndicators(self):
        canvas = self.pixmap()
        painter = QtGui.QPainter(canvas)
        fm = QtGui.QFontMetrics(painter.font())
        for y in range(0, 8):
            textToDraw = str(y + 1)
            rect = fm.boundingRect(textToDraw)
            painter.drawStaticText(
                    (LEFT_MARGIN - rect.width()) // 2,
                    y * SQUARE_SIZE
                    + HALF_SQUARE_SIZE
                    + TOP_MARGIN
                    - rect.height() // 2,
                    QtGui.QStaticText(textToDraw),
            )
        for x in range(0, 8):
            textToDraw = chr(x + 65)
            rect = fm.boundingRect(textToDraw)
            painter.drawStaticText(
                    x * SQUARE_SIZE
                    + HALF_SQUARE_SIZE
                    + LEFT_MARGIN
                    - rect.width() // 2,
                    HEIGHT - (TOP_MARGIN + rect.height()) // 2,
                    QtGui.QStaticText(textToDraw),
            )
        painter.end()
        self.setPixmap(canvas)

    def drawBoard(self):
        canvas = self.pixmap()
        painter = QtGui.QPainter(canvas)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        for y in range(0, 8):
            for x in range(0, 8):
                if self.colorPerspective == chess.WHITE:
                    square = chess.square(x, 7 - y)
                else:
                    square = chess.square(7 - x, y)
                if square == self.mouseOverSquare and self.firstClickSquare is not None:
                    color = (
                        ChessBoard.SELECTED_DARK_SQUARE
                        if (x + y) % 2 == 1
                        else ChessBoard.SELECTED_LIGHT_SQUARE
                    )
                elif self.lastMove is not None and (
                    square == self.lastMove[0] or square == self.lastMove[1]
                ):
                    color = (
                        ChessBoard.CHECK_DARK_SQUARE
                        if (x + y) % 2 == 1
                        else ChessBoard.CHECK_LIGHT_SQUARE
                    )
                elif square == self.firstClickSquare:
                    color = (
                        ChessBoard.SELECTED_DARK_SQUARE
                        if (x + y) % 2 == 1
                        else ChessBoard.SELECTED_LIGHT_SQUARE
                    )
                else:
                    color = (
                        ChessBoard.DARK_SQUARE
                        if (x + y) % 2 == 1
                        else ChessBoard.LIGHT_SQUARE
                    )
                painter.fillRect(
                    x * SQUARE_SIZE + LEFT_MARGIN,
                    y * SQUARE_SIZE + TOP_MARGIN,
                    SQUARE_SIZE,
                    SQUARE_SIZE,
                    color,
                )

                if square == self.checkSquare:
                    # Create a red halo emanating from behind the king fading to the
                    # square color actual.
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

                # The lookup loops over the list which could be avoided if we drew the squares in
                # the right order and maintained our position in this list.
                if any(square == move.to_square for move in self.validMoves):
                    radius = VALID_MOVE_CIRCLE_RADIUS
                    if square in self.positions:
                        radius = VALID_CAPTURE_CIRCLE_RADIUS
                    color = (
                        ChessBoard.DARK_SQUARE
                        if (x + y) % 2 == 1
                        else ChessBoard.LIGHT_SQUARE
                    )

                    validHighlight = QColorConstants.DarkYellow
                    validHighlight.setAlphaF(0.7)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(validHighlight)
                    painter.setClipRect(
                        x * SQUARE_SIZE + LEFT_MARGIN,
                        y * SQUARE_SIZE + TOP_MARGIN,
                        SQUARE_SIZE,
                        SQUARE_SIZE,
                    )
                    painter.drawEllipse(
                        QtCore.QPointF(
                            x * SQUARE_SIZE + LEFT_MARGIN + HALF_SQUARE_SIZE,
                            y * SQUARE_SIZE + TOP_MARGIN + HALF_SQUARE_SIZE,
                        ),
                        radius,
                        radius,
                    )
                    painter.setClipping(False)

        painter.end()
        self.setPixmap(canvas)

    def cancelAnimation(self):
        if self.anim is not None:
            if self.anim.state() == QtCore.QAbstractAnimation.State.Running:
                self.anim.setCurrentTime(self.anim.duration())
            self.anim = None

    def clearAnimation(self):
        self.anim = None

    def startAnimation(self):
        if self.anim is not None:
            self.anim.start()
            self.anim.finished.connect(self.clearAnimation)

    def rotate(self, colorPerspective: chess.Color):
        if self.colorPerspective != colorPerspective:
            self.colorPerspective = colorPerspective
            self.clearClicks()
            self.drawBoard()
            for piece in self.positions.values():
                piece.rotate(colorPerspective)

    class PromotionWindow(QWidget):
        def __init__(
            self, whoseTurn: chess.Color, chess_board, move: chess.Move
        ) -> None:
            super().__init__()
            layout = QtWidgets.QVBoxLayout()
            self.label = QLabel("Choose promotion piece")
            layout.addWidget(self.label)
            piece_layout = QtWidgets.QHBoxLayout()
            for type in [
                chess.QUEEN,
                chess.ROOK,
                chess.BISHOP,
                chess.KNIGHT,
            ]:
                piece_button = QtWidgets.QPushButton(
                    icon=Piece.image_map(type, whoseTurn)
                )
                piece_layout.addWidget(piece_button)
                move = chess.Move(move.from_square, move.to_square, promotion=type)
                piece_button.clicked.connect(
                    lambda type=type, move=move: chess_board.promote(move, type)
                )
            layout.addLayout(piece_layout)
            self.setLayout(layout)

    def promote(self, move, promotion_type):
        self.moveHandler.move(
            chess.Move(move.from_square, move.to_square, promotion_type)
        )
        self.promotion_window.hide()

    def makeMove(self, fromSquare, toSquare, instant=True):
        for move in self.validMoves:
            if move.from_square == fromSquare and move.to_square == toSquare:
                if move.promotion is None:
                    return self.moveHandler.move(move, instant=instant)
                else:
                    # Need to select a promotion square first
                    self.promotion_window = ChessBoard.PromotionWindow(
                        self.moveHandler.whoseTurn(), self, move
                    )
                    self.promotion_window.show()

        return False
