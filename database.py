import aiosqlite
import asyncio

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
    con: asyncio.Future

    def __init__(self, database_file):
        self.cache = {}
        self.file = database_file
        self.con = None

    async def conn(self):
        if self.con is None:
            self.con = asyncio.ensure_future(aiosqlite.connect(self.file))
        return await self.con

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
            [(epd,) for epd in epds],
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
        future = asyncio.get_event_loop().create_future()
        for epd in epds:
            self.cache[epd] = future

        con = await self.conn()

        async with con.cursor() as cur:
            if len(epds) > 1:
                await ChessDatabase.findMultipleEpds(cur, epds, user, color)
            else:
                await ChessDatabase.findSingleEpd(cur, epds[0], user, color)

            results = {}
            async for (epd, win, draw, loss, next_move, count) in cur:
                row = (win, draw, loss, next_move, count)
                if epd not in results:
                    results[epd] = set()
                results[epd].add(row)

            for (epd, row) in results.items():
                self.cache[epd] = row

        for epd in epds:
            if self.cache[epd] == future:
                self.cache[epd] = []

        future.set_result(True)

    async def lookupPositions(self, epds: list[str], user: str, color: chess.Color):
        unknown_epds = [epd for epd in epds if epd not in self.cache]
        if unknown_epds:
            await self.populateCache(unknown_epds, user, color)
        future_epds = [
            self.cache[epd]
            for epd in epds
            if epd in self.cache and isinstance(self.cache[epd], asyncio.Future)
        ]
        await asyncio.gather(*future_epds)

        return self.cache[epds[0]]

    async def close(self):
        if self.con is not None:
            await (await self.conn()).close()
