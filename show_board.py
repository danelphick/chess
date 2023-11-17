import asyncio
import functools
import io
import pathlib
import sys

import qasync
from qasync import asyncSlot, asyncClose, QApplication

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import chess
import chess.pgn
from chess_board import ChessBoard
from controller import Controller
from database_pane import DatabasePane
from eval_bar import EvalBar
from move_list import MoveList
from game import Game
from openings_pane import OpeningsPane

controller = None

# logging.basicConfig(level=logging.DEBUG)


class MainWindow(QMainWindow):
    board_widget: ChessBoard
    eval_board: EvalBar
    timer: QtCore.QTimer
    next: QPushButton
    move_list: MoveList
    database_pane: DatabasePane
    openings_pane: OpeningsPane

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
        self.eval_bar = EvalBar()
        self.board_widget = ChessBoard()
        self.board_widget.setAlignment(QtCore.Qt.AlignTop)
        board_and_analysis_layout = QVBoxLayout()
        eval_and_board_layout = QHBoxLayout()
        eval_and_board_layout.addWidget(self.eval_bar)
        eval_and_board_layout.addWidget(self.board_widget)
        board_and_analysis_layout.addLayout(eval_and_board_layout)
        self.analysis_widget = QLabel()

        self.analysis_widget.setWordWrap(True)
        self.analysis_widget.setStyleSheet("padding: 4px; background: black")
        self.analysis_widget.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

        analysis_height = (
            self.analysis_widget.fontMetrics()
            .boundingRect(
                QtCore.QRect(0, 0, 100, 100),
                QtCore.Qt.TextFlag.TextWordWrap,
                "foo\nfoo\nfoo",
            )
            .height()
            + 4 * 2 * 2  # for padding
        )
        self.analysis_widget.setFixedHeight(analysis_height)
        board_and_analysis_layout.addWidget(self.analysis_widget)
        top_layout.addLayout(board_and_analysis_layout)

        self.first = QPushButton("|<")
        self.previous = QPushButton("<")
        self.next = QPushButton(">")
        self.last = QPushButton(">|")

        tabView = QtWidgets.QTabWidget()
        right_panel_layout = QVBoxLayout()
        top_layout.addLayout(right_panel_layout)
        self.move_list = MoveList()
        tabView.addTab(self.move_list, "Game")

        self.database_pane = DatabasePane()
        tabView.addTab(self.database_pane, "Database")

        self.openings_pane = OpeningsPane()
        tabView.addTab(self.openings_pane, "Openings")

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

    @asyncClose
    async def closeEvent(self, event):
        await controller.stop()


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


def openFile():
    pgn_file, _ = QtWidgets.QFileDialog.getOpenFileName(filter="*.pgn")
    if pgn_file:
        pgn_text = pathlib.Path(pgn_file).read_text()
        setupGame(pgn_text)


window = None


def setupGame(pgn_text):
    global controller, window
    pgn = chess.pgn.read_game(io.StringIO(pgn_text))
    game = Game(chess.Board(), pgn)
    controller = Controller(
        game,
        window.board_widget,
        window.eval_bar,
        window.move_list,
        window.database_pane,
        window.openings_pane,
        window.first,
        window.previous,
        window.next,
        window.last,
        window.analysis_widget,
    )


async def main():
    global window

    def close_future(future, loop):
        loop.call_later(10, future.cancel)
        future.cancel()

    loop = asyncio.get_event_loop()
    future = asyncio.Future()

    app = QApplication.instance()
    app.setWindowIcon(QtGui.QIcon("pieces/white_knight.svg"))

    if hasattr(app, "aboutToQuit"):
        getattr(app, "aboutToQuit").connect(
            functools.partial(close_future, future, loop)
        )

    window = MainWindow()
    setupGame(pgn_text)

    window.show()

    try:
        await future
    except asyncio.CancelledError:
        pass
    return True


if __name__ == "__main__":
    try:
        qasync.run(main())
    except asyncio.CancelledError as e:
        sys.exit(0)
