from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QColorConstants
from PySide6.QtWidgets import QLabel, QWidget, QSizePolicy


def roundedPercentage(value):
    value = value * 100
    return round(value)


class ClickableLabel(QLabel):
    def __init__(self, text, callback):
        super().__init__(text)
        self.callback = callback

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        self.callback()


class TableLabel(ClickableLabel):
    MOVE_STYLE = """
    padding: 4px 4px 4px 2px;
    color: white;
    """

    def __init__(self, callback, text, align):
        super().__init__(text, callback)
        self.setStyleSheet(TableLabel.MOVE_STYLE)
        self.setAlignment(align | QtCore.Qt.AlignVCenter)


class WinDrawLossWidget(ClickableLabel):
    WIN_COLOR = QColor(0x3E9833)
    DRAW_COLOR = QColorConstants.Gray
    LOSS_COLOR = QColor(0xD32F2F)

    win_percentage: int
    draw_percentage: int
    loss_percentage: int

    def draw(self):
        width = self.width()
        win_width = round(width / 100 * self.win_percentage)
        draw_width = round(width / 100 * self.draw_percentage)
        loss_width = width - win_width - draw_width
        canvas = QtGui.QPixmap(width, 20)
        painter = QtGui.QPainter(canvas)
        painter.fillRect(0, 0, win_width, 20, self.WIN_COLOR)
        painter.fillRect(win_width, 0, draw_width, 20, self.DRAW_COLOR)
        painter.fillRect(
            win_width + draw_width,
            0,
            loss_width,
            20,
            self.LOSS_COLOR,
        )

        def drawPercentageText(left, width, value, color):
            MINIMUM_WIDTH = 18
            MINIMUM_WIDTH_WITH_SIGN = 30
            if width > MINIMUM_WIDTH:
                text = str(value)
                if width > MINIMUM_WIDTH_WITH_SIGN:
                    text += "%"
                painter.setPen(color)
                painter.drawText(
                    QRectF(left, 0, width, 20),
                    Qt.AlignCenter,
                    text,
                )

        drawPercentageText(0, win_width, self.win_percentage, QColorConstants.White)
        drawPercentageText(
            win_width,
            draw_width,
            self.draw_percentage,
            QColorConstants.Black,
        )
        drawPercentageText(
            width - loss_width,
            loss_width,
            self.loss_percentage,
            QColorConstants.White,
        )

        painter.end()
        self.setPixmap(canvas)

    def __init__(self, callback, wins, draws, losses, total_moves):
        super().__init__(None, callback)
        self.win_percentage = roundedPercentage(wins / total_moves)
        self.draw_percentage = roundedPercentage(draws / total_moves)
        self.loss_percentage = roundedPercentage(losses / total_moves)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.draw()

    def sizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(100, 20)

    def minimumSizeHint(self) -> QtCore.QSize:
        return QtCore.QSize(100, 20)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        self.draw()
        return super().resizeEvent(event)


class OpeningsPane(QtWidgets.QScrollArea):
    def __init__(self):
        super().__init__()
        self.setMoves([], None)
        self.setWidgetResizable(True)
        (left, _, right, _) = self.move_grid.getContentsMargins()
        self.setMinimumWidth(50 + 60 + 100 + left + right + 2)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def setMovesText(self, text):
        self.widget = QLabel(text)
        self.widget.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.setWidget(self.widget)
        self.widget.setContentsMargins(0, 5, 0, 0)

    def setMovesLoading(self):
        self.setMovesText("Loading moves...")

    def setMoves(self, moves, controller):
        if not moves:
            self.setMovesText("No moves found in database")

        self.widget = QWidget()
        self.setWidget(self.widget)
        self.move_grid = QtWidgets.QGridLayout()
        self.widget.setLayout(self.move_grid)

        self.move_grid.setSpacing(0)
        self.move_grid.setColumnStretch(0, 0)
        self.move_grid.setColumnStretch(1, 0)
        self.move_grid.setColumnStretch(2, 1)
        self.move_grid.setColumnMinimumWidth(0, 50)
        self.move_grid.setColumnMinimumWidth(1, 60)
        self.move_grid.setColumnMinimumWidth(2, 100)
        self.move_grid.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)

        if moves:
            for move, row in zip(
                sorted(moves, key=lambda x: x[1], reverse=True), range(len(moves))
            ):
                move_text = move[0]
                if move_text is None:
                    continue
                callback = lambda move_text=move_text: controller.moveFromSan(move_text)

                move_label = TableLabel(callback, move_text, QtCore.Qt.AlignLeft)
                self.move_grid.addWidget(move_label, row, 0)

                total_moves = move[1]
                total_label = TableLabel(
                    callback, str(total_moves), QtCore.Qt.AlignRight
                )
                self.move_grid.addWidget(total_label, row, 1)

                self.move_grid.addWidget(
                    WinDrawLossWidget(callback, 0, total_moves, 0, total_moves),
                    row,
                    2,
                )
        else:
            self.move_grid.addWidget(
                QLabel("No moves found in database"),
                0,
                0,
                1,
                -1,
                QtCore.Qt.AlignHCenter,
            )

        self.move_grid.setRowStretch(len(moves) + 1, 1)
