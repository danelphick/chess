import io
import pathlib
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

        menubar = self.menuBar()
        fileMenu = menubar.addMenu("&File")

        openAction = fileMenu.addAction("&Open")
        openAction.setShortcut("Ctrl+O")
        openAction.setStatusTip("Open game")
        openAction.triggered.connect(openFile)

        self.root = QWidget()
        top_layout = QHBoxLayout()
        self.root.setLayout(top_layout)

        self.board_widget = ChessBoard()
        self.board_widget.setAlignment(QtCore.Qt.AlignTop)
        top_layout.addWidget(self.board_widget)

        self.first = QPushButton("|<")
        self.previous = QPushButton("<")
        self.next = QPushButton(">")
        self.last = QPushButton(">|")

        tabView = QtWidgets.QTabWidget()
        right_panel_layout = QVBoxLayout()
        top_layout.addLayout(right_panel_layout)
        self.move_list = MoveList()

        tabView.addTab(self.move_list, "Game")
        tabView.addTab(QWidget(), "Database")

        right_panel_layout.addWidget(tabView)
        navigation_layout = QHBoxLayout()
        navigation_layout.setSpacing(2)
        navigation_layout.addWidget(self.first)
        navigation_layout.addWidget(self.previous)
        navigation_layout.addWidget(self.next)
        navigation_layout.addWidget(self.last)

        right_panel_layout.addLayout(navigation_layout)
        self.setCentralWidget(self.root)

        QtGui.QShortcut(QtGui.QKeySequence.MoveToNextChar, self.next, self.next.click)
        QtGui.QShortcut(
            QtGui.QKeySequence.MoveToPreviousChar,
            self.previous,
            self.previous.click,
        )
        QtGui.QShortcut(
            QtGui.QKeySequence.MoveToStartOfDocument, self.first, self.first.click
        )
        QtGui.QShortcut(
            QtGui.QKeySequence.MoveToEndOfDocument,
            self.last,
            self.last.click,
        )

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
Nb1 35. c5 Kd5 36. c6 Kc5
"""

controller = None


def openFile():
    pgn_file, _ = QtWidgets.QFileDialog.getOpenFileName(filter="*.pgn")
    if pgn_file:
        pgn_text = pathlib.Path(pgn_file).read_text()
        setupGame(pgn_text)


def setupGame(pgn_text):
    global controller
    pgn = chess.pgn.read_game(io.StringIO(pgn_text))
    game = Game(chess.Board(), pgn)
    controller = Controller(
        game,
        window.board_widget,
        window.move_list,
        window.first,
        window.previous,
        window.next,
        window.last,
    )


window = MainWindow()
setupGame(pgn_text)

window.show()

app.exec()
