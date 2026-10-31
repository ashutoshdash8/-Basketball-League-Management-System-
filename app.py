"""
Basketball League Management System - Flask backend
All business rules (standings, validation, efficiency, grades) stay inside MySQL.
This file only calls your functions / procedures / triggers and returns JSON.
"""
import os
from datetime import date, datetime
from decimal import Decimal

import mysql.connector
from mysql.connector import Error
from flask import Flask, jsonify, request
from flask.json.provider import DefaultJSONProvider

# ---------------------------------------------------------------- config
DB = dict(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "basketball_db"),
)

# Column names taken from the report. If your script used different names,
# change them here only - nothing else in this file needs editing.
C = dict(
    player_name="player_name",   # players.player_name
    score1="team1_score",        # matches.team1_score
    score2="team2_score",        # matches.team2_score
    minutes="minutes",           # player_stats.minutes
)


class JSON(DefaultJSONProvider):
    @staticmethod
    def default(o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        return DefaultJSONProvider.default(o)


app = Flask(__name__, static_folder="static", static_url_path="")
app.json = JSON(app)


# ---------------------------------------------------------------- helpers
def connect():
    return mysql.connector.connect(**DB)


def query(sql, params=()):
    conn = connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()


def execute(sql, params=()):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def call(proc, args):
    """Call a stored procedure and return every row it SELECTs."""
    conn = connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.callproc(proc, args)
        rows = []
        for result in cur.stored_results():
            rows.extend(result.fetchall())
        conn.commit()
        return rows
    finally:
        conn.close()


def body():
    return request.get_json(silent=True) or {}


def need_int(data, key):
    try:
        return int(data[key])
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"'{key}' is required and must be a whole number")


def need_text(data, key):
    v = str(data.get(key, "")).strip()
    if not v:
        raise ValueError(f"'{key}' is required")
    return v


@app.errorhandler(Error)
def db_error(e):
    # SIGNAL messages (error 1644) arrive here, e.g. "A team cannot play itself"
    return jsonify(error=getattr(e, "msg", str(e))), 400


@app.errorhandler(ValueError)
def bad_input(e):
    return jsonify(error=str(e)), 400


# ---------------------------------------------------------------- read APIs
@app.get("/api/teams")
def teams():
    return jsonify(query("SELECT team_id, team_name, city, coach FROM teams ORDER BY team_name"))


@app.get("/api/standings")
def standings():
    return jsonify(query("""
        SELECT t.team_id, t.team_name, s.played, s.won, s.lost, s.points,
               get_team_wins(t.team_id) AS wins_check
        FROM standings s JOIN teams t ON t.team_id = s.team_id
        ORDER BY s.points DESC, s.won DESC, t.team_name"""))


@app.get("/api/players")
def players():
    return jsonify(query(f"""
        SELECT p.player_id, p.{C['player_name']} AS player_name, p.position, p.jersey_no,
               t.team_id, t.team_name
        FROM players p JOIN teams t ON t.team_id = p.team_id
        ORDER BY t.team_name, p.jersey_no"""))


@app.get("/api/player-report")
def player_report():
    # Same query as Fig 4.5 / Table 4.2: functions used inside a SELECT
    return jsonify(query(f"""
        SELECT p.{C['player_name']} AS player_name, t.team_name,
               SUM(ps.points) AS total_points,
               ROUND(AVG(calc_efficiency(ps.points, ps.rebounds, ps.assists, ps.steals)), 2) AS avg_efficiency,
               get_player_grade(AVG(calc_efficiency(ps.points, ps.rebounds, ps.assists, ps.steals))) AS grade
        FROM players p
        JOIN teams t ON t.team_id = p.team_id
        JOIN player_stats ps ON ps.player_id = p.player_id
        GROUP BY p.player_id, p.{C['player_name']}, t.team_name
        ORDER BY avg_efficiency DESC"""))


@app.get("/api/top-scorers")
def top_scorers():
    n = max(1, min(int(request.args.get("n", 3)), 50))
    return jsonify(call("top_scorers", [n]))


@app.get("/api/matches")
def matches():
    return jsonify(query(f"""
        SELECT m.match_id, m.match_date,
               t1.team_name AS team1, t2.team_name AS team2,
               m.{C['score1']} AS score1, m.{C['score2']} AS score2,
               w.team_name AS winner
        FROM matches m
        JOIN teams t1 ON t1.team_id = m.team1_id
        JOIN teams t2 ON t2.team_id = m.team2_id
        LEFT JOIN teams w ON w.team_id = m.winner_id
        ORDER BY m.match_date DESC, m.match_id DESC"""))


# ---------------------------------------------------------------- write APIs
@app.post("/api/teams")
def add_team():
    d = body()
    # trigger trg_team_standings creates the standings row automatically
    new_id = execute("INSERT INTO teams (team_name, city, coach) VALUES (%s, %s, %s)",
                     (need_text(d, "team_name"), need_text(d, "city"), need_text(d, "coach")))
    return jsonify(message="Team added", team_id=new_id), 201


@app.post("/api/players")
def add_player():
    d = body()
    rows = call("add_player", [need_text(d, "player_name"), need_int(d, "team_id"),
                               need_text(d, "position"), need_int(d, "jersey_no")])
    # add_player's exit handlers (1062 / 1452) SELECT a friendly message instead of raising
    msg = " ".join(str(v) for r in rows for v in r.values()) if rows else "Player added"
    if msg.lower().startswith("error"):
        return jsonify(error=msg), 400
    return jsonify(message=msg), 201


@app.post("/api/matches")
def record_match():
    d = body()
    # record_match validates, picks the winner and inserts; trigger updates standings
    call("record_match", [need_text(d, "match_date"), need_int(d, "team1_id"), need_int(d, "team2_id"),
                          need_int(d, "score1"), need_int(d, "score2")])
    return jsonify(message="Match recorded and standings updated"), 201


@app.post("/api/player-stats")
def add_stats():
    d = body()
    # trigger trg_validate_stats rejects negatives and minutes outside 0-60
    execute(f"""INSERT INTO player_stats (match_id, player_id, points, rebounds, assists, steals, {C['minutes']})
                VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (need_int(d, "match_id"), need_int(d, "player_id"), need_int(d, "points"),
             need_int(d, "rebounds"), need_int(d, "assists"), need_int(d, "steals"), need_int(d, "minutes")))
    return jsonify(message="Stats saved"), 201


@app.get("/")
def home():
    return app.send_static_file("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
