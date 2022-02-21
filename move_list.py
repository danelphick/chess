from PySide6.QtWidgets import QWidget, QLabel
from PySide6 import QtWidgets


class MoveList(QtWidgets.QScrollArea):
    MOVE_STYLE = """
    padding: 4px 4px 4px 2px;
    color: white;
    """

    CURRENT_MOVE_STYLE = MOVE_STYLE + """
    background: lightgray;
    color: black;
    """

    def __init__(self):
        super().__init__()
        self.widget = QWidget()
        self.setWidget(self.widget)

        self.move_grid = QtWidgets.QGridLayout()
        self.move_grid.setSpacing(0)
        self.move_grid.setColumnStretch(3, 1)
        self.move_grid.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.widget.setLayout(self.move_grid)

    def setMoves(self, moves):
        moves = iter(moves)
        row = 0
        try:
            while True:
                white_move_label = QLabel(next(moves).san())
                white_move_label.setStyleSheet(MoveList.MOVE_STYLE)
                row = row + 1
                number_label = QLabel(str(row))
                number_label.setStyleSheet(MoveList.MOVE_STYLE)
                self.move_grid.addWidget(number_label, row, 0)
                self.move_grid.addWidget(white_move_label, row, 1)
                black_move_label = QLabel(next(moves).san())
                self.move_grid.addWidget(black_move_label, row, 2)
                black_move_label.setStyleSheet(MoveList.MOVE_STYLE)
        except StopIteration:
            pass
        self.move_grid.setRowStretch(row + 1, 1)
        self.move_grid.setColumnStretch(3, 1)

    def styleMove(self, turnAndNumber, style):
        if turnAndNumber is not None:
            turn, number = turnAndNumber
            item = self.move_grid.itemAtPosition(number, 2 - int(turn))
            if item is not None:
                item.widget().setStyleSheet(style)

    def setCurrentMove(self, new, old):
        if old != new:
            self.styleMove(old, MoveList.MOVE_STYLE)

        self.styleMove(new, MoveList.CURRENT_MOVE_STYLE)
