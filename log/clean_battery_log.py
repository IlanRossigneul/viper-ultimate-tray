import csv
import sys
from pathlib import Path

LOG_DIR = Path(__file__).parent

VALID_SOURCES = {
    "wired",
    "wireless",
}

if len(sys.argv) != 2:
    print(
        "Usage:\n"
        "    python clean_battery_log.py wired\n"
        "    python clean_battery_log.py wireless"
    )
    sys.exit(1)

source = sys.argv[1].lower()

if source not in VALID_SOURCES:
    print(
        f"Invalid source: {source}\n"
        "Accepted values: wired, wireless"
    )
    sys.exit(1)

INPUT_FILE = (
    LOG_DIR
    / f"battery_{source}_charge_log.csv"
)

OUTPUT_FILE = (
    LOG_DIR
    / f"battery_{source}_charge_log_cleaned.csv"
)


def clean_log() -> None:
    with INPUT_FILE.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(csv.DictReader(file))

    if not rows:
        print("Le fichier est vide.")
        return

    cleaned_rows = []

    for index, row in enumerate(rows):
        current_state = (
            row["battery_percent"],
            row["is_charging"],
        )

        previous_state = None
        next_state = None

        if index > 0:
            previous_state = (
                rows[index - 1]["battery_percent"],
                rows[index - 1]["is_charging"],
            )

        if index < len(rows) - 1:
            next_state = (
                rows[index + 1]["battery_percent"],
                rows[index + 1]["is_charging"],
            )

        is_first = current_state != previous_state
        is_last = current_state != next_state

        if is_first or is_last:
            cleaned_rows.append(row)

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "timestamp",
                "battery_percent",
                "is_charging",
            ],
        )

        writer.writeheader()
        writer.writerows(cleaned_rows)

    print(
        f"{len(rows)} lignes originales.",
    )

    print(
        f"{len(cleaned_rows)} lignes conservées.",
    )

    print(
        f"Résultat : {OUTPUT_FILE.name}",
    )


if __name__ == "__main__":
    clean_log()