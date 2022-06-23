from PySide6 import QtGui
from PySide6.QtCore import Qt
from PySide6.QtGui import QColorConstants
from PySide6.QtWidgets import QLabel

from chess_board import HEIGHT
import chess

WIDTH = 10


class EvalBar(QLabel):
    eval: float

    def __init__(self):
        super().__init__()

        self.eval = 0.0

        canvas = QtGui.QPixmap(WIDTH, HEIGHT)
        canvas.fill(Qt.gray)
        self.setPixmap(canvas)
        self.setFixedSize(WIDTH, HEIGHT)
        self.drawBar()

    def updateBar(self, eval):
        self.eval = eval.white().score() / 100.0
        self.drawBar()

    def drawBar(self):
        canvas = self.pixmap()

        eval = (10.0 + max(-10.0, min(10.0, int(self.eval)))) / 20

        white_height = int(HEIGHT * eval)
        black_height = HEIGHT - white_height

        painter = QtGui.QPainter(canvas)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(
            0,
            0,
            WIDTH,
            black_height,
            QColorConstants.Black,
        )
        painter.fillRect(
            0,
            black_height,
            WIDTH,
            white_height,
            QColorConstants.White,
        )

        painter.end()
        self.setPixmap(canvas)
