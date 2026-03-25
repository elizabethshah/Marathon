from __future__ import annotations

import json
import sys
import time
import uuid
from pathlib import Path
from urllib import error, request

from tcx_parser import parse_tcx_file


ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "helper" / "import_state.json"
DEFAULT_WATCH_DIR = Path.home() / "Documents" / "GarminExports"
IMPORT_URL = "http://127.0.0.1:8000/api/import-workout"
POLL_SECONDS = 15


def main() -> None:
    watch_dir = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else DEFAULT_WATCH_DIR
    watch_dir.mkdir(parents=True, exist_ok=True)

    print(f"Watching {watch_dir} for new .tcx files")
    print("Press Ctrl+C to stop")

    while True:
        process_folder(watch_dir)
        time.sleep(POLL_SECONDS)


def process_folder(watch_dir: Path) -> None:
    state = load_state()
    seen_files = state.setdefault("seen_files", {})

    for file_path in sorted(watch_dir.glob("*.tcx")):
        fingerprint = build_fingerprint(file_path)
        if seen_files.get(str(file_path)) == fingerprint:
            continue

        try:
            workout = parse_tcx_file(file_path)
            workout["id"] = f"garmin-{uuid.uuid4()}"
            post_import(workout)
            seen_files[str(file_path)] = fingerprint
            save_state(state)
            print(f"Imported {file_path.name}")
        except error.HTTPError as http_error:
            message = http_error.read().decode("utf-8", errors="ignore")
            print(f"Skipped {file_path.name}: server rejected import ({http_error.code}) {message}")
            if http_error.code == 409:
                seen_files[str(file_path)] = fingerprint
                save_state(state)
        except Exception as exc:
            print(f"Could not import {file_path.name}: {exc}")


def build_fingerprint(file_path: Path) -> str:
    stat = file_path.stat()
    return f"{stat.st_mtime_ns}:{stat.st_size}"


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}

    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def post_import(workout: dict) -> None:
    body = json.dumps(workout).encode("utf-8")
    req = request.Request(
        IMPORT_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req) as response:
        response.read()


if __name__ == "__main__":
    main()
