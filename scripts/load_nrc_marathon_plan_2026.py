from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKOUTS_FILE = ROOT / "workouts.json"
PLAN_NAME = "nrc_marathon_2026"
START_DATE = date(2026, 6, 29)
RACE_DATE = date(2026, 11, 1)

PACE = {
    "mile": "7:00/mi",
    "5k": "7:40/mi",
    "10k": "7:55/mi",
    "tempo": "8:15/mi",
    "half": "8:20/mi",
    "marathon": "8:35/mi",
    "recovery": "9:20/mi",
    "best": "Best pace by feel",
}


@dataclass(frozen=True)
class RunEntry:
    label: str
    workout_type: str
    pace: str
    notes: str
    planned_miles: float = 0.0


@dataclass(frozen=True)
class NonRunEntry:
    workout_type: str
    exercises: str
    total_minutes: int
    notes: str


def estimate_miles_from_minutes(minutes: int, pace_minutes: float) -> float:
    return round(minutes / pace_minutes, 1)


def make_recovery_run(label: str, description: str, minutes: int | None = None, miles: float | None = None) -> RunEntry:
    if miles is None and minutes is not None:
        miles = estimate_miles_from_minutes(minutes, 9 + (20 / 60))

    if miles is None:
        miles = 0.0

    if minutes is not None:
        note = f"{label}: {description}. Target recovery pace {PACE['recovery']}."
    else:
        note = f"{label}: {description} at recovery pace {PACE['recovery']}."

    return RunEntry(label=label, workout_type="easy run", pace=PACE["recovery"], notes=note, planned_miles=miles)


def make_long_run(description: str, miles: float, note_suffix: str = "") -> RunEntry:
    notes = f"Long run: {description}. Run as a comfortable progression, starting near {PACE['recovery']} and finishing closer to {PACE['marathon']}."
    if note_suffix:
        notes = f"{notes} {note_suffix}"
    return RunEntry(label="Long Run", workout_type="long run", pace=f"{PACE['recovery']} -> {PACE['marathon']}", notes=notes, planned_miles=miles)


def make_speed_run(description: str, workout_type: str, pace: str, note_suffix: str = "") -> RunEntry:
    notes = description
    if note_suffix:
        notes = f"{notes} {note_suffix}"
    return RunEntry(label="Speed Run", workout_type=workout_type, pace=pace, notes=notes, planned_miles=0.0)


def make_strength(minutes: int = 30, note_suffix: str = "") -> NonRunEntry:
    notes = "Strength day added to replace one rest day. Focus on core, hips, glutes, and light single-leg stability."
    if note_suffix:
        notes = f"{notes} {note_suffix}"
    return NonRunEntry(workout_type="strength", exercises="Core, glutes, hips, single-leg stability", total_minutes=minutes, notes=notes)


def make_cross_train(minutes: int = 45, note_suffix: str = "") -> NonRunEntry:
    notes = "Cross-training day added to replace one rest day. Keep this aerobic and low impact."
    if note_suffix:
        notes = f"{notes} {note_suffix}"
    return NonRunEntry(workout_type="cross-training", exercises="Bike, elliptical, swim, or brisk walk", total_minutes=minutes, notes=notes)


