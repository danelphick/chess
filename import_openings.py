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
    """CREATE TABLE IF NOT EXISTS raw_openings (
            id INTEGER PRIMARY KEY,
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
con.commit()


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
                            """INSERT OR IGNORE INTO raw_openings (
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


# print(f"{' ':80}", end="\r")
print(f"Parsed {index} lines")

con.commit()
