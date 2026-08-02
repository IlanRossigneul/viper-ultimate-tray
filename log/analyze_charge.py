import csv
import json
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


LOG_DIR = Path(__file__).parent

MODEL_FILE = (
    LOG_DIR
    / "battery_charge_model.json"
)


SOURCES = {
    "wired": {
        "log_file": "battery_wired_charge_log_cleaned.csv",
    },
    "wireless": {
        "log_file": "battery_wireless_charge_log_cleaned.csv",
    },
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
) -> list[dict]:
    log_file = (
        LOG_DIR
        / SOURCES[source]["log_file"]
    )

    if not log_file.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {log_file.name}"
        )

    with log_file.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        return [
            {
                "timestamp": datetime.fromisoformat(
                    row["timestamp"]
                ),
                "battery_percent": float(
                    row["battery_percent"]
                ),
                "is_charging": (
                    row["is_charging"] == "True"
                ),
            }
            for row in reader
        ]


def build_charge_model(
    entries: list[dict],
) -> dict[str, int]:
    charging_entries = [
        entry
        for entry in entries
        if entry["is_charging"]
    ]

    if not charging_entries:
        raise ValueError(
            "Aucune donnée de recharge trouvée."
        )

    full_charge_entry = next(
        (
            entry
            for entry in charging_entries
            if math.floor(
                entry["battery_percent"]
            ) >= 100
        ),
        None,
    )

    if full_charge_entry is None:
        raise ValueError(
            "Aucune donnée à 100 % trouvée."
        )

    full_charge_timestamp = (
        full_charge_entry["timestamp"]
    )

    charge_levels: dict[int, list[datetime]] = {}

    for entry in charging_entries:
        charge_level = math.floor(
            entry["battery_percent"]
        )

        if charge_level >= 100:
            break

        charge_levels.setdefault(
            charge_level,
            [],
        ).append(
            entry["timestamp"]
        )

    model = {}

    for charge_level, timestamps in (
        charge_levels.items()
    ):
        first_timestamp = min(
            timestamps
        )

        last_timestamp = max(
            timestamps
        )

        estimated_timestamp = (
            first_timestamp
            + (
                last_timestamp
                - first_timestamp
            ) / 2
        )

        remaining_seconds = int(
            (
                full_charge_timestamp
                - estimated_timestamp
            ).total_seconds()
        )

        model[str(charge_level)] = (
            remaining_seconds
        )

    return model


def load_model() -> dict:
    if not MODEL_FILE.exists():
        return {
            "sources": {
                "wired": {
                    "samples": [],
                    "average": {},
                    "statistics": {
                        "sample_count": 0,
                        "last_updated": None,
                    },
                },
                "wireless": {
                    "samples": [],
                    "average": {},
                    "statistics": {
                        "sample_count": 0,
                        "last_updated": None,
                    },
                },
            }
        }

    with MODEL_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def calculate_average_model(
    samples: list[dict],
) -> dict[str, int]:
    values = defaultdict(list)

    for sample in samples:
        for level, seconds in (
            sample["model"].items()
        ):
            values[level].append(
                seconds
            )

    average_model = {}

    for level, durations in (
        values.items()
    ):
        average_model[level] = round(
            sum(durations)
            /
            len(durations)
        )

    return dict(
        sorted(
            average_model.items(),
            key=lambda item: int(item[0]),
        )
    )


def save_model(
    data: dict,
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


def format_duration(
    seconds: int,
) -> str:
    hours, remainder = divmod(
        seconds,
        3600,
    )

    minutes, seconds = divmod(
        remainder,
        60,
    )

    if hours:
        return (
            f"{hours} h "
            f"{minutes:02d} min "
            f"{seconds:02d} s"
        )

    return (
        f"{minutes} min "
        f"{seconds:02d} s"
    )


def analyze_source(
    source: str,
) -> None:
    print(
        f"\nAnalyse {source}...",
        flush=True,
    )

    entries = load_charge_log(
        source
    )

    model = build_charge_model(
        entries
    )

    data = load_model()

    now = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    source_data = data["sources"][source]

    source_data["samples"].append(
        {
            "created_at": now,
            "model": model,
        }
    )

    source_data["average"] = (
        calculate_average_model(
            source_data["samples"]
        )
    )

    source_data["statistics"]["sample_count"] = (
        len(source_data["samples"])
    )

    source_data["statistics"]["last_updated"] = (
        now
    )

    save_model(
        data
    )

    print(
        f"Sample ajouté : "
        f"{source_data['statistics']['sample_count']}",
        flush=True,
    )

    print(
        f"Modèle moyen {source} :",
        flush=True,
    )

    for level, seconds in (
        source_data["average"].items()
    ):
        print(
            f"{level:>2} % → 100 % : "
            f"{format_duration(seconds)}",
        )


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

        analyze_source(
            source
        )

    else:
        for source in SOURCES:
            analyze_source(
                source
            )


if __name__ == "__main__":
    main()