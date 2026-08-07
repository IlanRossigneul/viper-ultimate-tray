from pathlib import Path


class BatteryLogDeleter:
    LOG_FILES: tuple[str, ...] = (
        "battery_wired_charge_log.csv",
        "battery_wireless_charge_log.csv",
        "battery_wired_charge_log_cleaned.csv",
        "battery_wireless_charge_log_cleaned.csv",
    )


    def __init__(self, log_dir: Path, verbose: bool = False):
        self.log_dir = log_dir

        self.verbose = verbose


    def _log(self, message: str) -> None:
        if self.verbose:
            print(message, flush=True)


    def delete(self) -> None:
        deleted_files = 0

        for filename in self.LOG_FILES:
            log_file = self.log_dir / filename

            if not log_file.exists():
                continue

            log_file.unlink()

            deleted_files += 1

            self._log(f"Deleted battery log: {filename}")

        if deleted_files == 0:
            self._log("No battery log found to delete.")
        else:
            self._log(f"Deleted {deleted_files} battery log file(s).")


def main() -> None:
    BatteryLogDeleter(Path(__file__).resolve().parent, verbose=True).delete()


if __name__ == "__main__":
    main()