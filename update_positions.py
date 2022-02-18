import chess
import chess.pgn
import io
import sqlite3

board = chess.Board()

con = sqlite3.connect("/Users/dan/github/chess/games.db")
cur = con.cursor()

pgns = []
total_rows = cur.execute("SELECT COUNT(1) FROM raw_games;").fetchone()[0]

# cur.execute("SELECT id, date, pgn FROM raw_games ORDER BY date;")

cur.execute("""SELECT id, date, pgn FROM (
    SELECT raw_games.id, date, pgn, game_id
    FROM raw_games LEFT JOIN positions ON id = game_id)
  WHERE game_id is NULL;""")

positions = {}

total_moves = 0

# last_game_id = cur.execute("SELECT MAX(game_id) FROM positions").fetchone()[0];
# last_game_id = 0 if last_game_id is None else last_game_id

write_cursor = con.cursor()

index = 0
for (game_id, date, raw_pgn) in cur:
  game = chess.pgn.read_game(io.StringIO(raw_pgn))
  board = game.board()
  while not game.is_end():
    game = game.next()
    epd = game.board().epd()
    write_cursor.execute("""
    INSERT INTO positions (epd, game_id) VALUES (?, ?)
    """, (epd, game_id))
    total_moves += 1
  print(f"{index} : {date} {total_moves}",end='\r')
  index = index + 1
con.commit()

print(f"{' ':80}", end="\r")
print(f"Imported positions from {total_moves} total moves")