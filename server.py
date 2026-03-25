from __future__ import annotations

import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parent
WORKOUTS_FILE = ROOT / "workouts.json"
RUN_WORKOUT_TYPES = {"easy run", "long run", "tempo", "intervals"}


def read_workouts() -> list[dict]:
    if not WORKOUTS_FILE.exists():
        return []

    try:
        return json.loads(WORKOUTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def write_workouts(workouts: list[dict]) -> None:
    WORKOUTS_FILE.write_text(json.dumps(workouts, indent=2), encoding="utf-8")


class WorkoutHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        # Avoid stale frontend files during local iteration.
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/workouts":
            self.respond_json(read_workouts())
            return

        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/workouts":
            self.handle_create_workout()
            return

        if parsed.path == "/api/import-workout":
            self.handle_import_workout()
            return

        self.respond_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def handle_create_workout(self) -> None:
        try:
            payload = self.read_json_body()
        except ValueError as error:
            self.respond_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return

        if not isinstance(payload, dict):
            self.respond_json({"error": "Expected a workout object."}, HTTPStatus.BAD_REQUEST)
            return

        workout_id = payload.get("id")
        if not workout_id:
            self.respond_json({"error": "Workout id is required."}, HTTPStatus.BAD_REQUEST)
            return

        workouts = read_workouts()
        if any(workout.get("id") == workout_id for workout in workouts):
            self.respond_json({"error": "Workout id already exists."}, HTTPStatus.CONFLICT)
            return
        if find_duplicate_workout(workouts, payload):
            self.respond_json({"error": "Workout looks like a duplicate of an existing Garmin import."}, HTTPStatus.CONFLICT)
            return

        workouts.append(payload)
        write_workouts(workouts)
        self.respond_json(payload, HTTPStatus.CREATED)

    def handle_import_workout(self) -> None:
        try:
            payload = self.read_json_body()
        except ValueError as error:
            self.respond_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return

        if not isinstance(payload, dict):
            self.respond_json({"error": "Expected a workout object."}, HTTPStatus.BAD_REQUEST)
            return

        workout_id = payload.get("id")
        if not workout_id:
            self.respond_json({"error": "Workout id is required."}, HTTPStatus.BAD_REQUEST)
            return

        source = payload.get("source")
        if source != "garmin_import":
            self.respond_json({"error": "Imported workouts must use source garmin_import."}, HTTPStatus.BAD_REQUEST)
            return

        workouts = read_workouts()
        if any(workout.get("id") == workout_id for workout in workouts):
            self.respond_json({"error": "Workout id already exists."}, HTTPStatus.CONFLICT)
            return
        if find_duplicate_workout(workouts, payload):
            self.respond_json({"error": "Workout looks like a duplicate of an existing workout."}, HTTPStatus.CONFLICT)
            return

        workouts.append(payload)
        write_workouts(workouts)
        self.respond_json(payload, HTTPStatus.CREATED)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        prefix = "/api/workouts/"
        if not parsed.path.startswith(prefix):
            self.respond_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return

        workout_id = unquote(parsed.path[len(prefix):])
        if not workout_id:
            self.respond_json({"error": "Workout id is required."}, HTTPStatus.BAD_REQUEST)
            return

        workouts = read_workouts()
        updated_workouts = [workout for workout in workouts if workout.get("id") != workout_id]
        if len(updated_workouts) == len(workouts):
            self.respond_json({"error": "Workout not found."}, HTTPStatus.NOT_FOUND)
            return

        write_workouts(updated_workouts)
        self.respond_json({"deletedId": workout_id})

    def read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        try:
            return json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("Request body must be valid JSON.") from error

    def respond_json(self, payload: dict | list, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def find_duplicate_workout(workouts: list[dict], candidate_workout: dict) -> bool:
    for workout in workouts:
        if is_plan_workout(workout) or is_plan_workout(candidate_workout):
            continue

        if candidate_workout.get("source") != "garmin_import" and workout.get("source") != "garmin_import":
            continue

        if workout.get("importedActivityId") and candidate_workout.get("importedActivityId"):
            if workout["importedActivityId"] == candidate_workout["importedActivityId"]:
                return True

        if workout.get("date") != candidate_workout.get("date"):
            continue

        candidate_is_run = is_workout_run_like(candidate_workout)
        existing_is_run = is_workout_run_like(workout)

        if candidate_is_run and existing_is_run:
            existing_miles = workout_distance_for_duplicate_check(workout)
            candidate_miles = workout_distance_for_duplicate_check(candidate_workout)
            if existing_miles and candidate_miles and abs(existing_miles - candidate_miles) <= 0.5:
                return True

        if not candidate_is_run and not existing_is_run:
            existing_minutes = workout_minutes_for_duplicate_check(workout)
            candidate_minutes = workout_minutes_for_duplicate_check(candidate_workout)
            if existing_minutes and candidate_minutes and abs(existing_minutes - candidate_minutes) <= 5:
                return True

    return False


def is_workout_run_like(workout: dict) -> bool:
    return workout.get("workoutType") in RUN_WORKOUT_TYPES


def is_plan_workout(workout: dict) -> bool:
    return workout.get("source") == "plan"


def workout_distance_for_duplicate_check(workout: dict) -> float:
    return to_float(workout.get("actualMiles")) or to_float(workout.get("plannedMiles"))


def workout_minutes_for_duplicate_check(workout: dict) -> float:
    return to_float(workout.get("totalMinutes")) or to_float(workout.get("totalDurationMinutes"))


def to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def main() -> None:
    if not WORKOUTS_FILE.exists():
        write_workouts([])

    server = ThreadingHTTPServer(("127.0.0.1", 8000), WorkoutHandler)
    print("Serving marathon tracker at http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
