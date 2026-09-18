import csv
import signal
import time
import traceback
from datetime import datetime
from pathlib import Path

from openrazer.client.devices.mice import RazerMouse

from razer.device import create_device_manager, find_viper_ultimate_device


class BatteryLogger:
    def __init__(
        self,
        log_dir: Path,
        interval_seconds: int = 1,
        verbose: bool = False,
    ) -> None:
        self.log_dir = log_dir

        self.interval_seconds = interval_seconds

        self.verbose = verbose

        self.running = True

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message, flush=True)

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
            self._log("\nStopping battery logger...")
            self.stop()

    def run(self) -> None:
        device_manager = create_device_manager()

        mouse = find_viper_ultimate_device(device_manager)

        if mouse is None:
            print("Mouse not detected.", flush=True)
            return

        log_file = self._get_log_file(mouse)

        self._initialize_log_file(log_file)

        self._log(f"Detected mode: {mouse.name}")

        self._log(f"Log file: {log_file.name}")

        self._log(f"Logging every {self.interval_seconds} second(s).")

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

            except Exception:  # noqa: BLE001
                traceback.print_exc()

            time.sleep(self.interval_seconds)

        self._log("Battery logger stopped.")


def main() -> None:
    logger = BatteryLogger(Path(__file__).resolve().parent, verbose=True)

    signal.signal(signal.SIGINT, logger._request_stop)

    signal.signal(signal.SIGTERM, logger._request_stop)

    logger.run()


if __name__ == "__main__":
    main()
