import csv
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from openrazer.client.devices.mice import RazerMouse

from razer.device import create_device_manager, find_viper_ultimate_device

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class BatteryLogEntry:
    timestamp: str
    battery_percent: float
    is_charging: bool


class BatteryLogger:
    def __init__(
        self,
        log_dir: Path,
        interval_seconds: int = 1,
        on_started: Callable[[str, int], None] | None = None,
        on_start_failed: Callable[[str], None] | None = None,
        on_entry: Callable[[BatteryLogEntry], None] | None = None,
        on_finished: Callable[[], None] | None = None,
        on_session_changed: Callable[[str, str], None] | None = None,
    ) -> None:
        self.log_dir = log_dir

        self.interval_seconds = interval_seconds

        self.on_started = on_started
        self.on_start_failed = on_start_failed
        self.on_entry = on_entry
        self.on_finished = on_finished
        self.on_session_changed = on_session_changed

        self.running = True

        self.last_state: list[float | bool] | None = None
        self.last_entry: list[str | float | bool] | None = None

    def _get_log_file(self, mouse: RazerMouse) -> Path:
        filename = (
            "battery_wired_charge_log.csv"
            if "(Wired)" in mouse.name
            else "battery_wireless_charge_log.csv"
        )

        return self.log_dir / filename

    def _initialize_log_file(self, log_file: Path) -> None:
        with log_file.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "battery_percent", "is_charging"])

    def _write_entry(
        self,
        writer: csv.writer,
        entry: list[str | float | bool],
    ) -> None:
        writer.writerow(entry)

        if self.on_entry is not None:
            self.on_entry(
                BatteryLogEntry(
                    timestamp=str(entry[0]),
                    battery_percent=float(entry[1]),
                    is_charging=bool(entry[2]),
                )
            )

    def _process_entry(
        self,
        writer: csv.writer,
        entry: list[str | float | bool],
    ) -> None:
        current_state = [entry[1], entry[2]]

        if self.last_state is None:
            self._write_entry(writer, entry)

        elif current_state != self.last_state:
            assert self.last_entry is not None

            self._write_entry(writer, self.last_entry)
            self._write_entry(writer, entry)

        self.last_state = current_state
        self.last_entry = entry

    def _flush_last_entry(self, writer: csv.writer) -> None:
        if self.last_entry is not None:
            self._write_entry(writer, self.last_entry)

            self.last_entry = None
            self.last_state = None

    def stop(self) -> None:
        self.running = False

    def _find_mouse(self) -> RazerMouse | None:
        started_at = time.perf_counter()

        try:
            device_manager = create_device_manager()
            mouse = find_viper_ultimate_device(device_manager)
        except Exception:
            logger.exception("Failed to detect mouse.")
            logger.debug(
                "Battery logger mouse detection failed after %.2f ms.",
                (time.perf_counter() - started_at) * 1000,
            )
            return None

        logger.debug(
            "Battery logger mouse detection: %.2f ms (found=%s).",
            (time.perf_counter() - started_at) * 1000,
            mouse is not None,
        )
        return mouse

    def run(self) -> None:
        mouse = self._find_mouse()

        if mouse is None:
            logger.error("Mouse not detected.")

            if self.on_start_failed is not None:
                self.on_start_failed("mouse_not_detected")

            return

        current_mode = mouse.name
        log_file = self._get_log_file(mouse)

        self._initialize_log_file(log_file)

        logger.info("Detected mode: %s", current_mode)
        logger.info("Log file: %s", log_file.name)
        logger.info(
            "Checking battery state every %s second(s).",
            self.interval_seconds,
        )

        if self.on_started is not None:
            self.on_started(current_mode, self.interval_seconds)

        while self.running:
            with log_file.open(
                "a",
                newline="",
                encoding="utf-8",
            ) as file:
                writer = csv.writer(file)

                while self.running:
                    cycle_started_at = time.perf_counter()
                    current_mouse = self._find_mouse()

                    if current_mouse is None:
                        logger.debug(
                            "Battery logger poll: mode=mouse_not_found total=%.2f ms",
                            (time.perf_counter() - cycle_started_at) * 1000,
                        )
                        time.sleep(self.interval_seconds)
                        continue

                    if current_mouse.name != current_mode:
                        logger.debug(
                            "Battery logger poll: mode_changed=%s total=%.2f ms",
                            current_mouse.name,
                            (time.perf_counter() - cycle_started_at) * 1000,
                        )
                        mouse = current_mouse
                        break

                    mouse = current_mouse

                    try:
                        battery_started_at = time.perf_counter()
                        battery = mouse._dbus_interfaces["power"].getBattery()
                        battery_duration = time.perf_counter() - battery_started_at

                        charging_started_at = time.perf_counter()
                        is_charging = mouse.is_charging
                        charging_duration = time.perf_counter() - charging_started_at

                        timestamp = (
                            datetime.now().astimezone().isoformat(timespec="seconds")
                        )
                        entry = [timestamp, battery, is_charging]
                        self._process_entry(writer, entry)
                        file.flush()

                        logger.debug(
                            "Battery logger poll: mode=active battery=%.2f ms "
                            "charging=%.2f ms total=%.2f ms",
                            battery_duration * 1000,
                            charging_duration * 1000,
                            (time.perf_counter() - cycle_started_at) * 1000,
                        )
                    except Exception:
                        logger.exception("Failed to log battery data.")
                        logger.debug(
                            "Battery logger poll failed after %.2f ms.",
                            (time.perf_counter() - cycle_started_at) * 1000,
                        )

                    time.sleep(self.interval_seconds)

                self._flush_last_entry(writer)

            if not self.running:
                break

            new_mode = mouse.name

            logger.info(
                "Connection mode changed: %s -> %s",
                current_mode,
                new_mode,
            )

            if self.on_session_changed is not None:
                self.on_session_changed(current_mode, new_mode)

            if not self.running:
                break

            current_mode = new_mode
            log_file = self._get_log_file(mouse)
            self._initialize_log_file(log_file)

            logger.info(
                "Started new logging session: %s",
                new_mode,
            )

        if self.on_finished is not None:
            self.on_finished()

        logger.info("Battery logger stopped.")
