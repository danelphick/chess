from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QLabel, QWidget


class DatabasePane(QtWidgets.QScrollArea):
    MOVE_STYLE = """
    padding: 4px 4px 4px 2px;
    color: white;
    """

    def __init__(self):
        super().__init__()
        self.setMoves([])
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def setMoves(self, moves):
        self.widget = QWidget()
        self.setWidget(self.widget)
        self.move_grid = QtWidgets.QGridLayout()
        self.widget.setLayout(self.move_grid)

        self.move_grid.setSpacing(0)
        self.move_grid.setColumnStretch(3, 1)
        self.move_grid.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)

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

            win_percentage = round(move[0] / total_moves * 100)
            draw_percentage = round(move[1] / total_moves * 100)
            loss_percentage = round(move[2] / total_moves * 100)
            chances_label = QLabel(
                f"{win_percentage}%/{draw_percentage}%/{loss_percentage}%"
            )
            chances_label.setStyleSheet(DatabasePane.MOVE_STYLE)
            self.move_grid.addWidget(chances_label, row, 2)

        self.move_grid.setRowStretch(len(moves) + 1, 1)
        self.move_grid.setColumnStretch(3, 1)
