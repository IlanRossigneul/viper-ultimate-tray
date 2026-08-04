import csv
import sys
from pathlib import Path


class BatteryLogCleaner:
    SOURCES: dict[str, str] = {
        "wired": "battery_wired_charge_log.csv",
        "wireless": "battery_wireless_charge_log.csv",
    }

    def __init__(
        self,
        log_dir: Path,
    ):
        self.log_dir = log_dir

    def clean(
        self,
        source: str,
    ) -> Path:
        if source not in self.SOURCES:
            raise ValueError(f"Invalid source: {source}")

        input_file = self.log_dir / self.SOURCES[source]

        output_file = self.log_dir / f"battery_{source}_charge_log_cleaned.csv"

        with input_file.open(
            "r",
            newline="",
            encoding="utf-8",
        ) as file:
            rows = list(csv.DictReader(file))

        if not rows:
            raise ValueError("File is empty.")

        cleaned_rows: list[dict[str, str]] = []

        for index, row in enumerate(rows):
            current_state = (row["battery_percent"], row["is_charging"])

            previous_state = None
            next_state = None

            if index > 0:
                previous_state = (rows[index - 1]["battery_percent"], rows[index - 1]["is_charging"])

            if index < len(rows) - 1:
                next_state = (rows[index + 1]["battery_percent"], rows[index + 1]["is_charging"])

            if current_state != previous_state or current_state != next_state:
                cleaned_rows.append(row)

        with output_file.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(file, fieldnames=["timestamp", "battery_percent", "is_charging"])

            writer.writeheader()
            writer.writerows(cleaned_rows)

        print(f"{len(rows)} original rows.")

        print(f"{len(cleaned_rows)} preserved rows.")

        print(f"Result: {output_file.name}")

        return output_file


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Usage:\n"
            "    python clean_battery_log.py wired\n"
            "    python clean_battery_log.py wireless"
        )
        sys.exit(1)

    source = sys.argv[1].lower()

    BatteryLogCleaner(Path(__file__).resolve().parent).clean(source)


if __name__ == "__main__":
    main()