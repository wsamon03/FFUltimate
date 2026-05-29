"""Pure data transformation utilities for ESPN API parsing."""

from typing import Tuple, Optional, Any


def parse_possession_time(mm_ss_str: str) -> Optional[int]:
    """Convert possession time from MM:SS format to total seconds."""
    if not mm_ss_str or not isinstance(mm_ss_str, str):
        return None
    try:
        parts = mm_ss_str.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, AttributeError):
        pass
    return None


def parse_fraction(frac_str: str) -> Tuple[Optional[int], Optional[int]]:
    """Parse a fraction string like '5/12' or '4-12' into (make, attempt)."""
    if not frac_str or not isinstance(frac_str, str):
        return (None, None)
    try:
        if "/" in frac_str:
            parts = frac_str.split("/")
        elif "-" in frac_str:
            parts = frac_str.split("-")
        else:
            return (None, None)
        if len(parts) == 2:
            return (int(parts[0]), int(parts[1]))
    except (ValueError, AttributeError):
        pass
    return (None, None)


def map_stat_by_label(labels: list, stats: list, target_label: str) -> Optional[str]:
    """Find stat value by matching label in ESPN's parallel arrays."""
    if not labels or not stats or not target_label:
        return None
    try:
        target_upper = target_label.upper()
        for i, label in enumerate(labels):
            if label and isinstance(label, str) and label.upper() == target_upper:
                if i < len(stats):
                    return stats[i]
    except (AttributeError, TypeError):
        pass
    return None


def parse_sacks(sack_str: str) -> Optional[float]:
    """Parse sack value handling half-sacks."""
    if not sack_str or not isinstance(sack_str, str):
        return None
    try:
        return float(sack_str)
    except ValueError:
        return None


def parse_int(s: str) -> Optional[int]:
    """Safely parse integer from string."""
    if not s or not isinstance(s, str):
        return None
    try:
        return int(s)
    except ValueError:
        return None


def safe_jsonb(data: dict) -> dict:
    """Create a JSONB-safe dictionary by filtering out None values."""
    if not data:
        return {}
    result = {}
    for key, value in data.items():
        if value is not None:
            if isinstance(value, (str, int, float, bool, list, dict)):
                result[key] = value
            else:
                result[key] = str(value)
    return result


def extract_stat_value(stat_obj: Any, target_label: str) -> Optional[str]:
    """Extract a stat value from ESPN's stat object (dict with labels/values or simple list)."""
    if not stat_obj:
        return None
    if isinstance(stat_obj, dict):
        labels = stat_obj.get("labels", [])
        values = stat_obj.get("values", [])
        return map_stat_by_label(labels, values, target_label)
    if isinstance(stat_obj, list):
        for i, item in enumerate(stat_obj):
            if isinstance(item, str) and item.upper() == target_label.upper():
                if i + 1 < len(stat_obj):
                    return str(stat_obj[i + 1])
    return None


def get_stat_from_statistics(statistics: list, display_name: str, target_label: str) -> Optional[str]:
    """Find a stat value from ESPN's statistics array by display name and label."""
    if not statistics:
        return None
    for stat in statistics:
        if isinstance(stat, dict) and stat.get("name", "").lower() == display_name.lower():
            return extract_stat_value(stat, target_label)
    return None
