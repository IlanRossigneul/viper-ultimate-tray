import csv
import logging
from pathlib import Path

from app.logging import setup_logger

logger = logging.getLogger(__name__)


class BatteryLogCleaner:
    LOG_FILES: tuple[str, str] = (
        "battery_wired_charge_log.csv",
        "battery_wireless_charge_log.csv",
    )

    def __init__(self, log_dir: Path) -> None:
        self.log_dir = log_dir

    def _clean_file(self, input_file: Path) -> Path | None:
        if not input_file.exists():
            return None

        output_file = input_file.with_name(input_file.stem + "_cleaned.csv")

        with input_file.open(
            "r",
            newline="",
            encoding="utf-8",
        ) as file:
            rows = list(csv.DictReader(file))

        if not rows:
            logger.info("%s: empty file.", input_file.name)
            return None

        cleaned_rows: list[dict[str, str]] = []

        for index, row in enumerate(rows):
            current_state = (row["battery_percent"], row["is_charging"])

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

            if current_state != previous_state or current_state != next_state:
                cleaned_rows.append(row)

        with output_file.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=["timestamp", "battery_percent", "is_charging"],
            )

            writer.writeheader()
            writer.writerows(cleaned_rows)

        logger.info("%s: %s original rows.", input_file.name, len(rows))

        logger.info("%s: %s preserved rows.", input_file.name, len(cleaned_rows))

        logger.info("%s: created.", output_file.name)

        return output_file

    def clean(self) -> None:
        cleaned_files = 0

        for filename in self.LOG_FILES:
            input_file = self.log_dir / filename

            if self._clean_file(input_file) is not None:
                cleaned_files += 1

        if cleaned_files == 0:
            logger.info("No battery log found.")


def main() -> None:
    setup_logger(logging.DEBUG)

    BatteryLogCleaner(Path(__file__).resolve().parent).clean()


if __name__ == "__main__":
    main()
