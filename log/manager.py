from pathlib import Path
from threading import Thread

from .battery_logger import BatteryLogger
from .clean_battery_log import BatteryLogCleaner
from .analyze_charge import ChargeAnalyzer


class LogManager:
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir

        self.logger: BatteryLogger | None = None
        self.logger_thread: Thread | None = None

        self.cleaner: BatteryLogCleaner = BatteryLogCleaner(self.log_dir, verbose=False)

        self.analyzer: ChargeAnalyzer = ChargeAnalyzer(self.log_dir, verbose=False)


    def is_logger_running(self) -> bool:
        return self.logger_thread is not None and self.logger_thread.is_alive()


    def clean_battery_logs(self) -> None:
        try:
            self.cleaner.clean()
        except Exception as error:
            print(f"Failed to clean battery logs: {error}", flush=True)


    def analyze_charge_logs(self) -> None:
        try:
            self.analyzer.analyze()
        except Exception as error:
            print(f"Failed to analyze battery logs: {error}", flush=True)


    def start_logger(self) -> bool:
        if self.is_logger_running():
            return False

        self.logger = BatteryLogger(self.log_dir, verbose=False)

        self.logger_thread = Thread(target=self.logger.run, daemon=True, name="BatteryLogger")

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

        # Clean raw logs before analysis to generate a normalized dataset.
        self.clean_battery_logs()

        # Update charge model with the latest charging session.
        self.analyze_charge_logs()

        return True