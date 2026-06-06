import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="nfl_fantasy",
    user="postgres",
    password="qabctpass",
)

cur = conn.cursor()

# Check if the game exists in games table
cur.execute("""
    SELECT id FROM games WHERE id = 'dcd325fe-8dcf-4c1b-bc05-26b944c4e6ce'
""")
game_exists = cur.fetchone()
print(f"Game dcd325fe... exists: {game_exists[0] if game_exists else 'NO'}")

# Check if player_game_stats has data for this game
cur.execute("""
    SELECT COUNT(*) FROM player_game_stats WHERE game_id = 'dcd325fe-8dcf-4c1b-bc05-26b944c4e6ce'
""")
count = cur.fetchone()[0]
print(f"player_game_stats for dcd325fe...: {count}")
if count == 0:
    print("No stats data for this game! Data needs to be ingested.")

# Check what columns player_game_stats has
cur.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_name = 'player_game_stats' 
    ORDER BY ordinal_position
    LIMIT 20
""")
cols = cur.fetchall()
print("\nPlayer_game_stats columns:")
for col in cols:
    print(f"  {col[0]}")

cur.close()
conn.close()
