import csv
import json
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ChargeEntry = dict[str, datetime | float | bool]

FULL_CHARGE_LEVEL = 100
EMPTY_CHARGE_LEVEL = 0


LOG_DIR = Path(__file__).resolve().parent

MODEL_FILE = LOG_DIR / "battery_charge_model.json"
SAMPLES_FILE = LOG_DIR / "battery_charge_samples.json"

SOURCES: dict[str, dict[str, str]] = {
    "wired": {"log_file": "battery_wired_charge_log_cleaned.csv"},
    "wireless": {"log_file": "battery_wireless_charge_log_cleaned.csv"},
}


def print_usage() -> None:
    print(
        "Usage:\n"
        "    python analyze_charge.py\n"
        "    python analyze_charge.py wired\n"
        "    python analyze_charge.py wireless",
        flush=True,
    )


def load_charge_log(
    source: str,
) -> list[ChargeEntry]:
    log_file = LOG_DIR / SOURCES[source]["log_file"]

    if not log_file.exists():
        raise FileNotFoundError(f"File not found: {log_file.name}")

    with log_file.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        return [
            {
                "timestamp": datetime.fromisoformat(row["timestamp"]),
                "battery_percent": float(row["battery_percent"]),
                "is_charging": row["is_charging"] == "True",
            }
            for row in reader
        ]


def get_charging_entries(
    entries: list[ChargeEntry],
) -> list[ChargeEntry]:
    charging_entries = [
        entry
        for entry in entries
        if entry["is_charging"]
    ]

    if not charging_entries:
        raise ValueError("No charging data found.")

    return charging_entries


def get_charge_level(
    entry: ChargeEntry,
) -> int | None:
    battery_percent = entry["battery_percent"]

    if entry["is_charging"] and battery_percent == EMPTY_CHARGE_LEVEL:
        return None

    return math.floor(battery_percent)


def build_charge_transitions(
    entries: list[ChargeEntry],
) -> dict[str, int]:
    charging_entries = get_charging_entries(entries)

    level_durations: defaultdict[str, list[int]] = defaultdict(list)

    previous_entry: ChargeEntry | None = None
    previous_level: int | None = None
    first_level: int | None = None

    for entry in charging_entries:
        current_level = get_charge_level(entry)

        if current_level is None:
            continue

        if previous_entry is None:
            previous_entry = entry
            previous_level = current_level
            first_level = current_level
            continue

        assert previous_level is not None
        assert first_level is not None

        if current_level > previous_level:
            duration = int(
                (entry["timestamp"] - previous_entry["timestamp"]).total_seconds()
            )

            is_initial_partial_transition = (
                first_level != EMPTY_CHARGE_LEVEL
                and previous_level == first_level
            )

            if not is_initial_partial_transition:
                level_durations[str(previous_level)].append(duration)

            previous_entry = entry
            previous_level = current_level

    if not level_durations:
        raise ValueError("No charge level durations found.")

    return dict(
        sorted(
            {
                level: sum(durations)
                for level, durations in level_durations.items()
            }.items(),
            key=lambda item: int(item[0]),
        )
    )


def load_samples() -> dict[str, Any]:
    if not SAMPLES_FILE.exists():
        return {"wired": [], "wireless": [],}

    with SAMPLES_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def load_model() -> dict[str, Any]:
    if not MODEL_FILE.exists():
        return {
            "wired": {
                "statistics": {
                    "sample_count": 0,
                    "last_updated": None,
                },
                "average": {},
            },
            "wireless": {
                "statistics": {
                    "sample_count": 0,
                    "last_updated": None,
                },
                "average": {},
            },
        }

    with MODEL_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def calculate_average_transitions(
    samples: list[dict[str, Any]],
) -> dict[str, int]:
    level_durations: defaultdict[str, list[int]] = defaultdict(list)

    for sample in samples:
        for level, seconds in sample["transitions"].items():
            level_durations[level].append(seconds)

    average_transitions: dict[str, int] = {}

    for level, durations in level_durations.items():
        average_transitions[level] = round(sum(durations) / len(durations))

    return dict(sorted(average_transitions.items(), key=lambda item: int(item[0])))


def save_model(
    data: dict[str, Any],
) -> None:
    with MODEL_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=4,
        )

        file.write("\n")


def save_samples(
    data: dict[str, Any],
) -> None:
    with SAMPLES_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=4,
        )

        file.write("\n")


def format_duration(
    seconds: int,
) -> str:
    hours, remainder = divmod(seconds, 3600)

    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f"{hours} h {minutes:02d} min {seconds:02d} s"

    return f"{minutes} min {seconds:02d} s"


def analyze_source(
    source: str,
) -> None:
    print(f"\nAnalyze {source}...", flush=True)

    entries = load_charge_log(source)

    transitions = build_charge_transitions(entries)

    samples = load_samples()
    model_data = load_model()

    now = datetime.now().astimezone().isoformat(timespec="seconds")

    samples[source].append({"created_at": now, "transitions": transitions,})

    model_data[source]["average"] = calculate_average_transitions(samples[source])

    model_data[source]["statistics"]["sample_count"] = len(samples[source])

    model_data[source]["statistics"]["last_updated"] = now

    save_samples(samples)

    save_model(model_data)

    print(f"Sample added: {model_data[source]['statistics']['sample_count']}", flush=True)

    print(f"Average model {source}:", flush=True)

    for level, seconds in model_data[source]["average"].items():
        print(f"{level:>2} % : {format_duration(seconds)}")


def main() -> None:
    args = sys.argv[1:]

    if len(args) > 1:
        print_usage()
        return

    if args:
        source = args[0]

        if source not in SOURCES:
            print_usage()
            return

        analyze_source(source)

    else:
        for source in SOURCES:
            analyze_source(source)


if __name__ == "__main__":
    main()