import csv
import logging
import signal
import time
from datetime import datetime
from pathlib import Path

from openrazer.client.devices.mice import RazerMouse

from app.logging import setup_logger
from razer.device import create_device_manager, find_viper_ultimate_device

logger = logging.getLogger(__name__)


class BatteryLogger:
    def __init__(
        self,
        log_dir: Path,
        interval_seconds: int = 1,
    ) -> None:
        self.log_dir = log_dir

        self.interval_seconds = interval_seconds

        self.running = True

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

    def stop(self) -> None:
        self.running = False

    def _request_stop(self, _signum, _frame) -> None:
        if self.running:
            logger.info("Stopping battery logger...")
            self.stop()

    def run(self) -> None:
        device_manager = create_device_manager()

        mouse = find_viper_ultimate_device(device_manager)

        if mouse is None:
            logger.error("Mouse not detected.")
            return

        log_file = self._get_log_file(mouse)

        self._initialize_log_file(log_file)

        logger.info("Detected mode: %s", mouse.name)

        logger.info("Log file: %s", log_file.name)

        logger.info(
            "Logging every %s second(s).",
            self.interval_seconds,
        )

        while self.running:
            try:
                battery = mouse._dbus_interfaces["power"].getBattery()

                is_charging = mouse.is_charging

                timestamp = datetime.now().astimezone().isoformat(timespec="seconds")

                with log_file.open(
                    "a",
                    newline="",
                    encoding="utf-8",
                ) as file:
                    writer = csv.writer(file)

                    writer.writerow([timestamp, battery, is_charging])

            except Exception:
                logger.exception("Failed to log battery data.")

            time.sleep(self.interval_seconds)

        logger.info("Battery logger stopped.")


def main() -> None:
    setup_logger(logging.DEBUG)

    battery_logger = BatteryLogger(Path(__file__).resolve().parent)

    signal.signal(signal.SIGINT, battery_logger._request_stop)

    signal.signal(signal.SIGTERM, battery_logger._request_stop)

    battery_logger.run()


if __name__ == "__main__":
    main()
