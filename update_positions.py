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
    SELECT raw_games.id, date, pgn, game_id
    FROM raw_games LEFT JOIN game_positions ON id = game_id)
  WHERE game_id is NULL;"""
)

positions = {}

total_moves = 0

write_cursor = con.cursor()

index = 0
for (game_id, date, raw_pgn) in cur:
    game = chess.pgn.read_game(io.StringIO(raw_pgn))
    ply = 0
    last_game_pos_id = None
    while game is not None:
        board = game.board()
        epd = board.epd()

        write_cursor.execute("INSERT OR IGNORE INTO positions (epd) VALUES (?)", (epd,))

        pos_id = write_cursor.execute(
            "SELECT pos_id FROM positions WHERE epd = ?", (epd,)
        ).fetchone()[0]

        next = game.next()
        next_move = None if next is None else board.san(next.move)
        write_cursor.execute(
            """
    INSERT INTO game_positions (pos_id, ply, game_id, last_game_pos_id, next_move)
    VALUES (?, ?, ?, ?, ?)
    """,
            (pos_id, ply, game_id, last_game_pos_id, next_move),
        )

        last_game_pos_id = write_cursor.lastrowid
        total_moves += 1
        ply += 1
        game = next
    print(f"{index} : {date} {total_moves}", end="\r")
    index = index + 1
con.commit()

print(f"{' ':80}", end="\r")
print(f"Imported positions from {total_moves} total moves")
