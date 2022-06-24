from PySide6.QtWidgets import QWidget, QLabel, QPushButton
from PySide6 import QtWidgets, QtCore

import chess


class MoveList(QtWidgets.QScrollArea):
    MOVE_STYLE = """
    padding-left: 8px;
    padding-right: 8px;
    padding-top: 4px;
    padding-bottom: 2px;
    text-align: left;
    color: white;
    border: none;
    """

    CURRENT_MOVE_STYLE = (
        MOVE_STYLE
        + """
    background-color: lightgray;
    color: black;
    """
    )

    def __init__(self):
        super().__init__()
        self.setMoves(None, [])
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff);

    def removeMove(self, row, color):
        if color == chess.BLACK:
            item = self.move_grid.itemAtPosition(row, 2)
        else:
            item = self.move_grid.itemAtPosition(row, 1)
            # if removing the white move then also remove the move number.
            self.move_grid.itemAtPosition(row, 0).widget().setParent(None)
            self.move_grid.setRowMinimumHeight(row, 0)
            self.move_grid.setRowStretch(row, 0)

        item.widget().setParent(None)

    def createClickableLabel(self, text, turnAndMove):
        label = QPushButton(text)
        label.setStyleSheet(MoveList.MOVE_STYLE)
        if turnAndMove is not None:
            label.clicked.connect(lambda: self.controller.selectMove(*turnAndMove))
        return label

    def setMoves(self, controller, moves):
        # Resetting the grid layout itself seems to be very difficult in pyside
        # since you don't seem able to actually delete the layout, so just
        # recreate the widget every time we add a new set of moves.
        self.controller = controller
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.move_grid = QtWidgets.QGridLayout()
        self.widget.setLayout(self.move_grid)

        self.move_grid.setSpacing(0)
        self.move_grid.setColumnStretch(3, 1)
        self.move_grid.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)

        moves = iter(moves)
        row = 0
        try:
            while True:
                white_move = next(moves)
                move_number = row + 1
                white_move_label = self.createClickableLabel(white_move.san(), (chess.WHITE, move_number))
                number_label = self.createClickableLabel(str(move_number), None)
                self.move_grid.addWidget(number_label, row, 0)
                if self.move_grid.itemAtPosition(row, 1):
                    self.move_grid.itemAtPosition(row, 1).widget().setText(
                        white_move.san()
                    )
                else:
                    self.move_grid.addWidget(white_move_label, row, 1)
                black_move_label = self.createClickableLabel(next(moves).san(), (chess.BLACK, move_number))
                self.move_grid.addWidget(black_move_label, row, 2)
                black_move_label.setStyleSheet(MoveList.MOVE_STYLE)
                row = move_number
        except StopIteration:
            pass

        self.move_grid.setRowStretch(row + 1, 1)

    def styleMove(self, turnAndNumber, style, ensureVisible=False):
        if turnAndNumber is None:
            # This is the 0th move before anything has started
            if ensureVisible:
                self.ensureVisible(0, 0)
        else:
            turn, number = turnAndNumber
            item = self.move_grid.itemAtPosition(number - 1, 2 - int(turn))
            if item is not None:
                item.widget().setStyleSheet(style)
                if ensureVisible:
                    QtCore.QTimer.singleShot(0, lambda: self.ensureWidgetVisible(item.widget()))

    def setCurrentMove(self, new, old):
        if old != new:
            self.styleMove(old, MoveList.MOVE_STYLE)

        self.styleMove(new, MoveList.CURRENT_MOVE_STYLE, ensureVisible=True)

    def addMove(self, turnAndNumber, move):
        turn, number = turnAndNumber
        row = number - 1
        move_label = self.createClickableLabel(move)
        if turn == chess.WHITE:
            number_label = self.createClickableLabel(str(number), turnAndNumber)
            self.move_grid.addWidget(number_label, row, 0)
            self.move_grid.addWidget(move_label, row, 1)
        else:
            self.move_grid.addWidget(move_label, row, 2)

    def removeMoves(self, turnAndNumber):
        turn, number = turnAndNumber
        row = number - 1
        if turn == chess.BLACK:
            # delete the black move and increment the number before starting the loop
            if (item := self.move_grid.itemAtPosition(row, 2)) is not None:
                if (widget := item.widget()) is not None:
                    widget.setParent(None)
            row = row + 1

        for t in range(row, self.move_grid.rowCount()):
            for i in range(0, 3):
                item = self.move_grid.itemAtPosition(t, i)
                if item is not None:
                    item.widget().setParent(None)