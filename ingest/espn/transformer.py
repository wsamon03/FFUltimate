"""ESPN-specific stats transformer: normalized model -> DB stat dicts."""

import json
from typing import Any, Dict

from ingest.base import Transformer, BaseModel
from ingest.utils.transformers import (
    parse_possession_time, parse_fraction, parse_int,
    parse_sacks, safe_jsonb, map_stat_by_label, get_stat_from_statistics,
)


class ESPNTransformer(Transformer):
    """Transform ESPN normalized models into DB-ready stat dictionaries."""

    def transform_team_stats(self, team_model: BaseModel) -> dict:
        """Convert ESPN boxscore team data to DB-ready stat dict."""
        raw_stats = team_model.team_statistics if hasattr(team_model, "team_statistics") else []
        raw_score = team_model.score

        stats: Dict[str, Any] = {"pts_total": raw_score}

        for stat in raw_stats:
            if not isinstance(stat, dict):
                continue
            name = stat.get("name", "")
            display_value = stat.get("displayValue", "")
            value = stat.get("value")

            if name == "possessionTime":
                if display_value:
                    stats["off_possession_secs"] = parse_possession_time(display_value)
                elif value is not None and value != "-":
                    stats["off_possession_secs"] = parse_int(str(int(value)))

            elif "third" in name.lower():
                if display_value:
                    make, att = parse_fraction(display_value)
                    stats["off_3rd_make"] = make
                    stats["off_3rd_att"] = att

            elif name == "redZoneAttempts":
                if display_value:
                    make, att = parse_fraction(display_value)
                    stats["off_redzone_td"] = make
                    stats["off_redzone_att"] = att

            elif name == "firstDowns":
                if value is not None and value != "-":
                    stats["off_first_downs"] = parse_int(str(int(value)))

            elif name == "totalYards":
                yds_val = display_value if display_value and display_value != "-" else None
                stats["off_total_yds"] = parse_int(yds_val)

            elif name == "totalOffensivePlays":
                if value is not None and value != "-":
                    stats["off_plays"] = parse_int(str(int(value)))

            elif name == "totalPenaltiesYards":
                if display_value and "-" in display_value:
                    parts = display_value.split("-")
                    if len(parts) == 2:
                        stats["penalties_count"] = parse_int(parts[0])
                        stats["penalties_yds"] = parse_int(parts[1])

        return stats

    def transform_player_stats(self, player_model: BaseModel) -> dict:
        """Convert ESPN boxscore player data to DB-ready stat dict."""
        raw_cat = player_model.raw_category if hasattr(player_model, "raw_category") else {}
        labels = raw_cat.get("labels", [])
        stats_arr = raw_cat.get("stats", [])
        category_name = player_model.category_name if hasattr(player_model, "category_name") else ""
        return _parse_player_stats(labels, stats_arr, category_name)


def _parse_player_stats(labels: list, stats_arr: list, category_name: str) -> dict:
    """Parse a single player's stats from labels/stats arrays."""
    if not labels or not stats_arr:
        return {}

    stats = {}
    # Build label -> value map
    stat_map = {}
    for i, label in enumerate(labels):
        if i < len(stats_arr):
            stat_map[label] = stats_arr[i]

    category_lower = category_name.lower()

    if "pass" in category_lower:
        ca = stat_map.get("C/ATT", "")
        if ca:
            comp, att = parse_fraction(ca)
            stats["pass_comp"] = comp
            stats["pass_att"] = att
        stats["pass_yds"] = parse_int(stat_map.get("YDS"))
        stats["pass_td"] = parse_int(stat_map.get("TD"))
        stats["pass_int"] = parse_int(stat_map.get("INT"))
        sacks_str = stat_map.get("SACKS", "")
        if sacks_str and sacks_str != "-":
            if isinstance(sacks_str, str) and "-" in sacks_str:
                stats["pass_sacked"] = parse_int(sacks_str.split("-")[0])
            else:
                stats["pass_sacked"] = parse_sacks(sacks_str)

    elif "rush" in category_lower:
        stats["rush_att"] = parse_int(stat_map.get("CAR"))
        stats["rush_yds"] = parse_int(stat_map.get("YDS"))
        stats["rush_td"] = parse_int(stat_map.get("TD"))

    elif "recv" in category_lower or "receiving" in category_lower:
        stats["rec_receptions"] = parse_int(stat_map.get("REC"))
        stats["rec_targets"] = parse_int(stat_map.get("TGTS"))
        stats["rec_yds"] = parse_int(stat_map.get("YDS"))
        stats["rec_td"] = parse_int(stat_map.get("TD"))

    elif "def" in category_lower:
        solo = parse_int(stat_map.get("SOLO")) or 0
        tot = parse_int(stat_map.get("TOT")) or 0
        stats["def_solo"] = solo
        stats["def_ast"] = max(0, tot - solo)
        stats["def_sacks"] = parse_sacks(stat_map.get("SACKS", ""))
        stats["def_tfl"] = parse_int(stat_map.get("TFL"))
        stats["def_pd"] = parse_int(stat_map.get("PD"))
        stats["def_qb_hits"] = parse_int(stat_map.get("QB HTS"))
        stats["def_td"] = parse_int(stat_map.get("TD"))

    elif category_lower == "interceptions":
        stats["def_int"] = parse_int(stat_map.get("INT"))

    elif "kickreturn" in category_lower.replace(" ", ""):
        stats["ret_kick_no"] = parse_int(stat_map.get("NO"))
        stats["ret_kick_yds"] = parse_int(stat_map.get("YDS"))
        stats["ret_kick_td"] = parse_int(stat_map.get("TD"))

    elif "puntreturn" in category_lower.replace(" ", ""):
        stats["ret_punt_no"] = parse_int(stat_map.get("NO"))
        stats["ret_punt_yds"] = parse_int(stat_map.get("YDS"))
        stats["ret_punt_td"] = parse_int(stat_map.get("TD"))

    elif "kicking" in category_lower:
        fg = stat_map.get("FG", "")
        if fg and ("/" in fg or "-" in fg):
            make, att = parse_fraction(fg)
            stats["k_fg_make"] = make
            stats["k_fg_att"] = att
        xp = stat_map.get("XP", "")
        if xp and ("/" in xp or "-" in xp):
            make, att = parse_fraction(xp)
            stats["k_xp_make"] = make
            stats["k_xp_att"] = att

    elif "punting" in category_lower:
        stats["p_no"] = parse_int(stat_map.get("NO"))
        stats["p_yds"] = parse_int(stat_map.get("YDS"))
        stats["p_in20"] = parse_int(stat_map.get("In 20"))
        stats["p_tb"] = parse_int(stat_map.get("TB"))
        stats["p_fc"] = parse_int(stat_map.get("FC"))
        stats["p_blk"] = parse_int(stat_map.get("BLK"))
        stats["p_long"] = parse_int(stat_map.get("LONG"))

    return stats
