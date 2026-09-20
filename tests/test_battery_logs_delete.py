from pathlib import Path

from battery_logs.delete_battery_log import BatteryLogDeleter

LOG_FILENAMES = (
    "battery_wired_charge_log.csv",
    "battery_wireless_charge_log.csv",
)


def _write_log(log_dir: Path, filename: str, content: str) -> Path:
    log_file = log_dir / filename
    log_file.write_text(content, encoding="utf-8")

    return log_file


def test_delete_wired_log(tmp_path: Path) -> None:
    input_file = _write_log(
        tmp_path,
        "battery_wired_charge_log.csv",
        "content\n",
    )

    BatteryLogDeleter(tmp_path).delete()

    assert not input_file.exists()


def test_delete_wireless_log(tmp_path: Path) -> None:
    input_file = _write_log(
        tmp_path,
        "battery_wireless_charge_log.csv",
        "content\n",
    )

    BatteryLogDeleter(tmp_path).delete()

    assert not input_file.exists()


def test_delete_all_battery_logs(tmp_path: Path) -> None:
    log_files = [
        _write_log(
            tmp_path,
            filename,
            f"{filename}\n",
        )
        for filename in LOG_FILENAMES
    ]

    BatteryLogDeleter(tmp_path).delete()

    for log_file in log_files:
        assert not log_file.exists()


def test_delete_preserves_unrelated_files(tmp_path: Path) -> None:
    unrelated_files = [
        tmp_path / "battery_charge_model.json",
        tmp_path / "battery_charge_samples.json",
        tmp_path / "manager.py",
        tmp_path / "other_file.txt",
    ]

    for file in unrelated_files:
        file.write_text("content\n", encoding="utf-8")

    BatteryLogDeleter(tmp_path).delete()

    for file in unrelated_files:
        assert file.exists()
        assert file.read_text(encoding="utf-8") == "content\n"


def test_delete_does_nothing_when_no_log_exists(tmp_path: Path) -> None:
    BatteryLogDeleter(tmp_path).delete()

    assert not any(tmp_path.iterdir())


def test_delete_keeps_empty_logs_removed(tmp_path: Path) -> None:
    log_files = [_write_log(tmp_path, filename, "") for filename in LOG_FILENAMES]

    BatteryLogDeleter(tmp_path).delete()

    for log_file in log_files:
        assert not log_file.exists()
