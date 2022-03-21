import berserk
import chess
import chess.pgn
from datetime import datetime
import io
import sqlite3
import yaml

board = chess.Board()

with open('config.yaml', 'r') as file:
   config = yaml.safe_load(file)

session = berserk.TokenSession(config['lichess']['api_token'])
username = config['lichess']['username']
client = berserk.Client(session=session)

con = sqlite3.connect("/Users/dan/github/chess/games.db")
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS raw_games (date TEXT, pgn TEXT);")
con.commit()

last_date = None
last_timestamp = None
if cur.execute("SELECT COUNT(1) FROM raw_games;").fetchone()[0] > 0:
    last_date = cur.execute(
        "SELECT date FROM raw_games ORDER BY date DESC LIMIT 1"
    ).fetchone()[0]

if last_date is not None:
    last_iso_date = datetime.fromisoformat(last_date)
    last_timestamp = int(berserk.utils.to_millis(last_iso_date))

print(f"Getting all games since last one at {last_iso_date}")

games = client.games.export_by_player(
    username,
    as_pgn=True,
    evals=True,
    opening=True,
    since=last_timestamp + 1000,
)

index = 1
for game in games:
    headers = chess.pgn.read_game(io.StringIO(game)).headers
    date = headers["UTCDate"].replace(".", "-") + " " + headers["UTCTime"]
    print(f"Getting game {index} {date}", end="\r")
    cur.execute("INSERT INTO raw_games (date, pgn) VALUES (?, ?)", (date, game))
    index = index + 1

print(f"{' ':80}", end="\r")
print(f"Got {index - 1} games")

con.commit()
