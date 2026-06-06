import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="nfl_fantasy",
    user="postgres",
    password="qabctpass",
)

cur = conn.cursor()
game_uuid = "dcd325fe-8dcf-4c1b-bc05-26b944c4e6ce"

# First, check if player_game_stats table has data for this game
try:
    cur.execute(
        """
    SELECT COUNT(*) FROM player_game_stats 
    WHERE game_id = $1 AND pass_att > 0 
    ORDER BY pass_yds DESC LIMIT 5
    """,
        (game_uuid,)
    )
    result = cur.fetchone()
    print(f"Total passing records with pass_att > 0: {result[0]}")
    for r in cur.fetchall()[:5]:
        print(f"  - Player {r[0]}: {r[1]}")
except Exception as e:
    print(f"Error: {e}")

cur.close()
conn.close()
