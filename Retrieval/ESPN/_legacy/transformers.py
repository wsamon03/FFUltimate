"""
Data transformation utilities for ESPN API to database schema mapping.
"""

import logging
import re
from typing import Tuple, Optional, Any

logger = logging.getLogger(__name__)


def parse_possession_time(mm_ss_str: str) -> Optional[int]:
    """
    Convert possession time from MM:SS format to total seconds.

    Args:
        mm_ss_str: String in format "MM:SS" or "M:SS"

    Returns:
        Total seconds as integer, or None if parsing fails
    """
    if not mm_ss_str or not isinstance(mm_ss_str, str):
        return None

    try:
        parts = mm_ss_str.split(":")
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = int(parts[1])
            return (minutes * 60) + seconds
    except (ValueError, AttributeError) as e:
        logger.debug(f"Failed to parse possession time '{mm_ss_str}': {e}")

    return None


def parse_fraction(frac_str: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Parse a fraction string like "5/12" into two integers.

    Args:
        frac_str: String in format "make/attempt"

    Returns:
        Tuple of (make, attempt) integers, with None for failed parses
    """
    if not frac_str or not isinstance(frac_str, str):
        return (None, None)

    try:
        parts = frac_str.split("/")
        if len(parts) == 2:
            make = int(parts[0])
            attempt = int(parts[1])
            return (make, attempt)
    except (ValueError, AttributeError) as e:
        logger.debug(f"Failed to parse fraction '{frac_str}': {e}")

    return (None, None)


def map_stat_by_label(labels: list, stats: list, target_label: str) -> Optional[str]:
    """
    Find stat value by matching label index in ESPN's dynamic stat arrays.

    ESPN returns stats as parallel arrays: labels[i] corresponds to stats[i].
    This function finds the index of target_label and returns the corresponding stat.

    Args:
        labels: List of stat label strings (e.g., ["CP/ATT", "YDS", "TD"])
        stats: List of stat value strings (e.g., ["5/12", "125", "1"])
        target_label: The label we're looking for

    Returns:
        Stat value string or None if label not found
    """
    if not labels or not stats or not target_label:
        return None

    try:
        # Find index of target label (case-insensitive)
        target_upper = target_label.upper()
        for i, label in enumerate(labels):
            if label and isinstance(label, str) and label.upper() == target_upper:
                if i < len(stats):
                    return stats[i]
    except (AttributeError, TypeError) as e:
        logger.debug(f"Error mapping stat by label '{target_label}': {e}")

    return None


def parse_sacks(sack_str: str) -> Optional[float]:
    """
    Parse sack value handling half-sacks (e.g., "0.5").

    Args:
        sack_str: Sack value as string

    Returns:
        Float value or None if parsing fails
    """
    if not sack_str or not isinstance(sack_str, str):
        return None

    try:
        return float(sack_str)
    except ValueError as e:
        logger.debug(f"Failed to parse sacks '{sack_str}': {e}")
        return None


def parse_int(s: str) -> Optional[int]:
    """
    Safely parse integer from string.

    Args:
        s: String value to parse

    Returns:
        Integer or None if parsing fails
    """
    if not s or not isinstance(s, str):
        return None

    try:
        return int(s)
    except ValueError as e:
        logger.debug(f"Failed to parse int '{s}': {e}")
        return None


def extract_stat_value(stat_obj: Any, target_label: str) -> Optional[str]:
    """
    Extract a stat value from ESPN's stat object structure.

    ESPN stats can be either:
    - Simple array: [value1, value2, ...] with labels array
    - Object with 'values' key

    Args:
        stat_obj: Stat object or list from ESPN API
        target_label: Label to find

    Returns:
        Stat value or None
    """
    if not stat_obj:
        return None

    # Handle object with labels/values structure
    if isinstance(stat_obj, dict):
        labels = stat_obj.get("labels", [])
        values = stat_obj.get("values", [])
        return map_stat_by_label(labels, values, target_label)

    # Handle simple list (some ESPN responses use this)
    if isinstance(stat_obj, list):
        # Try to find label in list and get next value
        for i, item in enumerate(stat_obj):
            if isinstance(item, str) and item.upper() == target_label.upper():
                if i + 1 < len(stat_obj):
                    return str(stat_obj[i + 1])

    return None


def get_stat_from_statistics(statistics: list, display_name: str, target_label: str) -> Optional[str]:
    """
    Find a stat value from ESPN's statistics array by display name and label.

    Args:
        statistics: List of stat objects from boxscore.teams[].statistics
        display_name: The stat group name (e.g., "Passing", "Rushing")
        target_label: The specific stat label within that group

    Returns:
        Stat value or None
    """
    if not statistics:
        return None

    for stat in statistics:
        if isinstance(stat, dict):
            if stat.get("name", "").lower() == display_name.lower():
                return extract_stat_value(stat, target_label)

    return None


def safe_jsonb(data: dict) -> dict:
    """
    Create a safe JSONB metadata dictionary.

    Filters out None values and ensures all values are JSON-serializable.

    Args:
        data: Dictionary of metadata

    Returns:
        Cleaned dictionary suitable for JSONB storage
    """
    if not data:
        return {}

    result = {}
    for key, value in data.items():
        if value is not None:
            # Handle any non-serializable values
            if isinstance(value, (str, int, float, bool, list, dict)):
                result[key] = value
            else:
                result[key] = str(value)

    return result
