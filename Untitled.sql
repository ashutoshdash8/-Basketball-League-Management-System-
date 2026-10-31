CREATE DATABASE IF NOT EXISTS basketball_db;
USE basketball_db;

CREATE TABLE teams (
    team_id    INT PRIMARY KEY AUTO_INCREMENT,
    team_name  VARCHAR(50) NOT NULL UNIQUE,
    city       VARCHAR(50),
    coach      VARCHAR(50)
);

CREATE TABLE players (
    player_id    INT PRIMARY KEY AUTO_INCREMENT,
    player_name  VARCHAR(50) NOT NULL,
    team_id      INT NOT NULL,
    position     VARCHAR(20),
    jersey_no    INT,
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    UNIQUE (team_id, jersey_no)
);

CREATE TABLE matches (
    match_id     INT PRIMARY KEY AUTO_INCREMENT,
    match_date   DATE NOT NULL,
    team1_id     INT NOT NULL,
    team2_id     INT NOT NULL,
    team1_score  INT NOT NULL,
    team2_score  INT NOT NULL,
    winner_id    INT NOT NULL,
    FOREIGN KEY (team1_id)  REFERENCES teams(team_id),
    FOREIGN KEY (team2_id)  REFERENCES teams(team_id),
    FOREIGN KEY (winner_id) REFERENCES teams(team_id)
);

CREATE TABLE player_stats (
    stat_id    INT PRIMARY KEY AUTO_INCREMENT,
    match_id   INT NOT NULL,
    player_id  INT NOT NULL,
    points     INT DEFAULT 0,
    rebounds   INT DEFAULT 0,
    assists    INT DEFAULT 0,
    steals     INT DEFAULT 0,
    minutes    INT DEFAULT 0,
    FOREIGN KEY (match_id)  REFERENCES matches(match_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);

CREATE TABLE standings (
    team_id  INT PRIMARY KEY,
    played   INT DEFAULT 0,
    won      INT DEFAULT 0,
    lost     INT DEFAULT 0,
    points   INT DEFAULT 0,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);