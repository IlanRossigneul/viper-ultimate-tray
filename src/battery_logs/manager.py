import logging
from pathlib import Path
from threading import Thread

from .analyze_charge import ChargeAnalyzer
from .archive_battery_log import BatteryLogArchiver
from .battery_logger import BatteryLogger
from .clean_battery_log import BatteryLogCleaner
from .delete_battery_log import BatteryLogDeleter

logger = logging.getLogger(__name__)


class LogManager:
    def __init__(self, log_dir: Path) -> None:
        self.log_dir = log_dir

        self.logger: BatteryLogger | None = None
        self.logger_thread: Thread | None = None

        self.cleaner: BatteryLogCleaner = BatteryLogCleaner(self.log_dir)

        self.analyzer: ChargeAnalyzer = ChargeAnalyzer(self.log_dir)

        self.archiver: BatteryLogArchiver = BatteryLogArchiver(self.log_dir)

        self.deleter: BatteryLogDeleter = BatteryLogDeleter(self.log_dir)

    def is_logger_running(self) -> bool:
        return self.logger_thread is not None and self.logger_thread.is_alive()

    def clean_battery_logs(self) -> bool:
        try:
            self.cleaner.clean()
            return True
        except Exception as error:  # noqa: BLE001
            logger.error(
                "Failed to clean battery logs: %s",
                error,
            )
            return False

    def analyze_charge_logs(self) -> bool:
        try:
            self.analyzer.analyze()
            return True
        except Exception as error:  # noqa: BLE001
            logger.error(
                "Failed to analyze battery logs: %s",
                error,
            )
            return False

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
        if not self.clean_battery_logs():
            return

        if not self.analyze_charge_logs():
            return

        if not self.archive_battery_logs():
            return

        if not self.delete_battery_logs():
            return

    def start_logger(self) -> bool:
        if self.is_logger_running():
            return False

        self.logger = BatteryLogger(self.log_dir)

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
