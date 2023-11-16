import io
import json
import os
import sqlite3

import chess
import chess.pgn
from config import config

board = chess.Board()

openings_dir = "/Users/dan/github/scraper/books/"

con = sqlite3.connect("/Users/dan/github/chess/openings.db")
cur = con.cursor()
cur.execute(
    """CREATE TABLE IF NOT EXISTS openings (
            opening_id INTEGER PRIMARY KEY,
            name TEXT,
            variation TEXT,
            link TEXT,
            type TEXT,
            book TEXT,
            chapter TEXT,
            paused INTEGER,
            learned INTEGER,
            UNIQUE(name, book, chapter, link)
            );
"""
)
cur.execute(
    """CREATE TABLE IF NOT EXISTS positions (
            pos_id INTEGER PRIMARY KEY,
            epd TEXT UNIQUE
            );
"""
)
cur.execute(
    """CREATE TABLE IF NOT EXISTS opening_positions (
            opening_pos_id INTEGER PRIMARY KEY,
            pos_id INTEGER,
            ply INTEGER,
            opening_id INTEGER,
            last_opening_pos_id INTEGER,
            next_move TEXT
            );
"""
)
con.commit()

def import_line(cur, variation, game, opening_id):
    ply = 0
    last_opening_pos_id = None
    while game is not None:
        board = game.board()
        epd = board.epd()

        cur.execute("INSERT OR IGNORE INTO positions (epd) VALUES (?)", (epd,))
        pos_id = cur.execute(
            "SELECT pos_id FROM positions WHERE epd = ?", (epd,)
        ).fetchone()[0]

        next = game.next()
        next_move = None if next is None else board.san(next.move)

        cur.execute(
            """
    INSERT INTO opening_positions (pos_id, ply, opening_id, last_opening_pos_id, next_move)
    VALUES (?, ?, ?, ?, ?)
            """,
            (pos_id, ply, opening_id, last_opening_pos_id, next_move),
        )
        last_opening_pos_id = cur.lastrowid

        # print(next_move)
        ply += 1
        game = next

# Get list of directories in the openings directory
main_scanner = os.scandir(openings_dir)
print("Files and Directories in '% s':" % openings_dir)
index = 0
lastrowid = cur.lastrowid
for book_entry in main_scanner:
    if book_entry.is_dir() or book_entry.is_file():
        book_dir = os.path.join(openings_dir, book_entry.name)
        dir_scanner = os.scandir(book_dir)
        for chapter_entry in dir_scanner:
            if chapter_entry.is_file():
                chapter_path = os.path.join(book_dir, chapter_entry.name)
                print(chapter_path)
                with open(chapter_path) as f:
                    data = json.load(f)
                    for variation in data:
                        if (
                            not variation["variation"]
                            or variation["type"] == "informational"
                        ):
                            continue
                        line = variation["variation"]
                        game = chess.pgn.read_game(io.StringIO(line))
                        if game.errors:
                            print(game.errors)
                        if game.is_end():
                            continue

                        # Insert each variation into the database
                        cur.execute(
                            """INSERT OR IGNORE INTO openings (
                                 name,
                                 variation,
                                 link,
                                 type,
                                 book,
                                 chapter,
                                 paused,
                                 learned)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (

                                variation["name"],
                                variation["variation"],
                                variation.get("link", ""),
                                variation["type"],
                                variation["book"],
                                variation["chapter"],
                                variation["paused"],
                                variation["learned"],
                            ),
                        )

                        if cur.lastrowid != lastrowid:
                            lastrowid = cur.lastrowid
                            index = index + 1
                            print(
                                f"{index}: {variation['book']} {variation['chapter']} {variation['name']} {variation.get('link')}"
                            )

                            import_line(cur, variation, game, lastrowid)


# print(f"{' ':80}", end="\r")
print(f"Parsed {index} lines")

con.commit()
