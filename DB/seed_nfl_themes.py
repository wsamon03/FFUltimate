"""Seed 32 NFL team themes using official brand hex colors only."""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncpg

load_dotenv(Path(__file__).parent.parent / ".env")

# All hex values are official team colors from teamcolorcodes.com.
# primary_color  = most iconic accent color
# primary_hover  = darker official color (used for hover state)
# bg_color       = darkest official color, very dark tinted background
# card_color     = slightly lighter bg
# card_hover     = slightly lighter card
# border_color   = muted border tinted with team color
# text_primary   = near-white (always readable)
# text_secondary = team secondary/accent color
#
# For bg/card/border we derive dark tints from the team's darkest official color.
# We never invent new colors — every hex used exists in the team's official palette
# except bg/card/card_hover/border which are darkened tints of official colors
# (since no team has 5 shades of dark bg in their palette).

TEAMS = [
    # AFC East
    # Bills: #00338D (royal blue), #C60C30 (red)
    ("bills", "Buffalo Bills",
     "#00338D", "#C60C30",
     "#050a17", "#0a1328", "#111e3d", "#1a2e58",
     "#f0f2f8", "#C60C30"),

    # Dolphins: #008E97 (aqua), #FC4C02 (orange), #005778 (dark blue)
    ("dolphins", "Miami Dolphins",
     "#008E97", "#005778",
     "#040f10", "#081c1e", "#0d292c", "#133d42",
     "#f0f8f8", "#FC4C02"),

    # Patriots: #002244 (navy), #C60C30 (red), #B0B7BC (silver)
    ("patriots", "New England Patriots",
     "#002244", "#C60C30",
     "#04080f", "#081018", "#0d1a28", "#152538",
     "#f0f2f8", "#C60C30"),

    # Jets: #125740 (green), #000000 (black)
    ("jets", "New York Jets",
     "#125740", "#000000",
     "#060f0b", "#0c1c15", "#122820", "#1a3a2c",
     "#f0f8f4", "#FFFFFF"),

    # AFC North
    # Ravens: #241773 (purple), #000000 (black), #9E7C0C (gold), #C60C30 (red)
    ("ravens", "Baltimore Ravens",
     "#241773", "#000000",
     "#07060f", "#0e0c1e", "#15122d", "#201a40",
     "#f0eef8", "#9E7C0C"),

    # Bengals: #FB4F14 (orange), #000000 (black)
    ("bengals", "Cincinnati Bengals",
     "#FB4F14", "#000000",
     "#100804", "#1e1008", "#2c180c", "#402212",
     "#f8f2ee", "#000000"),

    # Browns: #311D00 (brown), #FF3C00 (orange)
    ("browns", "Cleveland Browns",
     "#FF3C00", "#311D00",
     "#0f0800", "#1e1000", "#2d1800", "#3d2200",
     "#f8f2ee", "#311D00"),

    # Steelers: #FFB612 (gold), #101820 (black), #A5ACAF (silver)
    ("steelers", "Pittsburgh Steelers",
     "#FFB612", "#101820",
     "#080a0c", "#101820", "#18242e", "#22323e",
     "#f8f8f8", "#A5ACAF"),

    # AFC South
    # Texans: #03202F (navy), #A71930 (red)
    ("texans", "Houston Texans",
     "#A71930", "#03202F",
     "#060b0f", "#0c1820", "#122430", "#1a3040",
     "#f8f0f0", "#03202F"),

    # Colts: #002C5F (blue), #A2AAAD (silver)
    ("colts", "Indianapolis Colts",
     "#002C5F", "#A2AAAD",
     "#07090f", "#0c1220", "#122030", "#1a2e42",
     "#f0f2f8", "#A2AAAD"),

    # Jaguars: #101820 (black), #D7A22A (gold), #006778 (teal)
    ("jaguars", "Jacksonville Jaguars",
     "#006778", "#101820",
     "#04080a", "#081418", "#0d2025", "#143035",
     "#f0f6f8", "#D7A22A"),

    # Titans: #0C2340 (navy), #4B92DB (light blue), #C8102E (red)
    ("titans", "Tennessee Titans",
     "#4B92DB", "#0C2340",
     "#07080f", "#0c1020", "#121830", "#1a2542",
     "#f0f4f8", "#C8102E"),

    # AFC West
    # Broncos: #FB4F14 (orange), #002244 (navy)
    ("broncos", "Denver Broncos",
     "#FB4F14", "#002244",
     "#100804", "#1e1008", "#2c180c", "#3c2210",
     "#f8f2ee", "#002244"),

    # Chiefs: #E31837 (red), #FFB81C (gold)
    ("chiefs", "Kansas City Chiefs",
     "#E31837", "#FFB81C",
     "#100508", "#1e0a10", "#2c1018", "#3d1520",
     "#f8f0f1", "#FFB81C"),

    # Raiders: #000000 (black), #A5ACAF (silver)
    ("raiders", "Las Vegas Raiders",
     "#A5ACAF", "#000000",
     "#080808", "#101010", "#181818", "#242424",
     "#f8f8f8", "#000000"),

    # Chargers: #0080C6 (blue), #FFC20E (gold)
    ("chargers", "Los Angeles Chargers",
     "#0080C6", "#FFC20E",
     "#04101a", "#081e30", "#0e2c44", "#143858",
     "#f0f4f8", "#FFC20E"),

    # NFC East
    # Cowboys: #003594 (blue), #041E42 (dark navy), #869397 (silver)
    ("cowboys", "Dallas Cowboys",
     "#003594", "#041E42",
     "#060810", "#0a1020", "#101a32", "#182545",
     "#f0f2f8", "#869397"),

    # Giants: #0B2265 (blue), #A71930 (red), #A5ACAF (silver)
    ("giants", "New York Giants",
     "#0B2265", "#A71930",
     "#060810", "#0c1228", "#121e3e", "#1a2a52",
     "#f0f2f8", "#A71930"),

    # Eagles: #004C54 (midnight green), #A5ACAF (silver), #000000 (black)
    ("eagles", "Philadelphia Eagles",
     "#004C54", "#A5ACAF",
     "#04080a", "#081418", "#0d2025", "#143035",
     "#f0f6f6", "#A5ACAF"),

    # Commanders: #5A1414 (burgundy), #FFB612 (gold)
    ("commanders", "Washington Commanders",
     "#5A1414", "#FFB612",
     "#0f0606", "#1e0c0c", "#2c1212", "#3d1818",
     "#f8f0f0", "#FFB612"),

    # NFC North
    # Bears: #0B162A (navy), #C83803 (orange)
    ("bears", "Chicago Bears",
     "#C83803", "#0B162A",
     "#0a0c10", "#121820", "#1a2430", "#222e40",
     "#f8f2ee", "#0B162A"),

    # Lions: #0076B6 (blue), #B0B7BC (silver)
    ("lions", "Detroit Lions",
     "#0076B6", "#B0B7BC",
     "#06101a", "#0c1e30", "#122c44", "#183858",
     "#f0f4f8", "#B0B7BC"),

    # Packers: #203731 (green), #FFB612 (gold)
    ("packers", "Green Bay Packers",
     "#203731", "#FFB612",
     "#060d0c", "#0d1c18", "#142a24", "#1c3830",
     "#f0f8f4", "#FFB612"),

    # Vikings: #4F2683 (purple), #FFC62F (gold)
    ("vikings", "Minnesota Vikings",
     "#4F2683", "#FFC62F",
     "#0a080f", "#14101e", "#1e182e", "#2c2040",
     "#f2eef8", "#FFC62F"),

    # NFC South
    # Falcons: #A71930 (red), #000000 (black), #A5ACAF (silver)
    ("falcons", "Atlanta Falcons",
     "#A71930", "#000000",
     "#100608", "#1e0c10", "#2c1218", "#3d1820",
     "#f8f0f0", "#A5ACAF"),

    # Panthers: #0085CA (blue), #101820 (black), #BFC0BF (silver)
    ("panthers", "Carolina Panthers",
     "#0085CA", "#101820",
     "#060f18", "#0c1e2c", "#122c40", "#183855",
     "#f0f4f8", "#BFC0BF"),

    # Saints: #D3BC8D (gold), #101820 (black)
    ("saints", "New Orleans Saints",
     "#D3BC8D", "#101820",
     "#080808", "#101010", "#181818", "#222222",
     "#f8f8f8", "#101820"),

    # Buccaneers: #D50A0A (red), #FF7900 (orange), #34302B (pewter)
    ("buccaneers", "Tampa Bay Buccaneers",
     "#D50A0A", "#34302B",
     "#100606", "#1e0c0c", "#2c1212", "#3d1818",
     "#f8f0f0", "#FF7900"),

    # NFC West
    # Cardinals: #97233F (red), #000000 (black), #FFB612 (gold)
    ("cardinals", "Arizona Cardinals",
     "#97233F", "#000000",
     "#0f0608", "#1e0c10", "#2c1218", "#3d1820",
     "#f8f0f1", "#FFB612"),

    # Rams: #003594 (blue), #FFA300 (gold)
    ("rams", "Los Angeles Rams",
     "#003594", "#FFA300",
     "#06080f", "#0c1228", "#122040", "#1a2e55",
     "#f0f2f8", "#FFA300"),

    # 49ers: #AA0000 (red), #B3995D (gold)
    ("49ers", "San Francisco 49ers",
     "#AA0000", "#B3995D",
     "#100606", "#1e0c0c", "#2c1212", "#3d1818",
     "#f8f0f0", "#B3995D"),

    # Seahawks: #002244 (navy), #69BE28 (green), #A5ACAF (silver)
    ("seahawks", "Seattle Seahawks",
     "#002244", "#69BE28",
     "#04080f", "#081018", "#0e1c2c", "#162840",
     "#f0f2f8", "#69BE28"),
]