WEEKS = [
    {
        "weeks_to_go": 18,
        "monday": make_recovery_run("Recovery Run 1", "10:00 recovery run", minutes=10),
        "tuesday": make_speed_run("Intervals: 5:00 warm up, then 8 x 1:00 at 5K pace with 1:00 recovery between intervals.", "intervals", f"5K pace {PACE['5k']}"),
        "wednesday": make_strength(),
        "thursday": make_recovery_run("Recovery Run 2", "7:00 recovery run", minutes=7),
        "friday": make_recovery_run("Recovery Run 3", "2 mile recovery run", miles=2.0),
        "saturday": make_long_run("5 mile long run", 5.0),
        "sunday": make_cross_train(),
    },
    {
        "weeks_to_go": 17,
        "monday": make_recovery_run("Recovery Run 1", "12:00 recovery run", minutes=12),
        "tuesday": make_speed_run("Intervals: 5:00 warm up, then 1:00 at 5K pace, 2:00 at 10K pace, 1:00 at 5K pace, 2 x 0:45 at mile pace, 2:00 at 10K pace, 1:00 at 5K pace, 0:45 at mile pace, 0:30 best pace, 0:15 best pace, with 1:00 recovery between intervals.", "intervals", f"5K {PACE['5k']} | 10K {PACE['10k']} | Mile {PACE['mile']} | {PACE['best']}"),
        "wednesday": make_strength(),
        "thursday": make_recovery_run("Recovery Run 2", "5K recovery run", miles=3.1),
        "friday": make_recovery_run("Recovery Run 3", "1 mile recovery run", miles=1.0),
        "saturday": make_long_run("10K long run", 6.2),
        "sunday": make_cross_train(),
    },
    {
        "weeks_to_go": 16,
        "monday": make_recovery_run("Recovery Run 1", "15:00 recovery run", minutes=15),
        "tuesday": make_speed_run("Fartlek: 5:00 warm up, then 21:00 alternating 1:00 hard running and 2:00 easy running.", "intervals", f"Hard running near 5K pace {PACE['5k']}"),
        "wednesday": make_strength(),
        "thursday": make_recovery_run("Recovery Run 2", "5K recovery run", miles=3.1),
        "friday": make_recovery_run("Recovery Run 3", "25:00 recovery run", minutes=25),
        "saturday": make_long_run("7 mile long run", 7.0),
        "sunday": make_cross_train(),
    },
    {
        "weeks_to_go": 15,
        "monday": make_recovery_run("Recovery Run 1", "20:00 recovery run", minutes=20),
        "tuesday": make_speed_run("Hill workout: 5:00 warm up, then 5 rounds of 45 seconds at 10K effort and 15 seconds best effort. Recover 1:15 after the 10K effort and 0:45 after the best effort.", "intervals", f"10K effort {PACE['10k']} | {PACE['best']}"),
        "wednesday": make_strength(),
        "thursday": make_recovery_run("Recovery Run 2", "30:00 recovery run", minutes=30),
        "friday": make_recovery_run("Recovery Run 3", "35:00 recovery run", minutes=35),
        "saturday": make_long_run("10K long run", 6.2),
        "sunday": make_cross_train(),
    },
    {
        "weeks_to_go": 14,
        "monday": make_recovery_run("Recovery Run 1", "25:00 recovery run", minutes=25),
        "tuesday": make_speed_run("Intervals: 7:00 warm up, 3 x 2:00 at 5K pace, 10:00 tempo run, then 3 x 2:00 at 5K pace. Recover 1:00 after the 5K pace reps and 2:00 after the tempo run.", "intervals", f"5K {PACE['5k']} | Tempo {PACE['tempo']}"),
        "wednesday": make_strength(),
        "thursday": make_recovery_run("Recovery Run 2", "40:00 recovery run", minutes=40),
        "friday": make_recovery_run("Recovery Run 3", "45:00 recovery run", minutes=45),
        "saturday": make_long_run("8 mile long run", 8.0),
        "sunday": make_cross_train(),
    },
    {
        "weeks_to_go": 13,
        "monday": make_recovery_run("Recovery Run 1", "30:00 recovery run", minutes=30),
        "tuesday": make_speed_run("Intervals: 5:00 warm up, then 3 sets of 3:00 at 5K pace plus 4 x 0:30 at mile pace. Recover 2:00 after the 5K rep and 1:00 after the mile rep.", "intervals", f"5K {PACE['5k']} | Mile {PACE['mile']}"),
        "wednesday": make_strength(),
        "thursday": make_recovery_run("Recovery Run 2", "35:00 recovery run", minutes=35),
        "friday": make_recovery_run("Recovery Run 3", "45:00 recovery run", minutes=45),
        "saturday": make_long_run("10 mile long run", 10.0),
        "sunday": make_cross_train(),
    },
    {
        "weeks_to_go": 12,
        "monday": make_recovery_run("Recovery Run 1", "35:00 recovery run", minutes=35),
        "tuesday": make_speed_run("Tempo run: 7:00 warm up, then 20:00 at tempo pace.", "tempo", f"Tempo pace {PACE['tempo']}"),
        "wednesday": make_strength(),
        "thursday": make_recovery_run("Recovery Run 2", "30:00 recovery run", minutes=30),
        "friday": make_recovery_run("Recovery Run 3", "48:00 recovery run", minutes=48),
        "saturday": make_long_run("15K long run", 9.32),
        "sunday": make_cross_train(),
    },
    {
        "weeks_to_go": 11,
        "monday": make_recovery_run("Recovery Run 1", "35:00 recovery run", minutes=35),
        "tuesday": make_speed_run("Intervals: 5:00 warm up, then 3 x 7:00 at 5K pace with 2:30 recovery between intervals.", "intervals", f"5K pace {PACE['5k']}"),
        "wednesday": make_strength(),
        "thursday": make_recovery_run("Recovery Run 2", "25:00 recovery run", minutes=25),
        "friday": make_recovery_run("Recovery Run 3", "60:00 recovery run", minutes=60),
        "saturday": make_long_run("20K long run", 12.5),
        "sunday": make_cross_train(),
    },
    {
        "weeks_to_go": 10,
        "monday": make_recovery_run("Recovery Run 1", "45:00 recovery run", minutes=45),
        "tuesday": make_speed_run("Tempo run: 7:00 warm up, then 25:00 at tempo pace.", "tempo", f"Tempo pace {PACE['tempo']}"),
        "wednesday": make_strength(),
        "thursday": make_recovery_run("Recovery Run 2", "32:00 recovery run", minutes=32),
        "friday": make_recovery_run("Recovery Run 3", "33:00 recovery run", minutes=33),
        "saturday": make_long_run("Half marathon long run", 13.1),
        "sunday": make_cross_train(),
    },
    {
        "weeks_to_go": 9,
        "monday": make_recovery_run("Recovery Run 1", "50:00 recovery run", minutes=50),
        "tuesday": make_speed_run("Intervals: 5:00 warm up, then 5 x 5:00 at 10K pace with 2:00 recovery between intervals.", "intervals", f"10K pace {PACE['10k']}"),
        "wednesday": make_strength(),
        "thursday": make_recovery_run("Recovery Run 2", "60:00 recovery run", minutes=60),
        "friday": make_recovery_run("Recovery Run 3", "33:00 recovery run", minutes=33),
        "saturday": make_long_run("120:00 long run", 13.6, "Planned miles estimated from roughly 9:20-8:35 progression effort over 120 minutes."),
        "sunday": make_cross_train(),
    },
    {
        "weeks_to_go": 8,
        "monday": make_recovery_run("Recovery Run 1", "40:00 recovery run", minutes=40),
        "tuesday": make_speed_run("Tempo run: 5:00 warm up, 23:00 tempo run. First 12:00 strong and controlled, last 11:00 progressively faster, aiming to cover the same distance out and back.", "tempo", f"Tempo pace {PACE['tempo']}"),
        "wednesday": make_strength(),
        "thursday": make_recovery_run("Recovery Run 2", "35:00 recovery run", minutes=35),
        "friday": make_recovery_run("Recovery Run 3", "30:00 recovery run", minutes=30),
        "saturday": make_long_run("22-26K / 14-16 mile long run", 15.0, "Planned miles use the midpoint of Nike's 14-16 mile range."),
        "sunday": make_cross_train(),
    },
    {
        "weeks_to_go": 7,
        "monday": make_recovery_run("Recovery Run 1", "60:00 recovery run", minutes=60),
        "tuesday": make_speed_run("Hill workout: 5:00 warm up, then 1:00 at 10K effort, 0:45 at 5K effort, 0:30 at mile effort. Run the full series 3 times. Recover 2:00 after 10K effort, 1:30 after 5K effort, and 1:00 after mile effort.", "intervals", f"10K {PACE['10k']} | 5K {PACE['5k']} | Mile {PACE['mile']}"),
        "wednesday": make_strength(),
        "thursday": make_recovery_run("Recovery Run 2", "30:00 recovery run", minutes=30),
        "friday": make_recovery_run("Recovery Run 3", "30:00 recovery run", minutes=30),
        "saturday": make_long_run("26-29K / 16-18 mile long run", 17.0, "Planned miles use the midpoint of Nike's 16-18 mile range."),
        "sunday": make_cross_train(),
    },
    {
        "weeks_to_go": 6,
        "monday": make_recovery_run("Recovery Run 1", "65:00 recovery run", minutes=65),
        "tuesday": make_speed_run("Intervals: 5:00 warm up, then 8:00 at 10K pace, 4:00 at 5K pace, 2:00 at mile pace. Run the full series 3 times. Recover 3:00 after 10K pace and 2:00 after the 5K and mile pace reps.", "intervals", f"10K {PACE['10k']} | 5K {PACE['5k']} | Mile {PACE['mile']}"),
        "wednesday": make_strength(),
        "thursday": make_recovery_run("Recovery Run 2", "31:00 recovery run", minutes=31),
        "friday": make_recovery_run("Recovery Run 3", "30:00 recovery run", minutes=30),
        "saturday": make_long_run("90:00 long run", 10.0, "Planned miles estimated from roughly 9:20-8:35 progression effort over 90 minutes."),
        "sunday": make_cross_train(),
    },
    {
        "weeks_to_go": 5,
        "monday": make_recovery_run("Recovery Run 1", "75:00 recovery run", minutes=75),
        "tuesday": make_speed_run("Fartlek: 5:00 warm up, then 21:00 alternating 2:00 hard running and 1:00 easy running.", "intervals", f"Hard running near 10K to 5K pace ({PACE['10k']} to {PACE['5k']})"),
        "wednesday": make_strength(),
        "thursday": make_recovery_run("Recovery Run 2", "25:00 recovery run", minutes=25),
        "friday": make_recovery_run("Recovery Run 3", "30:00 recovery run", minutes=30),
        "saturday": make_long_run("29-35K / 18-22 mile long run", 20.0, "Planned miles use the midpoint of Nike's 18-22 mile range."),
        "sunday": make_cross_train(),
    },
    {
        "weeks_to_go": 4,
        "monday": make_recovery_run("Recovery Run 1", "45:00 recovery run", minutes=45),
        "tuesday": make_speed_run("Power Pyramid intervals: 5:00 warm up, 1:00 at mile pace, 5:00 at 5K pace, 10:00 at 10K pace, 5:00 at 5K pace, 1:00 at mile pace. Recover 0:30 after mile pace, 2:30 after 5K pace, and 3:00 after 10K pace.", "intervals", f"Mile {PACE['mile']} | 5K {PACE['5k']} | 10K {PACE['10k']}"),
        "wednesday": make_strength(),
        "thursday": make_recovery_run("Recovery Run 2", "45:00 recovery run", minutes=45),
        "friday": make_recovery_run("Recovery Run 3", "25:00 recovery run", minutes=25),
        "saturday": make_long_run("24-26K / 15-16 mile long run", 15.5, "Planned miles use the midpoint of Nike's 15-16 mile range."),
        "sunday": make_cross_train(),
    },
    {
        "weeks_to_go": 3,
        "monday": make_recovery_run("Recovery Run 1", "80:00 recovery run", minutes=80),
        "tuesday": make_speed_run("Tempo run: 2K warm up, 8K at tempo pace, 2K cool down.", "tempo", f"Tempo pace {PACE['tempo']}", note_suffix="This is roughly a 12K / 7.5 mile session including warm up and cool down."),
        "wednesday": make_strength(),
        "thursday": make_recovery_run("Recovery Run 2", "25:00 recovery run", minutes=25),
        "friday": make_recovery_run("Recovery Run 3", "30:00 recovery run", minutes=30),
        "saturday": make_long_run("19-23K / 12-14 mile long run", 13.0, "Planned miles use the midpoint of Nike's 12-14 mile range."),
        "sunday": make_cross_train(),
    },
    {
        "weeks_to_go": 2,
        "monday": make_recovery_run("Recovery Run 1", "45:00 recovery run", minutes=45),
        "tuesday": make_speed_run("Intervals: 6:00 warm up, then 1:00 at mile pace, 3:00 at 5K pace, 5:00 at 10K pace, 7:00 at recovery pace. Recover 0:30 after mile pace, 1:30 after 5K pace, and 2:30 after 10K pace.", "intervals", f"Mile {PACE['mile']} | 5K {PACE['5k']} | 10K {PACE['10k']} | Recovery {PACE['recovery']}"),
        "wednesday": make_strength(),
        "thursday": make_recovery_run("Recovery Run 2", "4.0 mile recovery run", miles=4.0),
        "friday": make_recovery_run("Recovery Run 3", "60:00 recovery run", minutes=60),
        "saturday": make_long_run("10 mile long run", 10.0),
        "sunday": make_cross_train(),
    },
    {
        "weeks_to_go": 1,
        "monday": make_recovery_run("Recovery Run 1", "5K / 3.1 mile recovery run", miles=3.1),
        "tuesday": make_speed_run("Tempo progression: 5:00 warm up, then 5:00 at recovery pace, 4:00 at 10K pace, 3:00 at 5K pace, 2:00 at mile pace, and 1:00 best pace.", "tempo", f"Recovery {PACE['recovery']} | 10K {PACE['10k']} | 5K {PACE['5k']} | Mile {PACE['mile']} | {PACE['best']}"),
        "wednesday": NonRunEntry(workout_type="strength", exercises="Light mobility, core activation, glute activation", total_minutes=20, notes="Race-week light strength only. Keep this easy and non-fatiguing."),
        "thursday": make_recovery_run("Recovery Run 2", "25:00 recovery run", minutes=25),
        "friday": make_recovery_run("Recovery Run 3", "1 mile recovery run", miles=1.0),
        "saturday": NonRunEntry(workout_type="cross-training", exercises="Easy walk, short spin, or mobility flow", total_minutes=20, notes="Race-week cross-training kept very light. Treat this as movement, not training."),
        "sunday": RunEntry(label="Race Day", workout_type="long run", pace=PACE["marathon"], notes="Race day: Marathon 26.2 miles. Target pace from the Nike pace chart for a 3:45 goal is 8:35/mi.", planned_miles=26.2),
    },
]


