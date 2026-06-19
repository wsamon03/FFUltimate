"""Seed 32 NFL team themes into user_api.themes."""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncpg

load_dotenv(Path(__file__).parent.parent / ".env")

# (name, display_name, primary, hover, bg, card, card_hover, border, text_primary, text_secondary)
TEAMS = [
    ("cardinals",   "Arizona Cardinals",       "#97233F","#7a1b32","#100a0c","#1e1115","#2a161b","#3d2028","#f8f0f1","#a8a8a8"),
    ("falcons",     "Atlanta Falcons",          "#A71930","#8a1427","#100a0b","#1e1113","#2a1518","#3d2024","#f8f0f0","#a5acaf"),
    ("ravens",      "Baltimore Ravens",         "#4a30c0","#3a2499","#0a0810","#141228","#1e1a38","#2e2858","#f0eef8","#c9a820"),
    ("bills",       "Buffalo Bills",            "#00338D","#002570","#080c18","#0f1528","#161e38","#1d2d55","#f0f2f8","#e05868"),
    ("panthers",    "Carolina Panthers",        "#0085CA","#006ba3","#080f18","#0f1928","#162338","#1c3050","#f0f4f8","#a0a5a8"),
    ("bears",       "Chicago Bears",            "#C83803","#a32e02","#100a07","#1e1310","#2a1a15","#3d2820","#f8f2f0","#4a6090"),
    ("bengals",     "Cincinnati Bengals",       "#FB4F14","#d4410f","#110a07","#201310","#2e1b15","#4a2a1f","#f8f3f0","#c8a090"),
    ("browns",      "Cleveland Browns",         "#FF3C00","#d43000","#110a07","#1f1108","#2d1810","#4a2a18","#f8f2ee","#c8a070"),
    ("cowboys",     "Dallas Cowboys",           "#1848b8","#1238a0","#080c18","#0f1528","#161e38","#1d2d55","#f0f2f8","#96a0a8"),
    ("broncos",     "Denver Broncos",           "#FB4F14","#d4410f","#110a07","#201210","#2e1a15","#4a2a1f","#f8f3f0","#6a7ab0"),
    ("lions",       "Detroit Lions",            "#0076B6","#005f93","#080f18","#0f1828","#162238","#1c2e50","#f0f4f8","#b0b7bc"),
    ("packers",     "Green Bay Packers",        "#2e5a44","#245040","#080f0c","#0f1a15","#16251c","#1e3828","#f0f8f2","#FFB612"),
    ("texans",      "Houston Texans",           "#A71930","#8a1427","#100a0b","#1e1113","#2a1518","#3d2024","#f8f0f0","#4a7090"),
    ("colts",       "Indianapolis Colts",       "#1a5cb0","#145098","#07090f","#0c1020","#131830","#1a2245","#f0f2f8","#8090c8"),
    ("jaguars",     "Jacksonville Jaguars",     "#006778","#005060","#060f11","#0c1a1e","#12252a","#1a3840","#f0f6f8","#c8a840"),
    ("chiefs",      "Kansas City Chiefs",       "#E31837","#be142d","#10080a","#1e1013","#2a1418","#3d2025","#f8f0f1","#d4a820"),
    ("raiders",     "Las Vegas Raiders",        "#a5acaf","#8a9295","#0a0a0a","#141414","#1e1e1e","#2e2e2e","#f8f8f8","#a5acaf"),
    ("chargers",    "Los Angeles Chargers",     "#0080C6","#0066a0","#07101a","#0e1a28","#152438","#1c3250","#f0f4f8","#d4b020"),
    ("rams",        "Los Angeles Rams",         "#1848b8","#1238a0","#080c18","#0f1528","#161e38","#1d2d55","#f0f2f8","#c89010"),
    ("dolphins",    "Miami Dolphins",           "#008E97","#007280","#07100f","#0d1c1e","#14282a","#1a3c40","#f0f6f8","#d4601a"),
    ("vikings",     "Minnesota Vikings",        "#4F2683","#3e1e69","#0a080f","#140f1e","#1e162e","#30224d","#f2eef8","#d4a820"),
    ("patriots",    "New England Patriots",     "#C60C30","#a00a28","#100a0b","#1e1113","#2a1518","#3d2024","#f8f0f0","#6080a0"),
    ("saints",      "New Orleans Saints",       "#D3BC8D","#b8a070","#0a0a0a","#141414","#1e1e1e","#2e2e2e","#f8f8f8","#c8a870"),
    ("giants",      "New York Giants",          "#1040a0","#0c3488","#07080f","#0c1020","#131830","#1a2245","#f0f2f8","#d43838"),
    ("jets",        "New York Jets",            "#1a6e50","#145840","#07100c","#0d1a14","#14251c","#1a3826","#f0f6f2","#7ab870"),
    ("eagles",      "Philadelphia Eagles",      "#006a74","#005860","#060f10","#0c1a1c","#132428","#1a3438","#f0f6f6","#a5acaf"),
    ("steelers",    "Pittsburgh Steelers",      "#FFB612","#d49400","#0a0a0a","#141414","#1e1e1e","#2e2e2e","#f8f8f8","#a0a5a8"),
    ("49ers",       "San Francisco 49ers",      "#AA0000","#880000","#100808","#1e1010","#2a1414","#3d2020","#f8f0f0","#c8a070"),
    ("seahawks",    "Seattle Seahawks",         "#69BE28","#54991e","#07100a","#0e1c12","#15281a","#1c3822","#f0f6f2","#4a90c0"),
    ("buccaneers",  "Tampa Bay Buccaneers",     "#D50A0A","#b00808","#100808","#1e1010","#2a1414","#3d2020","#f8f0f0","#c8a870"),
    ("titans",      "Tennessee Titans",         "#418FDE","#3070b8","#07080f","#0c1020","#131830","#192245","#f0f2f8","#C8102E"),
    ("commanders",  "Washington Commanders",    "#773141","#5f2535","#0f0a0b","#1e1113","#2a1519","#3d2028","#f8f0f1","#c8a820"),
]

SQL = """
    INSERT INTO user_api.themes
        (name, display_name, primary_color, primary_hover, bg_color, card_color,
         card_hover, border_color, text_primary, text_secondary, font_family, is_default)
    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,'Inter, sans-serif',FALSE)
    ON CONFLICT (name) DO NOTHING
"""

async def main():
    conn = await asyncpg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        database=os.getenv("DB_NAME", "nfl_fantasy"),
    )
    inserted = skipped = 0
    for row in TEAMS:
        result = await conn.execute(SQL, *row)
        if result == "INSERT 0 1":
            inserted += 1
        else:
            skipped += 1

    total = await conn.fetchval("SELECT COUNT(*) FROM user_api.themes")
    print(f"Inserted: {inserted}  Skipped (already existed): {skipped}")
    print(f"Total themes in DB: {total}")

    rows = await conn.fetch("SELECT id, name, display_name FROM user_api.themes ORDER BY display_name")
    for r in rows:
        print(f"  [{r['id']:>2}] {r['name']:<12} — {r['display_name']}")

    await conn.close()

asyncio.run(main())
