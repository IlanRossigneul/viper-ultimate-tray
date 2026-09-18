import logging
from pathlib import Path

from app.logging import setup_logger

logger = logging.getLogger(__name__)


class BatteryLogDeleter:
    LOG_FILES: tuple[str, ...] = (
        "battery_wired_charge_log.csv",
        "battery_wireless_charge_log.csv",
        "battery_wired_charge_log_cleaned.csv",
        "battery_wireless_charge_log_cleaned.csv",
    )

    def __init__(self, log_dir: Path) -> None:
        self.log_dir = log_dir

    def delete(self) -> None:
        deleted_files = 0

        for filename in self.LOG_FILES:
            log_file = self.log_dir / filename

            if not log_file.exists():
                continue

            log_file.unlink()

            deleted_files += 1

            logger.info("Deleted battery log: %s", filename)

        if deleted_files == 0:
            logger.info("No battery log found to delete.")
        else:
            logger.info("Deleted %s battery log file(s).", deleted_files)


def main() -> None:
    setup_logger(logging.DEBUG)

    BatteryLogDeleter(Path(__file__).resolve().parent).delete()


if __name__ == "__main__":
    main()
