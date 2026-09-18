import logging
import shutil
from datetime import datetime
from pathlib import Path

from app.logging import setup_logger

logger = logging.getLogger(__name__)


class BatteryLogArchiver:
    LOG_FILES: tuple[str, ...] = (
        "battery_wired_charge_log.csv",
        "battery_wireless_charge_log.csv",
    )

    ARCHIVE_DIRECTORY: str = "archive"

    def __init__(self, log_dir: Path) -> None:
        self.log_dir = log_dir

    def _create_archive_directory(self) -> Path:
        # Archive directory names intentionally use local wall-clock time.
        archive_directory = (
            self.log_dir
            / self.ARCHIVE_DIRECTORY
            / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # noqa: DTZ005
        )

        archive_directory.mkdir(parents=True, exist_ok=True)

        return archive_directory

    def archive(self) -> None:
        archive_directory: Path | None = None

        archived_files = 0

        for filename in self.LOG_FILES:
            input_file = self.log_dir / filename

            if not input_file.exists():
                continue

            if archive_directory is None:
                archive_directory = self._create_archive_directory()

            output_file = archive_directory / filename

            shutil.copy2(input_file, output_file)

            archived_files += 1

            logger.info("%s/%s: archived.", archive_directory, filename)

        if archived_files == 0:
            logger.info("No battery log found.")


def main() -> None:
    setup_logger(logging.DEBUG)

    BatteryLogArchiver(Path(__file__).resolve().parent).archive()


if __name__ == "__main__":
    main()
