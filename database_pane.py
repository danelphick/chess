from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QColorConstants
from PySide6.QtWidgets import QLabel, QWidget


def roundedPercentageForUi(value):
    value = value * 100
    return round(value)


class DatabasePane(QtWidgets.QScrollArea):
    MOVE_STYLE = """
    padding: 4px 4px 4px 2px;
    color: white;
    """

    def __init__(self):
        super().__init__()
        self.setMoves([])
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def setMoves(self, moves):
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.move_grid = QtWidgets.QGridLayout()
        self.widget.setLayout(self.move_grid)

        self.move_grid.setSpacing(0)
        self.move_grid.setColumnStretch(3, 1)
        self.move_grid.setColumnMinimumWidth(0, 50)
        self.move_grid.setColumnMinimumWidth(1, 60)
        self.move_grid.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)

        win_color = QColor(0x3E9833)
        draw_color = QColorConstants.Gray
        loss_color = QColor(0xD32F2F)

        for move, row in zip(moves, range(len(moves))):
            move_text = move[3]
            if move_text is None:
                continue
            move_label = QLabel(move_text)
            move_label.setStyleSheet(DatabasePane.MOVE_STYLE)
            self.move_grid.addWidget(move_label, row, 0)

            total_moves = move[4]
            total_label = QLabel(str(total_moves))
            total_label.setStyleSheet(DatabasePane.MOVE_STYLE)
            total_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.move_grid.addWidget(total_label, row, 1)

            win_percentage = roundedPercentageForUi(move[0] / total_moves)
            draw_percentage = roundedPercentageForUi(move[1] / total_moves)
            loss_percentage = roundedPercentageForUi(move[2] / total_moves)

            chances_label = QLabel()
            chances_label.setMinimumSize(100, 20)
            canvas = QtGui.QPixmap(100, 20)
            painter = QtGui.QPainter(canvas)
            painter.fillRect(0, 0, win_percentage, 20, win_color)
            painter.fillRect(win_percentage, 0, draw_percentage, 20, draw_color)
            painter.fillRect(
                win_percentage + draw_percentage,
                0,
                100 - (win_percentage + draw_percentage),
                20,
                loss_color,
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
            chances_label.setPixmap(canvas)
            self.move_grid.addWidget(chances_label, row, 2)

        self.move_grid.setRowStretch(len(moves) + 1, 1)
        self.move_grid.setColumnStretch(3, 1)
