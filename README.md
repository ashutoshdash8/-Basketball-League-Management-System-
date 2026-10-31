# Basketball League Management System – Web App

Backend: Flask (Python) · Database: your existing MySQL `basketball_db` · Frontend: HTML/CSS/JS (served by Flask)

## Run
1. In MySQL Workbench run `basketball_project.sql` once so the database, functions, procedures and triggers exist.
2. In this folder:
   ```
   pip install -r requirements.txt
   set DB_PASSWORD=your_mysql_password        (Windows CMD)
   $env:DB_PASSWORD="your_mysql_password"     (PowerShell)
   python app.py
   ```
3. Open http://127.0.0.1:5000

Optional env vars: DB_HOST, DB_PORT, DB_USER, DB_NAME.

## If you get "Unknown column ..."
Open the `C = dict(...)` block at the top of `app.py` and set it to your real column names
(`DESCRIBE matches; DESCRIBE player_stats; DESCRIBE players;` shows them).
Also check the argument order of `calc_efficiency` in `/api/player-report` (assumed: points, rebounds, assists, steals).

## API
GET /api/standings · /api/player-report · /api/top-scorers?n=3 · /api/matches · /api/players · /api/teams
POST /api/matches · /api/players · /api/player-stats · /api/teams
