import csv
import json
import logging
import math
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any

ChargeEntry = dict[str, datetime | float | bool]

EMPTY_CHARGE_LEVEL = 0

logger = logging.getLogger(__name__)


class ChargeAnalysisResult(Enum):
    NO_NEW_SAMPLE = auto()
    NEW_SAMPLE_ADDED = auto()


class ChargeAnalyzer:
    LOG_FILES: tuple[tuple[str, Path], ...] = (
        ("wired", Path("battery_wired_charge_log.csv")),
        ("wireless", Path("battery_wireless_charge_log.csv")),
    )

    def __init__(
        self,
        log_dir: Path,
        on_samples: Callable[[dict[str, Any]], None] | None = None,
        on_model: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.log_dir = log_dir

        self.on_samples = on_samples
        self.on_model = on_model

        self.model_file = log_dir / "battery_charge_model.json"

        self.samples_file = log_dir / "battery_charge_samples.json"

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

    def _get_charge_level(self, entry: ChargeEntry) -> int | None:
        battery_percent = entry["battery_percent"]

        if entry["is_charging"] and battery_percent == EMPTY_CHARGE_LEVEL:
            return None

        return math.floor(battery_percent)

    def _build_charge_transitions(self, entries: list[ChargeEntry]) -> dict[str, int]:
        if not any(entry["is_charging"] for entry in entries):
            raise ValueError("No charging session found.")

        level_durations: defaultdict[str, list[int]] = defaultdict(list)

        previous_level: int | None = None
        first_level: int | None = None
        charging_started_at: datetime | None = None
        accumulated_duration = 0

        for entry in entries:
            current_level = self._get_charge_level(entry)

            if current_level is None:
                continue

            if not entry["is_charging"]:
                if charging_started_at is not None:
                    accumulated_duration += int(
                        (entry["timestamp"] - charging_started_at).total_seconds()
                    )
                    charging_started_at = None

                continue

            if previous_level is None:
                previous_level = current_level
                first_level = current_level
                charging_started_at = entry["timestamp"]
                continue

            assert first_level is not None

            if charging_started_at is None:
                charging_started_at = entry["timestamp"]
                continue

            if current_level > previous_level:
                assert charging_started_at is not None

                accumulated_duration += int(
                    (entry["timestamp"] - charging_started_at).total_seconds()
                )

                is_initial_partial_transition = (
                    first_level != EMPTY_CHARGE_LEVEL and previous_level == first_level
                )

                if not is_initial_partial_transition:
                    level_durations[str(previous_level)].append(accumulated_duration)

                previous_level = current_level
                charging_started_at = entry["timestamp"]
                accumulated_duration = 0

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

    def load_samples(self) -> dict[str, Any]:
        return self._load_samples()

    def load_model(self) -> dict[str, Any]:
        return self._load_model()

    def _rebuild_mode_model(
        self,
        mode: str,
        samples: dict[str, Any],
        model: dict[str, Any],
    ) -> None:
        mode_samples = samples.get(mode, [])

        model[mode] = {
            "statistics": {
                "sample_count": len(mode_samples),
                "last_updated": datetime.now()
                .astimezone()
                .isoformat(timespec="seconds"),
            },
            "average": self._calculate_average_transitions(mode_samples),
        }

    def update_sample(
        self,
        mode: str,
        created_at: str,
        transitions: dict[str, int],
    ) -> None:
        samples = self._load_samples()

        for sample in samples.get(mode, []):
            if sample["created_at"] == created_at:
                sample["transitions"] = transitions
                break
        else:
            return

        model = self._load_model()

        self._rebuild_mode_model(
            mode,
            samples,
            model,
        )

        self._save_samples(samples)
        self._save_model(model)

        self._notify_data(samples, model)

    def delete_sample(
        self,
        mode: str,
        created_at: str,
    ) -> None:
        samples = self._load_samples()

        mode_samples = samples.get(mode, [])

        for index, sample in enumerate(mode_samples):
            if sample["created_at"] == created_at:
                del mode_samples[index]
                break
        else:
            return

        model = self._load_model()

        self._rebuild_mode_model(
            mode,
            samples,
            model,
        )

        self._save_samples(samples)
        self._save_model(model)

        self._notify_data(samples, model)

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
    ) -> ChargeAnalysisResult:
        logger.info("Analyze %s...", mode)

        entries = self._load_charge_log(input_file)

        try:
            transitions = self._build_charge_transitions(entries)
        except ValueError as error:
            logger.warning("%s: %s", mode, error)
            return ChargeAnalysisResult.NO_NEW_SAMPLE

        if self._sample_already_exists(samples[mode], transitions):
            logger.info("Sample already exists.")
            return ChargeAnalysisResult.NO_NEW_SAMPLE

        now = datetime.now().astimezone().isoformat(timespec="seconds")

        samples[mode].append({"created_at": now, "transitions": transitions})

        model[mode]["average"] = self._calculate_average_transitions(samples[mode])

        model[mode]["statistics"]["sample_count"] = len(samples[mode])

        model[mode]["statistics"]["last_updated"] = now

        logger.info(
            "Sample added: %s",
            model[mode]["statistics"]["sample_count"],
        )

        logger.debug("Average model %s:", mode)

        for level, seconds in model[mode]["average"].items():
            logger.debug(
                "%2s %% : %s",
                level,
                self._format_duration(seconds),
            )

        return ChargeAnalysisResult.NEW_SAMPLE_ADDED

    def _notify_data(
        self,
        samples: dict[str, Any],
        model: dict[str, Any],
    ) -> None:
        if self.on_samples is not None:
            self.on_samples(samples)

        if self.on_model is not None:
            self.on_model(model)

    def analyze(self) -> ChargeAnalysisResult:
        samples = self._load_samples()
        model = self._load_model()

        result = ChargeAnalysisResult.NO_NEW_SAMPLE

        for mode, filename in self.LOG_FILES:
            input_file = self.log_dir / filename

            if not input_file.exists():
                continue

            mode_result = self._analyze_mode(
                mode,
                input_file,
                samples,
                model,
            )

            if mode_result is ChargeAnalysisResult.NEW_SAMPLE_ADDED:
                result = ChargeAnalysisResult.NEW_SAMPLE_ADDED

        self._save_samples(samples)
        self._save_model(model)

        if result is ChargeAnalysisResult.NO_NEW_SAMPLE:
            logger.info("No new sample added.")

        self._notify_data(samples, model)

        return result
