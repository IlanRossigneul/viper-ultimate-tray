import csv
import time
from datetime import datetime
from pathlib import Path

from openrazer.client import DeviceManager


class BatteryLogger:
    def __init__(
        self,
        log_dir: Path,
        interval_seconds: int = 1,
    ):
        self.log_dir = log_dir
        self.interval_seconds = interval_seconds

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

    def run(self) -> None:
        device_manager = DeviceManager()

        mouse = self._find_viper(device_manager)

        if mouse is None:
            print("Mouse not detected.", flush=True)
            return

        log_file = self._get_log_file(mouse)

        self._initialize_log_file(log_file)

        print(f"Detected mode: {mouse._name}", flush=True)

        print(f"Log file: {log_file.name}", flush=True)

        print(f"Logging every {self.interval_seconds} second(s).", flush=True)

        while True:
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

            except Exception as error:
                print(f"Unable to read mouse state: {error}", flush=True)

            time.sleep(self.interval_seconds)


if __name__ == "__main__":
    BatteryLogger(Path(__file__).resolve().parent).run()