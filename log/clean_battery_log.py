import csv
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent

VALID_SOURCES = {"wired", "wireless"}


def clean_log(
    input_file: Path,
    output_file: Path,
) -> None:
    with input_file.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:
        rows = list(csv.DictReader(file))

    if not rows:
        print("File is empty.")
        return

    cleaned_rows: list[dict[str, str]] = []

    for index, row in enumerate(rows):
        current_state = (row["battery_percent"], row["is_charging"])

        previous_state = None
        next_state = None

        if index > 0:
            previous_state = (rows[index - 1]["battery_percent"], rows[index - 1]["is_charging"])

        if index < len(rows) - 1:
            next_state = (rows[index + 1]["battery_percent"], rows[index + 1]["is_charging"])

        is_first = current_state != previous_state
        is_last = current_state != next_state

        if is_first or is_last:
            cleaned_rows.append(row)

    with output_file.open(
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

    print(f"{len(rows)} original rows.")

    print(f"{len(cleaned_rows)} preserved rows.")

    print(f"Result: {output_file.name}")


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Usage:\n"
            "    python clean_battery_log.py wired\n"
            "    python clean_battery_log.py wireless"
        )
        sys.exit(1)

    source = sys.argv[1].lower()

    if source not in VALID_SOURCES:
        print(f"Invalid source: {source}\nAccepted values: wired, wireless")
        sys.exit(1)

    input_file = LOG_DIR / f"battery_{source}_charge_log.csv"

    output_file = LOG_DIR / f"battery_{source}_charge_log_cleaned.csv"

    clean_log(input_file, output_file)


if __name__ == "__main__":
    main()