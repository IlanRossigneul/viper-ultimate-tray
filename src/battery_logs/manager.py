import logging
from collections.abc import Callable
from pathlib import Path
from threading import Thread
from typing import Any

from .analyze_charge import ChargeAnalysisResult, ChargeAnalyzer
from .archive_battery_log import BatteryLogArchiver
from .battery_logger import BatteryLogEntry, BatteryLogger
from .delete_battery_log import BatteryLogDeleter

logger = logging.getLogger(__name__)


class LogManager:
    def __init__(
        self,
        log_dir: Path,
        on_started: Callable[[str, int], None] | None = None,
        on_entry: Callable[[BatteryLogEntry], None] | None = None,
        on_finished: Callable[[], None] | None = None,
        on_samples: Callable[[dict[str, Any]], None] | None = None,
        on_model: Callable[[dict[str, Any]], None] | None = None,
        on_session_changed: Callable[[str, str], None] | None = None,
    ) -> None:
        self.log_dir = log_dir

        self.on_started = on_started
        self.on_entry = on_entry
        self.on_finished = on_finished
        self.on_samples = on_samples
        self.on_model = on_model
        self.on_session_changed = on_session_changed

        self.logger: BatteryLogger | None = None
        self.logger_thread: Thread | None = None

        self.analyzer: ChargeAnalyzer = ChargeAnalyzer(
            self.log_dir,
            on_samples=self.on_samples,
            on_model=self.on_model,
        )

        self.archiver: BatteryLogArchiver = BatteryLogArchiver(self.log_dir)

        self.deleter: BatteryLogDeleter = BatteryLogDeleter(self.log_dir)

    def is_logger_running(self) -> bool:
        return self.logger_thread is not None and self.logger_thread.is_alive()

    def analyze_charge_logs(self) -> ChargeAnalysisResult:
        return self.analyzer.analyze()

    def load_charge_samples(self) -> dict[str, Any]:
        return self.analyzer.load_samples()

    def load_charge_model(self) -> dict[str, Any]:
        return self.analyzer.load_model()

    def update_charge_sample(
        self,
        mode: str,
        created_at: str,
        transitions: dict[str, int],
    ) -> None:
        self.analyzer.update_sample(
            mode,
            created_at,
            transitions,
        )

    def delete_charge_sample(
        self,
        mode: str,
        created_at: str,
    ) -> None:
        self.analyzer.delete_sample(
            mode,
            created_at,
        )

    def archive_battery_logs(self) -> bool:
        try:
            self.archiver.archive()
            return True
        except Exception as error:  # noqa: BLE001
            logger.error(
                "Failed to archive battery logs: %s",
                error,
            )
            return False

    def delete_battery_logs(self) -> bool:
        try:
            self.deleter.delete()
            return True
        except Exception as error:  # noqa: BLE001
            logger.error(
                "Failed to delete battery logs: %s",
                error,
            )
            return False

    def _process_battery_logs(self) -> None:
        try:
            result = self.analyze_charge_logs()
        except Exception:
            logger.exception("Failed to analyze battery logs.")
            return

        if (
            result is ChargeAnalysisResult.NEW_SAMPLE_ADDED
            and not self.archive_battery_logs()
        ):
            return

        if not self.delete_battery_logs():
            return

    def _handle_session_changed(
        self,
        old_mode: str,
        new_mode: str,
    ) -> None:
        self._process_battery_logs()

        if self.on_session_changed is not None:
            self.on_session_changed(old_mode, new_mode)

    def start_logger(self) -> bool:
        if self.is_logger_running():
            return False

        self.logger = BatteryLogger(
            self.log_dir,
            on_started=self.on_started,
            on_entry=self.on_entry,
            on_finished=self.on_finished,
            on_session_changed=self._handle_session_changed,
        )

        self.logger_thread = Thread(
            target=self.logger.run, daemon=True, name="BatteryLogger"
        )

        self.logger_thread.start()

        return True

    def stop_logger(self) -> bool:
        if not self.is_logger_running():
            return False

        assert self.logger is not None
        assert self.logger_thread is not None

        self.logger.stop()

        self.logger_thread.join()

        self.logger = None

        self.logger_thread = None

        self._process_battery_logs()

        return True
