import io
import sys

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import chess
import chess.pgn
from chess_board import ChessBoard
from controller import Controller
from move_list import MoveList
from game import Game

app = QtWidgets.QApplication(sys.argv)
app.setWindowIcon(QtGui.QIcon("pieces/white_knight.svg"))


class MainWindow(QMainWindow):
    board_widget: ChessBoard
    timer: QtCore.QTimer
    next: QPushButton

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chess Analyzer")

        self.root = QWidget()
        top_layout = QHBoxLayout()
        self.root.setLayout(top_layout)

        self.board_widget = ChessBoard()
        self.board_widget.setAlignment(QtCore.Qt.AlignTop)
        top_layout.addWidget(self.board_widget)

        self.previous = QPushButton("Previous")
        self.next = QPushButton("Next")

        right_panel = QWidget()
        top_layout.addWidget(right_panel)
        right_panel_layout = QVBoxLayout()
        right_panel.setLayout(right_panel_layout)
        navigation_widget = QWidget()
        navigation_layout = QHBoxLayout()
        navigation_widget.setLayout(navigation_layout)
        navigation_layout.addWidget(self.previous)
        navigation_layout.addWidget(self.next)

        self.move_list = MoveList()

        right_panel_layout.addWidget(self.move_list)
        right_panel_layout.addWidget(navigation_widget)
        self.setCentralWidget(self.root)

    def clickNext(self):
        self.board_widget.cancelAnimation()
        self.board_widget.nextMove()

    def clickPrevious(self):
        self.board_widget.cancelAnimation()
        self.board_widget.goBack()

    def setFromGame(self, board: chess.Board, pgn: chess.pgn.Game):
        self.board_widget.setup(board)
        self.move_list.setMoves(pgn.mainline())


pgn_text = """
[White "player 1"]
[Black "player 2"]
[Result "1/2-1/2"]
[Termination "Game drawn by 50-move rule"]

1. e4 e5 2. d3 Nc6 3. Be3 Bb4+ 4. Nc3 Nf6 5. Nf3 d6 6. Nxe5 Nxe5 7. Be2 Bg4 8.
O-O Bxe2 9. Qxe2 Bxc3 10. bxc3 O-O 11. Rab1 b6 12. Rb5 Rb8 13. Rxe5 dxe5 14. Rb1
c5 15. Qf3 Qd7 16. Bxc5 bxc5 17. Rb3 Rxb3 18. cxb3 Qg4 19. Qxg4 Nxg4 20. a3 f5
21. exf5 Rxf5 22. f3 Ne3 23. b4 cxb4 24. axb4 Rg5 25. g3 Nc2 26. Kf2 Rf5 27. b5
Na3 28. c4 h6 29. Ke3 Kf7 30. Ke4 Ke6 31. h3 Rf7 32. h4 Rd7 33. h5 Rd4+ 34. Ke3
Nb1 35. c5 Kd5 36. c6 Kc5 37. c7 Kxb5 38. g4 Nc3 39. Kd2 Nb1+ 40. Ke2 Nc3+ 41.
Kd2 Kb6 42. c8=Q Nd5 43. Qb8+ Ka6 44. Qxe5 Rf4 45. Qd6+ Kb5 46. Qxd5+ Ka6 47.
Qc6+ Ka5 48. Qc7+ Kb5 49. Qb7+ Kc5 50. Qxa7+ Kd5 51. Qd7+ Ke5 52. Qxg7+ Kd5 53.
Qd7+ Ke5 54. Qc7+ Kd5 55. Qxf4 Ke6 56. Qxh6+ Ke5 57. Qd6+ Kxd6 58. h6 Ke6 59. h7
Kf6 60. d4 Kg7 61. d5 Kxh7 62. d6 Kg7 63. d7 Kf7 64. Ke3 Ke7 65. d8=Q+ Kxd8 66.
f4 Ke7 67. g5 Ke6 68. g6 Kf6 69. f5 Kxf5 70. g7 Kf6 71. g8=Q Ke5 72. Qg5+ Ke6
73. Qg4+ Ke5 74. Qd4+ Ke6 75. Qe4+ Kd6 76. Qf4+ Ke6 77. Qc4+ Kd6 78. Qb4+ Kd5
79. Qb5+ Kd6 80. Qd3+ Ke5 81. Qc3+ Kd5 82. Qa5+ Kd6 83. Qd8+ Ke5 84. Qc7+ Kd5
85. Qd7+ Ke5 86. Qe7+ Kd5 87. Qf7+ Ke5 88. Qh5+ Ke6 89. Qg6+ Ke5 90. Qg3+ Kd5
91. Qf3+ Ke5 92. Qc6 Kf5 93. Qe4+ Kf6 94. Kd4 Kg5 95. Qd5+ Kf6 96. Qe5+ Kg6 97.
Qe6+ Kg5 98. Qe3+ Kg4 99. Qe2+ Kf4 100. Qe5+ Kf3 101. Qe4+ Kg3 102. Qg6+ Kf4
103. Qf6+ Kg4 104. Qg7+ Kf4 105. Qf7+ Kg5 106. Qe7+ Kf5 107. Qc5+ Kf4 108. Qd6+
Kf5 109. Qd7+ Kf4 110. Qc7+ Kf5 111. Qc2+ Kf4 112. Qd2+ Kf5 113. Qd3+ Kf4 114.
Qf1+ Kg4 115. Qg2+ Kf4 116. Qf2+ Kg4 117. Qe3 Kf5 118. Qf3+ Kg5 119. Qg3+ Kf5
120. Qh3+ Kf4 121. Qf1+ Kg3 1/2-1/2
"""

pgn = chess.pgn.read_game(io.StringIO(pgn_text))
game = Game(chess.Board(), pgn)
window = MainWindow()
controller = Controller(
    game, window.board_widget, window.move_list, window.previous, window.next
)
QtGui.QShortcut(QtGui.QKeySequence.MoveToNextChar, window.next, window.next.click)
QtGui.QShortcut(
    QtGui.QKeySequence.MoveToPreviousChar, window.previous, window.previous.click
)
window.show()

app.exec()
