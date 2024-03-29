import asyncio
import chess.engine

from PySide6.QtWidgets import QLabel, QPushButton

import chess
from config import config
from chess_board import ChessBoard
from database import GameDatabase, OpeningDatabase
from database_pane import DatabasePane
from eval_bar import EvalBar
from game import Game
from move_list import MoveList
from openings_pane import OpeningsPane


class Controller:
    game: Game
    chess_board: ChessBoard
    move_list: MoveList
    game_database: GameDatabase
    game_database_pane: DatabasePane
    opening_database: OpeningDatabase
    opening_database_pane: DatabasePane
    currentTurnAndNumber: tuple[chess.Color, int]
    engine: chess.engine.SimpleEngine
    backgroundTasks: set[asyncio.Task]
    userColor: chess.Color

    def __init__(
        self,
        game: Game,
        chess_board: ChessBoard,
        eval_bar: EvalBar,
        move_list: MoveList,
        game_database_pane: DatabasePane,
        opening_database_pane: OpeningsPane,
        first: QPushButton,
        previous: QPushButton,
        next: QPushButton,
        last: QPushButton,
        rotate: QPushButton,
        analysis_widget: QLabel,
    ):
        self.game = game
        self.chess_board = chess_board
        self.eval_bar = eval_bar
        self.move_list = move_list
        self.game_database_pane = game_database_pane
        self.opening_database_pane = opening_database_pane
        self.first = first
        self.previous = previous
        self.next = next
        self.last = last
        self.rotate = rotate
        self.analysis_widget = analysis_widget
        self.currentTurnAndNumber = (chess.WHITE, 0)
        self.backgroundTasks = set()
        self.engine = None
        self.examineTasks = []
        self.userColor = chess.WHITE

        self.game_database = GameDatabase(
            database_file="games.db", username=config()["lichess"]["username"]
        )
        self.opening_database = OpeningDatabase(database_file="openings.db")
        self.first.clicked.connect(self.firstMove)
        self.previous.clicked.connect(self.previousMove)
        self.next.clicked.connect(self.nextMove)
        self.last.clicked.connect(self.lastMove)
        self.rotate.clicked.connect(self.rotateBoard)

        self.move_list.setMoves(self, game.getMoves())
        b = game.board.copy()
        positions = [b.epd()]
        for m in game.getMoves():
            b.push_uci(m.uci())
            positions.append(b.epd())

        self.scheduleLookupPositions(positions=positions)

        asyncio.create_task(self.startEngine())

        self.updateMoveListPosition()
        self.chess_board.setupBoard(game.board)
        self.chess_board.moveHandler = self

    async def startEngine(self):
        self.transport, self.engine = await chess.engine.popen_uci("stockfish")

    async def lookupGamePositions(self, positions, color):
        self.game_database_pane.setMovesLoading()
        moves = await self.game_database.lookupPositions(positions, color)
        filtered_moves = [
            move for move in moves if move[2] == (self.userColor == chess.WHITE)
        ]
        self.game_database_pane.setMoves(filtered_moves, self)

    async def lookupOpeningPositions(self, positions, color, ply, *, lookupAllBookMoves=False):
        self.opening_database_pane.setMovesLoading()
        if lookupAllBookMoves:
            first_position = positions[0]
            positions = []
            current_node = self.game.game.root()
            while next_node := current_node.next():
                positions.append(current_node.board().epd())
                current_node = next_node
            else:
                positions.append(current_node.board().epd())
            ply = 0
            await self.opening_database.lookupPositions(positions, color)
            moves = await self.opening_database.lookupPositions([first_position], color)
        else:
            moves = await self.opening_database.lookupPositions(positions, color)

        self.opening_database_pane.setMoves(moves, self)

        if ply == 0:
            # Cut off the first position since it's the starting position.
            positions = positions[1:]
            self.move_list.setBookMoves(
                0, self.opening_database.getBookMoves(positions, color)
            )
        else:
            self.move_list.setBookMoves(
                ply - 1, self.opening_database.getBookMoves(positions, color)
            )

    async def getEngine(self):
        if self.engine:
            return self.engine

        await self.startEngine()
        return self.engine

    async def examinePosition(self, board: chess.Board):
        try:
            engine = await self.getEngine()

            if asyncio.current_task() != self.examineTasks[-1]:
                return

            if len(self.examineTasks) > 1:
                for i in range(0, len(self.examineTasks) - 1):
                    task: asyncio.Task = self.examineTasks[i]
                    if not task.cancelled():
                        task.cancel()
                        await task

            del self.examineTasks[0:-1]

            # A new task could have been scheduled while we were waiting on cancelling the other
            # tasks.
            if asyncio.current_task() != self.examineTasks[-1]:
                return

            with await engine.analysis(board, chess.engine.Limit(depth=25)) as analysis:
                async for info in analysis:
                    score = info.get("score")
                    if score is not None:
                        score = score
                        if score.is_mate():
                            mate = score.white().mate()
                            if mate == 0:
                                score_text = "Checkmate"
                            elif mate > 0:
                                score_text = f"M+{mate}"
                            else:
                                score_text = f"M-{-mate}"
                        else:
                            score_text = "{:.2f}".format(
                                score.pov(chess.WHITE).score() / 100.0
                            )

                        depth = info.get("depth")

                        if board.is_game_over():
                            self.analysis_widget.setText(board.result(claim_draw=True))
                        else:
                            move = board.variation_san(info.get("pv"))
                            self.analysis_widget.setText(
                                f"{score_text} depth: {depth} {move}\n"
                            )
                        self.eval_bar.updateBar(score)

                    # Arbitrary stop condition.
                    if info.get("depth", 0) > 30:
                        break

            self.examineTasks.remove(asyncio.current_task())
        except asyncio.CancelledError:
            pass

    def scheduleTask(self, coro):
        task = asyncio.create_task(coro)
        self.backgroundTasks.add(task)
        task.add_done_callback(self.taskDone)
        return task

    def taskDone(self, task):
        if task.exception():
            raise task.exception()
        self.backgroundTasks.discard(task)

    def scheduleLookupPositions(self, positions=None, *, lookupAllBookMoves=False):
        if positions is None:
            positions = [self.game.board.epd()]
        self.scheduleTask(self.lookupGamePositions(positions, self.userColor))
        self.scheduleTask(
            self.lookupOpeningPositions(
                positions,
                self.userColor,
                self.game.ply,
                lookupAllBookMoves=lookupAllBookMoves
            )
        )

    def updateMoveListPosition(self):
        new = self.game.getTurnAndNumber()
        self.move_list.setCurrentMove(new, self.currentTurnAndNumber)
        self.currentTurnAndNumber = new

        self.scheduleLookupPositions()
        self.examineTasks.append(
            self.scheduleTask(self.examinePosition(self.game.board.copy()))
        )

    def updateBoard(self):
        self.chess_board.clearClicks()
        self.chess_board.setLastMove(
            self.game.getPreviousMove(), checkSquare=self.game.getKingCheckSquare()
        )
        self.chess_board.drawBoard()

    def makeMove(self, instant=False):
        """Carry out the next move in the game."""
        (fromPos, toPos) = self.game.getFromSquare(), self.game.getToSquare()
        captureSquare = self.game.getCapturedSquare()

        if captureSquare is not None:
            self.chess_board.capturePiece(captureSquare)
        self.chess_board.movePiece(
            fromPos, toPos, promoteTo=self.game.getPromotionPiece()
        )

        castlingRookMove = self.game.getCastlingRookMove()
        if castlingRookMove is not None:
            self.chess_board.movePiece(castlingRookMove[0], castlingRookMove[1])

        self.chess_board.startAnimation()

        self.game.advance()

        self.updateBoard()

        if instant:
            self.chess_board.cancelAnimation()

    def firstMove(self):
        self.chess_board.cancelAnimation()

        self.game.goToStart()
        self.chess_board.setupBoard(self.game.board)
        self.updateMoveListPosition()
        self.updateBoard()

    def lastMove(self):
        self.chess_board.cancelAnimation()

        self.game.goToEnd()
        self.chess_board.setupBoard(self.game.board)
        self.updateMoveListPosition()
        self.updateBoard()

    def nextMove(self):
        self.chess_board.cancelAnimation()

        if not self.game.hasMoreMoves():
            return

        self.makeMove()

        self.updateMoveListPosition()

    def previousMove(self):
        self.chess_board.cancelAnimation()

        if not self.game.goBack():
            return

        (fromPos, toPos) = self.game.getFromSquare(), self.game.getToSquare()

        self.updateBoard()

        if self.game.getPromotionPiece() is not None:
            self.chess_board.changePiece(toPos, chess.PAWN)

        captureSquare = self.game.getCapturedSquare()

        self.chess_board.movePiece(fromPos, toPos, reverse=True)
        if captureSquare is not None:
            self.chess_board.addPiece(
                captureSquare, self.game.board.piece_at(captureSquare), fadeIn=True
            )

        castlingRookMove = self.game.getCastlingRookMove()
        if castlingRookMove is not None:
            self.chess_board.movePiece(
                castlingRookMove[0], castlingRookMove[1], reverse=True
            )

        self.chess_board.startAnimation()

        self.updateMoveListPosition()

    def move(self, move: chess.Move, instant=False):
        if self.game.board.is_legal(move):
            old = self.currentTurnAndNumber
            self.game.replaceNextMove(move)
            move_text = self.game.game.next().san()
            self.makeMove(instant=instant)
            self.currentTurnAndNumber = self.game.getTurnAndNumber()
            self.move_list.removeMoves(self.currentTurnAndNumber)
            self.move_list.addMove(self.currentTurnAndNumber, move_text)
            self.move_list.setCurrentMove(self.currentTurnAndNumber, old)
            self.updateMoveListPosition()
            return True
        else:
            return False

    def moveFromSan(self, san):
        self.chess_board.cancelAnimation()
        self.chess_board.clearClicks()

        return self.move(self.game.board.parse_san(san))

    def getValidMoves(self, fromPos: chess.Square):
        return self.game.getValidMoves(fromPos)

    def whoseTurn(self) -> chess.Color:
        return self.game.board.turn

    async def stop(self):
        self.stopped = True
        await self.game_database.close()
        await self.opening_database.close()

    def selectMove(self, turn, number):
        self.chess_board.cancelAnimation()

        self.game.goToStart()
        self.game.advance(number * 2 - 1)
        if turn == chess.BLACK:
            self.game.advance()

        self.chess_board.setupBoard(self.game.board)
        self.updateMoveListPosition()
        self.updateBoard()

    def rotateBoard(self):
        self.userColor = chess.WHITE if self.userColor == chess.BLACK else chess.BLACK
        self.chess_board.rotate(self.userColor)
        self.scheduleLookupPositions(lookupAllBookMoves=True)
