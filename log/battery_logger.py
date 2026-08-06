import csv
import signal
import time
import traceback
from datetime import datetime
from pathlib import Path

from openrazer.client import DeviceManager


class BatteryLogger:
    def __init__(
        self,
        log_dir: Path,
        interval_seconds: int = 1,
        verbose: bool = False,
    ):
        self.log_dir = log_dir

        self.interval_seconds = interval_seconds

        self.verbose = verbose

        self.running = True


    def _log(self, message: str) -> None:
        if self.verbose:
            print(message, flush=True)


    def _find_viper(
        self,
        device_manager: DeviceManager,
    ) -> object | None:
        return next(
            (
                device
                for device in device_manager.devices
                if device.name.startswith("Razer Viper Ultimate")
            ),
            None,
        )


    def _get_log_file(
        self,
        mouse,
    ) -> Path:
        filename = (
            "battery_wired_charge_log.csv"
            if "(Wired)" in mouse._name
            else "battery_wireless_charge_log.csv"
        )

        return self.log_dir / filename


    def _initialize_log_file(
        self,
        log_file: Path,
    ) -> None:
        with log_file.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "battery_percent", "is_charging"])


    def stop(self) -> None:
        self.running = False


    def _request_stop(self, signum, frame) -> None:
        if self.running:
            self._log("\nStopping battery logger...")
            self.stop()


    def run(self) -> None:
        signal.signal(signal.SIGINT, self._request_stop)

        signal.signal(signal.SIGTERM, self._request_stop)

        device_manager = DeviceManager()

        mouse = self._find_viper(device_manager)

        if mouse is None:
            print("Mouse not detected.", flush=True)
            return

        log_file = self._get_log_file(mouse)

        self._initialize_log_file(log_file)

        self._log(f"Detected mode: {mouse._name}")

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

                    writer.writerow(
                        [
                            timestamp,
                            battery,
                            is_charging,
                        ]
                    )

            except Exception:
                traceback.print_exc()

            time.sleep(self.interval_seconds)

        self._log("Battery logger stopped.")


def main() -> None:
    BatteryLogger(Path(__file__).resolve().parent, verbose=True).run()


if __name__ == "__main__":
    main()