SQL = """
    INSERT INTO user_api.themes
        (name, display_name, primary_color, primary_hover, bg_color, card_color,
         card_hover, border_color, text_primary, text_secondary, font_family, is_default)
    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,'Inter, sans-serif',FALSE)
    ON CONFLICT (name) DO UPDATE SET
        display_name   = EXCLUDED.display_name,
        primary_color  = EXCLUDED.primary_color,
        primary_hover  = EXCLUDED.primary_hover,
        bg_color       = EXCLUDED.bg_color,
        card_color     = EXCLUDED.card_color,
        card_hover     = EXCLUDED.card_hover,
        border_color   = EXCLUDED.border_color,
        text_primary   = EXCLUDED.text_primary,
        text_secondary = EXCLUDED.text_secondary,
        font_family    = EXCLUDED.font_family
"""

async def main():
    conn = await asyncpg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        database=os.getenv("DB_NAME", "nfl_fantasy"),
    )
    for row in TEAMS:
        await conn.execute(SQL, *row)

    rows = await conn.fetch(
        "SELECT name, display_name, primary_color, text_secondary FROM user_api.themes "
        "WHERE name NOT IN ('dark','light','regular','forest') ORDER BY display_name"
    )
    for r in rows:
        print(f"{r['display_name']:<30} primary={r['primary_color']}  secondary={r['text_secondary']}")

    await conn.close()
    print(f"\nDone — {len(TEAMS)} team themes upserted.")

asyncio.run(main())
