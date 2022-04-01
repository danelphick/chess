from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QColorConstants
from PySide6.QtWidgets import QLabel, QWidget


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

    def __init__(self, callback, wins, draws, losses, total_moves):
        super().__init__(None, callback)
        win_percentage = roundedPercentage(wins / total_moves)
        draw_percentage = roundedPercentage(draws / total_moves)
        loss_percentage = roundedPercentage(losses / total_moves)

        self.setMinimumSize(100, 20)
        canvas = QtGui.QPixmap(100, 20)
        painter = QtGui.QPainter(canvas)
        painter.fillRect(0, 0, win_percentage, 20, self.WIN_COLOR)
        painter.fillRect(win_percentage, 0, draw_percentage, 20, self.DRAW_COLOR)
        painter.fillRect(
            win_percentage + draw_percentage,
            0,
            100 - (win_percentage + draw_percentage),
            20,
            self.LOSS_COLOR,
        )

        def drawPercentageText(left, width, value, color):
            MINIMUM_PERCENTAGE = 18
            MINIMUM_PERCENTAGE_WITH_SIGN = 30
            if value > MINIMUM_PERCENTAGE:
                text = str(value)
                if value > MINIMUM_PERCENTAGE_WITH_SIGN:
                    text += "%"
                painter.setPen(color)
                painter.drawText(
                    QRectF(left, 0, width, 20),
                    Qt.AlignCenter,
                    text,
                )

        drawPercentageText(0, win_percentage, win_percentage, QColorConstants.White)
        drawPercentageText(
            win_percentage,
            100 - loss_percentage,
            draw_percentage,
            QColorConstants.Black,
        )
        drawPercentageText(
            100 - loss_percentage,
            loss_percentage,
            loss_percentage,
            QColorConstants.White,
        )

        painter.end()
        self.setPixmap(canvas)


class DatabasePane(QtWidgets.QScrollArea):
    def __init__(self):
        super().__init__()
        self.setMoves([], None)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def setMoves(self, moves, controller):
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.move_grid = QtWidgets.QGridLayout()
        self.widget.setLayout(self.move_grid)

        self.move_grid.setSpacing(0)
        self.move_grid.setColumnStretch(3, 1)
        self.move_grid.setColumnMinimumWidth(0, 50)
        self.move_grid.setColumnMinimumWidth(1, 60)
        self.move_grid.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)

        for move, row in zip(moves, range(len(moves))):
            move_text = move[3]
            if move_text is None:
                continue
            callback = lambda move_text=move_text: controller.moveFromSan(move_text)

            move_label = TableLabel(callback, move_text, QtCore.Qt.AlignLeft)
            self.move_grid.addWidget(move_label, row, 0)

            total_moves = move[4]
            total_label = TableLabel(callback, str(total_moves), QtCore.Qt.AlignRight)
            self.move_grid.addWidget(total_label, row, 1)

            self.move_grid.addWidget(
                WinDrawLossWidget(callback, move[0], move[1], move[2], total_moves),
                row,
                2,
            )

        self.move_grid.setRowStretch(len(moves) + 1, 1)
        self.move_grid.setColumnStretch(3, 1)
