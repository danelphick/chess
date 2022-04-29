import sqlite3
import aiosqlite

from tabulate import tabulate

import chess
import chess.pgn

# Open a database from a given file name

# Query a position (by EPD) to find:
# a) number of games with win/draw/loss percentage
# b) successor moves


class ChessDatabase:
    con: sqlite3.Connection
    cache: dict[str, list[str]]

    def __init__(self, database_file):
        self.con = sqlite3.connect(database_file)
        self.cache = {}

    def lookupPosition(self, epd: str, user: str, color: chess.Color):
        if epd in self.cache:
            return self.cache[epd]

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

        self.cache[epd] = list(cur)
        return self.cache[epd]

    def lookupPositions(self, epds: list[str], user: str, color: chess.Color):
        cur = self.con.cursor()
        cur.executescript(
            """
            CREATE TEMPORARY TABLE IF NOT EXISTS temp_positions (epd STRING);
            DELETE FROM temp_positions;
            """
        )
        cur.executemany(
            """
            INSERT INTO temp_positions VALUES (?);
            """,
            [(epd,) for epd in epds]
        )
        cur.execute(
            f"""
            SELECT p.epd,
                   SUM(result = '1-0'),
                   SUM(result = '1/2-1/2'),
                   SUM(result = '0-1'),
                   next_move, COUNT(1) AS count
            FROM positions p
            JOIN game_positions g
            ON p.pos_id = g.pos_id
            JOIN games
            ON games.game_id = g.game_id
            JOIN temp_positions
            ON p.epd = temp_positions.epd
            WHERE {'white' if color == chess.WHITE else 'black'} = ?
            GROUP BY next_move
            ORDER BY p.epd, count DESC
        """,
            (user,),
        )
        for (epd, win, draw, loss, next_move, count) in cur:
            if epd in self.cache:
                self.cache[epd].append((win, draw, loss, next_move, count))
            else:
                self.cache[epd] = [(win, draw, loss, next_move, count)]
        for epd in epds:
            if epd not in self.cache:
                self.cache[epd] = []
        return self.cache[epds[0]]
