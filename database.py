import aiosqlite

from tabulate import tabulate

import chess
import chess.pgn

# Open a database from a given file name

# Query a position (by EPD) to find:
# a) number of games with win/draw/loss percentage
# b) successor moves


class ChessDatabase:
    cache: dict[str, list[str]]
    file: str
    con: aiosqlite.Connection

    def __init__(self, database_file):
        self.cache = {}
        self.file = database_file
        self.con = None

    async def conn(self):
        if self.con is None:
            self.con = await(aiosqlite.connect(self.file))
        return self.con

    async def findMultipleEpds(cur, epds: list[str], user: str, color: chess.Color):
        await cur.executescript(
            """
            CREATE TEMPORARY TABLE IF NOT EXISTS temp_positions (epd STRING);
            DELETE FROM temp_positions;
            """
        )
        await cur.executemany(
            """
            INSERT INTO temp_positions VALUES (?);
            """,
            [(epd,) for epd in epds]
        )
        await cur.execute(
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

    async def findSingleEpd(cur, epd: str, user: str, color: chess.Color):

        await cur.execute(
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
            WHERE {'white' if color == chess.WHITE else 'black'} = ?
            AND p.epd = ?
            GROUP BY next_move
            ORDER BY p.epd, count DESC
        """,
            (user, epd),
        )

    async def populateCache(self, epds: list[str], user: str, color: chess.Color):
        con = await self.conn()
        async with con.cursor() as cur:
            if len(epds) > 1:
                await ChessDatabase.findMultipleEpds(cur, epds, user, color)
            else:
                await ChessDatabase.findSingleEpd(cur, epds[0], user, color)

            async for (epd, win, draw, loss, next_move, count) in cur:
                if epd in self.cache:
                    self.cache[epd].append((win, draw, loss, next_move, count))
                else:
                    self.cache[epd] = [(win, draw, loss, next_move, count)]

    async def lookupPositions(self, epds: list[str], user: str, color: chess.Color):
        unknown_epds = [epds for epd in epds if epd not in self.cache]
        if unknown_epds:
            await self.populateCache(epds, user, color)

        for epd in epds:
            if epd not in self.cache:
                self.cache[epd] = []
        return self.cache[epds[0]]
