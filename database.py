import string
import chess
import chess.pgn
import io
import sqlite3
from pyparsing import White
from tabulate import tabulate
import functools


# Open a database from a given file name

# Query a position (by EPD) to find:
# a) number of games with win/draw/loss percentage
# b) successor moves


class ChessDatabase:
    con: sqlite3.Connection

    def __init__(self, database_file):
        self.con = sqlite3.connect(database_file)

    @functools.cache
    def lookupPosition(self, epd: string, user: string, color: chess.Color):
        cur = self.con.cursor()
        cur.execute(
            f"""
            SELECT SUM(result = '1-0'),
                   SUM(result = '1/2-1/2'),
                   SUM(result = '0-1'),
                   next_move, COUNT(1) AS count
            FROM positions p
            JOIN game_positions g
            ON p.pos_id = g.pos_id
            JOIN games
            ON games.game_id = g.game_id
            WHERE epd = ? AND {'white' if color == chess.WHITE else 'black'} = ?
            GROUP BY next_move
            ORDER BY count DESC
        """,
            (epd, user),
        )
        return list(cur)
