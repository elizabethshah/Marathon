from __future__ import annotations

from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET


RUN_WORKOUT_TYPES = {"easy run", "long run", "tempo", "intervals"}


def parse_tcx_file(file_path: Path) -> dict:
    tree = ET.parse(file_path)
    root = tree.getroot()

    activity = first_by_local_name(root, "Activity")
    if activity is None:
        raise ValueError("No activity found in TCX file.")

    activity_id = text_of_first(activity, "Id")
    sport = activity.attrib.get("Sport", "Other")
    laps = list(elements_by_local_name(activity, "Lap"))

    total_seconds = sum(number_from_text(text_of_first(lap, "TotalTimeSeconds")) for lap in laps)
    total_meters = sum(number_from_text(text_of_first(lap, "DistanceMeters")) for lap in laps)
    calories = sum(number_from_text(text_of_first(lap, "Calories")) for lap in laps)

    average_heart_rate = 0
    for lap in laps:
        heart_rate = first_by_local_name(first_by_local_name(lap, "AverageHeartRateBpm"), "Value")
        if heart_rate is not None and heart_rate.text:
            average_heart_rate = round(number_from_text(heart_rate.text))
            break

    start_value = activity_id
    if not start_value and laps:
        start_value = laps[0].attrib.get("StartTime", "")

    start_date = parse_date(start_value)
    if start_date is None:
        raise ValueError("Could not find a valid activity date in TCX file.")

    distance_miles = meters_to_miles(total_meters)
    total_minutes = seconds_to_minutes(total_seconds)
    workout_type = map_imported_workout_type(sport, distance_miles)

    return {
        "importedActivityId": activity_id or start_date.isoformat(),
        "importedAt": start_date.isoformat(),
        "importedSport": sport,
        "date": start_date.date().isoformat(),
        "workoutType": workout_type,
        "plannedMiles": 0,
        "actualMiles": distance_miles if is_run_type(workout_type) else 0,
        "plannedPace": "",
        "actualPace": format_pace(distance_miles, total_minutes) if is_run_type(workout_type) else "",
        "exercises": "" if is_run_type(workout_type) else sport,
        "totalMinutes": 0 if is_run_type(workout_type) else total_minutes,
        "totalDurationMinutes": total_minutes,
        "averageHeartRate": average_heart_rate,
        "calories": calories,
        "notes": build_import_notes(sport, total_minutes, average_heart_rate, calories),
        "source": "garmin_import",
    }


def first_by_local_name(parent: ET.Element | None, name: str) -> ET.Element | None:
    if parent is None:
        return None

    for element in parent.iter():
        if local_name(element.tag) == name:
            return element
    return None


def elements_by_local_name(parent: ET.Element | None, name: str):
    if parent is None:
        return []

    return [element for element in parent.iter() if local_name(element.tag) == name]


def text_of_first(parent: ET.Element | None, name: str) -> str:
    element = first_by_local_name(parent, name)
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def parse_date(raw_value: str) -> datetime | None:
    if not raw_value:
        return None

    normalized = raw_value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def number_from_text(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def meters_to_miles(meters: float) -> float:
    return meters / 1609.344


def seconds_to_minutes(seconds: float) -> int:
    return round(seconds / 60)


def is_run_type(workout_type: str) -> bool:
    return workout_type in RUN_WORKOUT_TYPES


def map_imported_workout_type(sport: str, distance_miles: float) -> str:
    normalized = sport.lower()
    if "running" in normalized:
        return "long run" if distance_miles >= 10 else "easy run"
    if "strength" in normalized:
        return "strength"
    return "cross-training"


def format_pace(distance_miles: float, total_minutes: int) -> str:
    if not distance_miles or not total_minutes:
        return ""

    minutes_per_mile = total_minutes / distance_miles
    whole_minutes = int(minutes_per_mile)
    seconds = round((minutes_per_mile - whole_minutes) * 60)
    if seconds == 60:
        whole_minutes += 1
        seconds = 0
    return f"{whole_minutes}:{seconds:02d}/mi"


def build_import_notes(sport: str, total_minutes: int, average_heart_rate: int, calories: float) -> str:
    parts = [f"Imported from Garmin TCX ({sport})"]
    if total_minutes:
        parts.append(f"Duration {total_minutes} min")
    if average_heart_rate:
        parts.append(f"Avg HR {average_heart_rate} bpm")
    if calories:
        parts.append(f"Calories {int(calories)}")
    return " | ".join(parts)
