import chess
import chess.pgn
import io
import sqlite3

board = chess.Board()

con = sqlite3.connect("/Users/dan/github/chess/games.db")
cur = con.cursor()

pgns = []
total_rows = cur.execute("SELECT COUNT(1) FROM raw_games;").fetchone()[0]

cur.execute(
    """SELECT id, date, pgn FROM (
    SELECT raw_games.id, raw_games.date, raw_games.pgn, game_id
    FROM raw_games LEFT JOIN games ON id = game_id)
  WHERE game_id is NULL;"""
)

write_cursor = con.cursor()

index = 0
for (game_id, date, pgn) in cur:
    game = chess.pgn.read_game(io.StringIO(pgn))
    headers = game.headers

    write_cursor.execute(
        """
  INSERT INTO games (
    game_id, pgn, date, result, white, black, time_control,
    variant, white_elo, black_elo, eco, opening, termination)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  """,
        (
            game_id,
            pgn,
            date,
            headers.get("Result"),
            headers.get("White"),
            headers.get("Black"),
            headers.get("TimeControl"),
            headers.get("Variant"),
            headers.get("WhiteElo"),
            headers.get("BlackElo"),
            headers.get("ECO"),
            headers.get("Opening"),
            headers.get("Termination"),
        ),
    )
    print(f"{index}", end="\r")
    index = index + 1
con.commit()

print(f"{' ':80}", end="\r")
print(f"Imported {index} games")
