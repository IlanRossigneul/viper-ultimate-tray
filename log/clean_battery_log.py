import csv
from pathlib import Path


class BatteryLogCleaner:
    LOG_FILES: tuple[str, str] = (
        "battery_wired_charge_log.csv",
        "battery_wireless_charge_log.csv",
    )

    def __init__(
        self,
        log_dir: Path,
        verbose: bool = False,
    ) -> None:
        self.log_dir = log_dir

        self.verbose = verbose

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message, flush=True)

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
            self._log(f"{input_file.name}: empty file.")
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

        self._log(f"{input_file.name}: {len(rows)} original rows.")

        self._log(f"{input_file.name}: {len(cleaned_rows)} preserved rows.")

        self._log(f"{output_file.name}: created.")

        return output_file

    def clean(self) -> None:
        cleaned_files = 0

        for filename in self.LOG_FILES:
            input_file = self.log_dir / filename

            if self._clean_file(input_file) is not None:
                cleaned_files += 1

        if cleaned_files == 0:
            self._log("No battery log found.")


def main() -> None:
    BatteryLogCleaner(Path(__file__).resolve().parent, verbose=True).clean()


if __name__ == "__main__":
    main()
