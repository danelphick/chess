import io
import sys

from PySide6 import QtCore, QtWidgets
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


class MainWindow(QMainWindow):
    board_widget: ChessBoard
    timer: QtCore.QTimer
    next: QPushButton

    def __init__(self):
        super().__init__()

        self.root = QWidget()
        top_layout = QHBoxLayout()
        self.root.setLayout(top_layout)

        self.board_widget = ChessBoard()
        # self.board_widget = ChessBoard(board, pgn)
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
[Event "Live Chess"]
[Site "Chess.com"]
[Date "2015.03.31"]
[Round "?"]
[White "JackOfAllHobbies"]
[Black "johnpanageas"]
[Result "1-0"]
[WhiteElo "837"]
[BlackElo "794"]
[TimeControl "5|0"]
[Termination "JackOfAllHobbies won by checkmate"]

1. e4 Nf6 2. e5 Ne4 3. d3 Nc5 4. d4 Ne4 5. Qd3 d5 6. exd6 Nxd6 7. Nf3 b5 8. Bf4
e5 9. Bxe5 Bf5 10. Qb3 Nc6 11. Bxb5 Qd7 12. O-O Ne4 13. Nc3 a6 14. Ba4 Be6 15.
d5 Bf5 16. Bxc6 Qxc6 17. dxc6 Bc5 18. Bxg7 Rg8 19. Ne5 Rxg7 20. Nxe4 Bxe4 21. g3
f5 22. Rad1 Bf3 23. Rd7 Rd8 24. Rxg7 Rd4 25. Qf7+ Kd8 26. Qg8+ Bf8 27. Qxf8# 1-0
"""
# pgn_text = """
# 1. e4 e5 2. Qh5 Nc6 3. Bc4 Qe7 4. Qxf7 Kd8 5. Qxf8 Qxf8
# """

pgn = chess.pgn.read_game(io.StringIO(pgn_text))
game = Game(chess.Board(), pgn)
window = MainWindow()
controller = Controller(
    game, window.board_widget, window.move_list, window.previous, window.next
)
window.show()

app.exec()