def build_plan_workouts() -> list[dict]:
    workouts: list[dict] = []

    for week_index, week in enumerate(WEEKS):
        week_start = START_DATE + timedelta(weeks=week_index)
        for day_offset, day_name in enumerate(["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
            workout_date = week_start + timedelta(days=day_offset)
            entry = week[day_name]
            if isinstance(entry, RunEntry):
                workouts.append({
                    "id": f"plan-{uuid.uuid4()}",
                    "date": workout_date.isoformat(),
                    "workoutType": entry.workout_type,
                    "plannedMiles": entry.planned_miles,
                    "actualMiles": 0,
                    "plannedPace": entry.pace,
                    "actualPace": "",
                    "exercises": "",
                    "totalMinutes": 0,
                    "notes": f"Week {week['weeks_to_go']} to go ({week_start.isoformat()}) | {entry.notes}",
                    "source": "plan",
                    "planName": PLAN_NAME,
                    "planWeek": week["weeks_to_go"],
                    "planLabel": entry.label,
                })
            else:
                workouts.append({
                    "id": f"plan-{uuid.uuid4()}",
                    "date": workout_date.isoformat(),
                    "workoutType": entry.workout_type,
                    "plannedMiles": 0,
                    "actualMiles": 0,
                    "plannedPace": "",
                    "actualPace": "",
                    "exercises": entry.exercises,
                    "totalMinutes": entry.total_minutes,
                    "notes": f"Week {week['weeks_to_go']} to go ({week_start.isoformat()}) | {entry.notes}",
                    "source": "plan",
                    "planName": PLAN_NAME,
                    "planWeek": week["weeks_to_go"],
                    "planLabel": entry.workout_type.title(),
                })

    return workouts


def main() -> None:
    existing_workouts = []
    if WORKOUTS_FILE.exists():
        existing_workouts = json.loads(WORKOUTS_FILE.read_text(encoding="utf-8"))

    preserved_workouts = [
        workout
        for workout in existing_workouts
        if not (workout.get("source") == "plan" and workout.get("planName") == PLAN_NAME)
    ]

    plan_workouts = build_plan_workouts()
    combined_workouts = preserved_workouts + plan_workouts
    combined_workouts.sort(key=lambda workout: workout["date"])

    WORKOUTS_FILE.write_text(json.dumps(combined_workouts, indent=2), encoding="utf-8")

    print(f"Loaded {len(plan_workouts)} Nike plan workouts into {WORKOUTS_FILE}")
    print(f"Race date: {RACE_DATE.isoformat()} at target marathon pace {PACE['marathon']}")


if __name__ == "__main__":
    main()
