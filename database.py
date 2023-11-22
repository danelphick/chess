import abc
import aiosqlite
import asyncio

import chess
import chess.pgn

# Open a database from a given file name

# Query a position (by EPD) to find:
# a) number of games with win/draw/loss percentage
# b) successor moves


class ChessDatabase(object):
    __metaclass__ = abc.ABCMeta

    cache: dict[str, list[str]]
    file: str
    con: asyncio.Future

    def __init__(self, database_file=()):
        self.cache = {}
        self.file = database_file
        self.con = None

    async def conn(self):
        if self.con is None:
            self.con = asyncio.ensure_future(aiosqlite.connect(self.file))
        return await self.con

    @abc.abstractmethod
    async def findMultipleEpdsFromTable(self, cur, user: str, color: chess.Color):
        """Method called by findMultipleEpds which should find all the positions using the table
        temp_positions, which that method sets up."""
        pass

    async def findMultipleEpds(
        self, cur, epds: list[str], user: str, color: chess.Color
    ):
        """Given a list of EPDs, find all the lines that contain that position."""
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
        await self.findMultipleEpdsFromTable(cur, user, color)

    @abc.abstractmethod
    async def findSingleEpd(self, cur, epd: str, user: str, color: chess.Color):
        """Given a single EPD, find all the lines that contain that position."""
        pass

    async def populateCache(self, epds: list[str], user: str, color: chess.Color):
        future = asyncio.get_event_loop().create_future()
        for epd in epds:
            self.cache[(color, epd)] = future

        con = await self.conn()

        async with con.cursor() as cur:
            if len(epds) > 1:
                await self.findMultipleEpds(cur, epds, user, color)
            else:
                await self.findSingleEpd(cur, epds[0], user, color)

            results = {}
            async for (epd, next_move, count, user_plays_white, *extras) in cur:
                row = (next_move, count, user_plays_white, *extras)
                color_epd = (user_plays_white, epd)
                if color_epd not in results:
                    results[color_epd] = set()
                results[color_epd].add(row)

            for color_epd, row in results.items():
                self.cache[color_epd] = row

        for epd in epds:
            if self.cache[(color, epd)] == future:
                self.cache[(color, epd)] = []

        future.set_result(True)

    async def lookupPositions(self, epds: list[str], user: str, color: chess.Color):
        unknown_epds = [
            epd for epd in epds if type(self.cache.get((color, epd))) is not tuple
        ]
        really_unknown_epds = [
            epd for epd in unknown_epds if self.cache.get((color, epd)) is None
        ]

        if really_unknown_epds:
            await self.populateCache(really_unknown_epds, user, color)
        future_epds = [
            self.cache[(color, epd)]
            for epd in epds
            if (color, epd) in self.cache
            and isinstance(self.cache[(color, epd)], asyncio.Future)
        ]
        await asyncio.gather(*future_epds)
        return self.cache[(color, epds[0])]

    async def close(self):
        if self.con is not None:
            await (await self.conn()).close()


class GameDatabase(ChessDatabase):
    def __init__(self, database_file):
        super(GameDatabase, self).__init__(
            database_file=database_file,
        )

    async def findMultipleEpdsFromTable(self, cur, user: str, color: chess.Color):
        await cur.execute(
            f"""
            SELECT p.epd,
                next_move, COUNT(1) AS count,
                white = ?  AS user_plays_white,
                SUM(result = '1-0') AS win,
                SUM(result = '1/2-1/2') AS draw,
                SUM(result = '0-1') AS loss
            FROM positions p
            JOIN game_positions g
            ON p.pos_id = g.pos_id
            JOIN games
            ON games.game_id = g.game_id
            JOIN temp_positions
            ON p.epd = temp_positions.epd
            GROUP BY p.epd, next_move, user_plays_white
            ORDER BY count DESC
        """,
            (user,),
        )

    async def findSingleEpd(self, cur, epd: str, user: str, color: chess.Color):
        await cur.execute(
            f"""
            SELECT p.epd,
                next_move, COUNT(1) AS count,
                white = ? AS user_plays_white,
                SUM(result = '1-0') AS win,
                SUM(result = '1/2-1/2') AS draw,
                SUM(result = '0-1') AS loss
            FROM positions p
            JOIN game_positions g
            ON p.pos_id = g.pos_id
            JOIN games
            ON games.game_id = g.game_id
            AND p.epd = ?
            GROUP BY next_move, user_plays_white
            ORDER BY count DESC
        """,
            (user, epd),
        )


class OpeningDatabase(ChessDatabase):
    def __init__(self, database_file):
        super(OpeningDatabase, self).__init__(database_file=database_file)

    async def findMultipleEpds(
        self, cur, epds: list[str], user: str, color: chess.Color
    ):
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
                next_move, COUNT(1) AS count, openings.for_white AS user_plays_white
            FROM positions p
            JOIN opening_positions g
            ON p.pos_id = g.pos_id
            JOIN openings
            ON openings.opening_id = g.opening_id
            JOIN temp_positions
            ON p.epd = temp_positions.epd
            GROUP BY p.epd, next_move
            ORDER BY p.epd, count DESC
            """
        )

    async def findSingleEpd(self, cur, epd: str, user: str, color: chess.Color):
        await cur.execute(
            f"""
            SELECT p.epd,
                next_move, COUNT(1) AS count, o.for_white AS user_plays_white
            FROM positions p
            JOIN opening_positions g
            ON p.pos_id = g.pos_id
            JOIN openings
            ON openings.opening_id = g.opening_id
            JOIN openings o
            ON o.opening_id = g.opening_id
            WHERE p.epd = ? AND o.for_white = ?
            GROUP BY next_move
            ORDER BY p.epd, count DESC
            """,
            (epd, int(color == chess.WHITE)),
        )
