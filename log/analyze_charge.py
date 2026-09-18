import csv
import json
import math
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ChargeEntry = dict[str, datetime | float | bool]

EMPTY_CHARGE_LEVEL = 0


class ChargeAnalyzer:
    LOG_FILES: tuple[tuple[str, Path], ...] = (
        ("wired", Path("battery_wired_charge_log_cleaned.csv")),
        ("wireless", Path("battery_wireless_charge_log_cleaned.csv")),
    )

    def __init__(
        self,
        log_dir: Path,
        verbose: bool = False,
    ) -> None:
        self.log_dir = log_dir

        self.verbose = verbose

        self.model_file = log_dir / "battery_charge_model.json"

        self.samples_file = log_dir / "battery_charge_samples.json"

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message, flush=True)

    def _load_charge_log(self, input_file: Path) -> list[ChargeEntry]:
        if not input_file.exists():
            raise FileNotFoundError(f"File not found: {input_file.name}")

        with input_file.open(
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

    def _get_charging_entries(self, entries: list[ChargeEntry]) -> list[ChargeEntry]:
        charging_entries = [entry for entry in entries if entry["is_charging"]]

        if not charging_entries:
            raise ValueError("No charging session found.")

        return charging_entries

    def _get_charge_level(self, entry: ChargeEntry) -> int | None:
        battery_percent = entry["battery_percent"]

        if entry["is_charging"] and battery_percent == EMPTY_CHARGE_LEVEL:
            return None

        return math.floor(battery_percent)

    def _build_charge_transitions(self, entries: list[ChargeEntry]) -> dict[str, int]:
        charging_entries = self._get_charging_entries(entries)

        level_durations: defaultdict[str, list[int]] = defaultdict(list)

        previous_entry: ChargeEntry | None = None
        previous_level: int | None = None
        first_level: int | None = None

        for entry in charging_entries:
            current_level = self._get_charge_level(entry)

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
                    first_level != EMPTY_CHARGE_LEVEL and previous_level == first_level
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

    def _load_samples(self) -> dict[str, Any]:
        if not self.samples_file.exists():
            return {"wired": [], "wireless": []}

        with self.samples_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    def _load_model(self) -> dict[str, Any]:
        if not self.model_file.exists():
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

        with self.model_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    def _calculate_average_transitions(
        self,
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

    def _sample_already_exists(
        self,
        samples: list[dict[str, Any]],
        transitions: dict[str, int],
    ) -> bool:
        if not samples:
            return False

        return samples[-1]["transitions"] == transitions

    def _save_model(self, data: dict[str, Any]) -> None:
        with self.model_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=4,
            )

            file.write("\n")

    def _save_samples(self, data: dict[str, Any]) -> None:
        with self.samples_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=4,
            )

            file.write("\n")

    def _format_duration(self, seconds: int) -> str:
        hours, remainder = divmod(seconds, 3600)

        minutes, seconds = divmod(remainder, 60)

        if hours:
            return f"{hours} h {minutes:02d} min {seconds:02d} s"

        return f"{minutes} min {seconds:02d} s"

    def _analyze_mode(
        self,
        mode: str,
        input_file: Path,
        samples: dict[str, Any],
        model: dict[str, Any],
    ) -> None:
        self._log(f"\nAnalyze {mode}...")

        entries = self._load_charge_log(input_file)

        try:
            transitions = self._build_charge_transitions(entries)
        except ValueError as error:
            self._log(f"{mode}: {error}")
            return

        if self._sample_already_exists(samples[mode], transitions):
            self._log("Sample already exists.")
            return

        now = datetime.now().astimezone().isoformat(timespec="seconds")

        samples[mode].append({"created_at": now, "transitions": transitions})

        model[mode]["average"] = self._calculate_average_transitions(samples[mode])

        model[mode]["statistics"]["sample_count"] = len(samples[mode])

        model[mode]["statistics"]["last_updated"] = now

        self._log(f"Sample added: {model[mode]['statistics']['sample_count']}")

        self._log(f"Average model {mode}:")

        for level, seconds in model[mode]["average"].items():
            self._log(f"{level:>2} % : {self._format_duration(seconds)}")

    def analyze(self) -> None:
        samples = self._load_samples()
        model = self._load_model()

        analyzed = False

        for mode, filename in self.LOG_FILES:
            input_file = self.log_dir / filename

            if not input_file.exists():
                continue

            self._analyze_mode(
                mode,
                input_file,
                samples,
                model,
            )

            analyzed = True

        if not analyzed:
            self._save_samples(samples)
            self._save_model(model)

            self._log("No cleaned battery log found.")

            return

        self._save_samples(samples)
        self._save_model(model)


def main() -> None:
    try:
        ChargeAnalyzer(Path(__file__).resolve().parent, verbose=True).analyze()
    except Exception:  # noqa: BLE001
        traceback.print_exc()


if __name__ == "__main__":
    main()
