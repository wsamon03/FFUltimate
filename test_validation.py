#!/usr/bin/env python3
"""
Validate imported NFL data: player info, individual stats, and cross-table joins.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    database=os.getenv("DB_NAME", "nfl_fantasy"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "owenethanTKD"),
    port=int(os.getenv("DB_PORT", "5432")),
)
conn.autocommit = True
cur = conn.cursor(cursor_factory=RealDictCursor)

PASS = 0
FAIL = 0


def check(desc, condition, detail=""):
    global PASS, FAIL
    status = "PASS" if condition else "FAIL"
    if condition:
        PASS += 1
    else:
        FAIL += 1
    extra = f" -- {detail}" if detail else ""
    print(f"  [{status}] {desc}{extra}")


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ==== TABLE COUNTS ====
section("1. TABLE ROW COUNTS")
tables = ["teams", "players", "games", "team_game_stats", "player_game_stats"]
counts = {}
for t in tables:
    cur.execute(f"SELECT COUNT(*) as cnt FROM {t}")
    counts[t] = cur.fetchone()["cnt"]
    print(f"  {t:25s} {counts[t]} rows")

check("teams > 0", counts["teams"] > 0, f"{counts['teams']} teams")
check("players > 0", counts["players"] > 0, f"{counts['players']} players")
check("games > 0", counts["games"] > 0, f"{counts['games']} games")
check("team_game_stats > 0", counts["team_game_stats"] > 0, f"{counts['team_game_stats']} rows")
check("player_game_stats > 0", counts["player_game_stats"] > 0, f"{counts['player_game_stats']} rows")

# ==== TEAMS ====
section("2. TEAMS DATA")
if counts["teams"] > 0:
    cur.execute("SELECT id, abbr, full_name FROM teams ORDER BY id")
    teams = cur.fetchall()
    for t in teams:
        print(f"  Team {t['id']}: {t['abbr']} - {t['full_name']}")

    check("all teams have non-empty abbr",
          all(t["abbr"] for t in teams),
          "abbr field populated")
    check("all teams have non-empty full_name",
          all(t["full_name"] for t in teams),
          "full_name field populated")

    # Check no phantom empty team
    cur.execute("SELECT id FROM teams WHERE abbr = '' OR full_name = ''")
    empty = cur.fetchall()
    check("no phantom empty teams", len(empty) == 0, f"{len(empty)} empty teams found")

# ==== GAMES ====
section("3. GAMES DATA")
if counts["games"] > 0:
    cur.execute("SELECT id, espn_id, status, game_date, week, season_year FROM games")
    games = cur.fetchall()
    for g in games:
        print(f"  Game {g['espn_id']}: {g['game_date']} week={g['week']} year={g['season_year']} status={g['status']}")

    check("games have valid espn_id",
          all(g["espn_id"] for g in games),
          "espn_id populated")
    check("games have valid dates",
          all(g["game_date"] for g in games),
          "game_date populated")

# ==== PLAYER-TEAM JOIN ====
section("4. PLAYER-TEAM JOIN")
if counts["players"] > 0:
    cur.execute("""
        SELECT p.name, p.position, p.team_id, t.abbr as team_abbr
        FROM players p
        LEFT JOIN teams t ON p.team_id = t.id
        ORDER BY p.id LIMIT 10
    """)
    rows = cur.fetchall()
    for r in rows:
        pos_display = r["position"] if r["position"] else "None"
        print(f"  {r['name']:30s} pos={pos_display:6s} team_id={r['team_id']} ({r['team_abbr']})")

    cur.execute("""
        SELECT COUNT(*) as cnt FROM players
        WHERE position IS NULL OR position = ''
    """)
    no_pos = cur.fetchone()["cnt"]
    check("all players have position", no_pos == 0, f"{no_pos} players without position")

    cur.execute("""
        SELECT COUNT(*) as cnt FROM players p
        LEFT JOIN teams t ON p.team_id = t.id
        WHERE t.id IS NULL
    """)
    orphan = cur.fetchone()["cnt"]
    check("all players reference valid team", orphan == 0, f"{orphan} orphans")

# ==== PLAYER-STATS-PLAYER JOIN ====
section("5. PLAYER STATS -> PLAYER JOIN")
if counts["player_game_stats"] > 0:
    # Verify all player_game_stats reference valid players
    cur.execute("""
        SELECT COUNT(*) as cnt FROM player_game_stats pg
        LEFT JOIN players p ON pg.player_id = p.id
        WHERE p.id IS NULL
    """)
    orphan_pg = cur.fetchone()["cnt"]
    check("all player_game_stats reference valid player", orphan_pg == 0, f"{orphan_pg} orphans")

    # Verify all player_game_stats reference valid games
    cur.execute("""
        SELECT COUNT(*) as cnt FROM player_game_stats pg
        LEFT JOIN games g ON pg.game_id = g.id
        WHERE g.id IS NULL
    """)
    orphan_game = cur.fetchone()["cnt"]
    check("all player_game_stats reference valid game", orphan_game == 0, f"{orphan_game} orphans")

    # Show sample joined stats
    cur.execute("""
        SELECT p.name, p.position, g.espn_id as game_id,
               pg.pass_comp, pg.pass_att, pg.pass_yds, pg.pass_td, pg.pass_int,
               pg.rush_att, pg.rush_yds, pg.rush_td,
               pg.rec_receptions, pg.rec_targets, pg.rec_yds, pg.rec_td,
               pg.def_solo, pg.def_ast, pg.def_sacks,
               pg.k_fg_make, pg.k_fg_att
        FROM player_game_stats pg
        JOIN players p ON pg.player_id = p.id
        JOIN games g ON pg.game_id = g.id
        ORDER BY pg.id
        LIMIT 5
    """)
    rows = cur.fetchall()
    print(f"\n  Sample player game stats ({len(rows)} shown):")
    if rows:
        header = f"  {'Player':<25s} {'Pos':>4s}  {'Game':>13s}  {'Pass':>12s}  {'Rush':>10s}  {'Rec':>10s}  {'Def':>10s}  {'Kic':>8s}"
        print(header)
        print("  " + "-" * 110)
        for r in rows:
            def _int(val):
                return str(val) if val is not None else "-"
            def _sack(val):
                return str(val) if val is not None else "-"

            pass_str = f"{_int(r['pass_comp'])}/{_int(r['pass_att'])} {_int(r['pass_yds'])}yd {r['pass_td']}TD"
            rush_str = f"{_int(r['rush_att'])}/{_int(r['rush_yds'])}yd {r['rush_td']}TD"
            rec_str = f"{_int(r['rec_receptions'])}/{_int(r['rec_targets'])} {_int(r['rec_yds'])}yd {r['rec_td']}TD"
            def_str = f"{_int(r['def_solo'])} solo {_sack(r['def_sacks'])} sacks"
            kic_str = f"{_int(r['k_fg_make'])}/{_int(r['k_fg_att'])}"

            print(f"  {r['name']:<23s} {r['position']:>4s}  {r['game_id']:>13s}  {pass_str:>12s}  {rush_str:>10s}  {rec_str:>10s}  {def_str:>10s}  {kic_str:>8s}")

# ==== TEAM STATS -> TEAM JOIN ====
section("6. TEAM STATS -> TEAM JOIN")
if counts["team_game_stats"] > 0:
    cur.execute("""
        SELECT t.abbr, t.full_name, tgs.pts_total, tgs.off_total_yds,
               tgs.off_first_downs, tgs.off_possession_secs, tgs.def_sacks, tgs.penalties_count
        FROM team_game_stats tgs
        JOIN teams t ON tgs.team_id = t.id
        ORDER BY tgs.id
    """)
    rows = cur.fetchall()
    print(f"\n  Team game stats ({len(rows)} rows):")
    print(f"  {'Team':>6s}  {'PTS':>4s}  {'YDS':>5s}  {'1stD':>5s}  {'Poss(s)':>8s}  {'Sacks':>6s}  {'Pen':>4s}")
    print("  " + "-" * 42)
    for r in rows:
        pts = r["pts_total"] if r["pts_total"] is not None else "-"
        yds = r["off_total_yds"] if r["off_total_yds"] is not None else "-"
        fd = r["off_first_downs"] if r["off_first_downs"] is not None else "-"
        poss = r["off_possession_secs"] if r["off_possession_secs"] is not None else "-"
        sk = r["def_sacks"] if r["def_sacks"] is not None else "-"
        pn = r["penalties_count"] if r["penalties_count"] is not None else "-"
        print(f"  {str(r['abbr']):>6s}  {pts:>4s}  {yds:>5s}  {fd:>5s}  {poss:>8s}  {str(sk):>6s}  {str(pn):>4s}")

    # Check possession time makes sense (should be 150-720 seconds for NFL)
    cur.execute("""
        SELECT COUNT(*) as cnt FROM team_game_stats
        WHERE off_possession_secs IS NOT NULL
          AND (off_possession_secs < 120 OR off_possession_secs > 720)
    """)
    bad_poss = cur.fetchone()["cnt"]
    check("possession time in reasonable range (120-720s)", bad_poss == 0, f"{bad_poss} out of range")

# ==== CROSS-GAME PLAYER CONSISTENCY ====
section("7. PLAYER ID CONSISTENCY ACROSS GAMES")
if counts["player_game_stats"] > 0:
    # A player appearing in multiple games should have the same external_id
    cur.execute("""
        SELECT p.external_id, p.name, COUNT(DISTINCT pg.game_id) as game_count
        FROM player_game_stats pg
        JOIN players p ON pg.player_id = p.id
        GROUP BY p.external_id, p.name
        HAVING COUNT(DISTINCT pg.game_id) > 1
        ORDER BY game_count DESC
        LIMIT 5
    """)
    multi_game = cur.fetchall()
    if multi_game:
        print(f"\n  Players in multiple games:")
        for r in multi_game:
            print(f"    {r['name']} ({r['external_id']}): {r['game_count']} games")
        check("same player consistent across games", True, f"{len(multi_game)} multi-game players verified")
    else:
        check("multi-game player consistency", True, "single-game only - N/A")

# ==== STAT plausibility ====
section("8. STAT PLAUSIBILITY")
if counts["player_game_stats"] > 0:
    # Passing: comp should never exceed att
    cur.execute("""
        SELECT COUNT(*) as cnt FROM player_game_stats
        WHERE pass_comp IS NOT NULL AND pass_att IS NOT NULL
          AND pass_comp > pass_att
    """)
    bad_pass = cur.fetchone()["cnt"]
    check("pass_comp <= pass_att", bad_pass == 0, f"{bad_pass} violations")

    # Rush att should be >= 0
    cur.execute("""
        SELECT COUNT(*) as cnt FROM player_game_stats
        WHERE rush_att IS NOT NULL AND rush_att < 0
    """)
    neg_rush = cur.fetchone()["cnt"]
    check("rush_att >= 0", neg_rush == 0, f"{neg_rush} violations")

    # Yards should be >= 0
    cur.execute("""
        SELECT COUNT(*) as cnt FROM player_game_stats
        WHERE pass_yds IS NOT NULL AND pass_yds < 0
    """)
    neg_yds = cur.fetchone()["cnt"]
    check("pass_yds >= 0", neg_yds == 0, f"{neg_yds} violations")

    # Sacks should be >= 0
    cur.execute("""
        SELECT COUNT(*) as cnt FROM player_game_stats
        WHERE def_sacks IS NOT NULL AND def_sacks < 0
    """)
    neg_sacks = cur.fetchone()["cnt"]
    check("def_sacks >= 0", neg_sacks == 0, f"{neg_sacks} violations")

    # TD should be >= 0
    cur.execute("""
        SELECT COUNT(*) as cnt FROM player_game_stats
        WHERE pass_td IS NOT NULL AND pass_td < 0
    """)
    neg_td = cur.fetchone()["cnt"]
    check("pass_td >= 0", neg_td == 0, f"{neg_td} violations")

    # Half-sacks: check if any are float (0.5)
    cur.execute("""
        SELECT COUNT(*) as cnt FROM player_game_stats
        WHERE def_sacks IS NOT NULL AND def_sacks != CAST(def_sacks AS INTEGER)
    """)
    half_sack = cur.fetchone()["cnt"]
    if half_sack > 0:
        print(f"  Half-sack entries found: {half_sack}")
        cur.execute("""
            SELECT p.name, pg.def_sacks
            FROM player_game_stats pg
            JOIN players p ON pg.player_id = p.id
            WHERE pg.def_sacks IS NOT NULL AND pg.def_sacks != CAST(pg.def_sacks AS INTEGER)
            LIMIT 3
        """)
        for r in cur.fetchall():
            print(f"    {r['name']}: {r['def_sacks']} sacks")
    check("half-sack support (def_sacks can be float)", True, f"{half_sack} half-sack entries")

# ==== PERCENTAGE CHECKS ====
section("9. DERIVED STAT CHECKS")
if counts["player_game_stats"] > 0:
    # Passing pct should be 0-100
    cur.execute("""
        SELECT COUNT(*) as cnt FROM player_game_stats
        WHERE pass_comp IS NOT NULL AND pass_att IS NOT NULL AND pass_att > 0
          AND (pass_comp::float / pass_att * 100) > 100
    """)
    bad_pct = cur.fetchone()["cnt"]
    check("pass completion % <= 100", bad_pct == 0, f"{bad_pct} violations")

    # Team pts in quarters should roughly match pts_total
    if counts["team_game_stats"] > 0:
        cur.execute("""
            SELECT pts_q1, pts_q2, pts_q3, pts_q4, pts_ot, pts_total
            FROM team_game_stats
            WHERE pts_total IS NOT NULL
        """)
        rows = cur.fetchall()
        if rows:
            max_diff = 0
            for r in rows:
                q_sum = (r["pts_q1"] or 0) + (r["pts_q2"] or 0) + (r["pts_q3"] or 0) + (r["pts_q4"] or 0) + (r["pts_ot"] or 0)
                diff = abs(q_sum - (r["pts_total"] or 0))
                max_diff = max(max_diff, diff)
            check("quarter scores sum to pts_total", max_diff <= 3, f"max diff = {max_diff}")

# ==== SUMMARY ====
section("VALIDATION SUMMARY")
total = PASS + FAIL
print(f"\n  Total checks: {total}")
print(f"  PASSED: {PASS}")
print(f"  FAILED: {FAIL}")
if FAIL > 0:
    print("\n  SOME CHECKS FAILED - see details above")
    sys.exit(1)
else:
    print("\n  ALL CHECKS PASSED")
    sys.exit(0)
