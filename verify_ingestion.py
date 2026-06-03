"""Verify player stats ingestion after COALESCE fix."""
import urllib.request, json
import time

def get_task_status(task_id):
    """Poll task status until completed."""
    for i in range(20):
        time.sleep(5)
        url = "http://localhost:8002/api/ingest/status/{}".format(task_id)
        try:
            resp = urllib.request.urlopen(url, timeout=5)
            status = json.loads(resp.read())
            if status['status'] != 'running':
                return status
        except:
            pass
    return None

def main():
    # Trigger W8/2024 ingestion
    url = "http://localhost:8002/api/ingest/week?year=2024&week=8"
    req = urllib.request.Request(url, method='POST')
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    task_id = data['task_id']
    print("Created task: {}".format(task_id))
    
    # Wait for completion
    status = get_task_status(task_id)
    print("Final status:\n{}".format(json.dumps(status, indent=2)))
    
    # Verify DB
    import psycopg2
    conn = psycopg2.connect(host='localhost', port='5432', dbname='nfl_fantasy', user='postgres', password='owenethanTKD')
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM games WHERE season_year=2024 AND week=8')
    w8_games = cur.fetchone()[0]
    print("W8/2024 games: {}".format(w8_games))
    
    cur.execute('SELECT COUNT(*) FROM player_game_stats WHERE game_id IN (SELECT id FROM games WHERE season_year=2024 AND week=8)')
    w8_ps = cur.fetchone()[0]
    print("W8/2024 player stats: {}".format(w8_ps))
    
    cur.execute("""
        SELECT g.espn_id, pgs.pass_yds, pgs.rush_yds, pgs.rec_yds
        FROM games g 
        JOIN player_game_stats pgs ON pgs.game_id = g.id
        JOIN players p ON pgs.player_id = p.id
        WHERE g.espn_id = 401671852 AND p.name = 'Jameis Winston'
    """)
    wst_stats = cur.fetchall()
    q4_stats = sum(1 for _, py, ry, re in wst_stats if py >= 300)
    print("Jameis Winston stats (pass_yds >= 300): {} rows".format(q4_stats))
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
