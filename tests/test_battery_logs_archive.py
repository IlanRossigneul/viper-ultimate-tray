from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from battery_logs.archive_battery_log import BatteryLogArchiver

FIXED_DATETIME = datetime(2026, 9, 19, 20, 15, 30)


def _write_log(log_dir: Path, filename: str, content: str) -> Path:
    log_file = log_dir / filename
    log_file.write_text(content, encoding="utf-8")

    return log_file


def test_archive_wired_log(tmp_path: Path) -> None:
    content = "timestamp,battery_percent,is_charging\n"
    input_file = _write_log(
        tmp_path,
        "battery_wired_charge_log.csv",
        content,
    )

    archiver = BatteryLogArchiver(tmp_path)

    with patch("battery_logs.archive_battery_log.datetime") as datetime_mock:
        datetime_mock.now.return_value = FIXED_DATETIME
        archiver.archive()

    archive_file = (
        tmp_path / "archive" / "2026-09-19_20-15-30" / "battery_wired_charge_log.csv"
    )

    assert archive_file.exists()
    assert archive_file.read_text(encoding="utf-8") == content
    assert input_file.exists()
    assert input_file.read_text(encoding="utf-8") == content


def test_archive_wireless_log(tmp_path: Path) -> None:
    content = "timestamp,battery_percent,is_charging\n"
    input_file = _write_log(
        tmp_path,
        "battery_wireless_charge_log.csv",
        content,
    )

    archiver = BatteryLogArchiver(tmp_path)

    with patch("battery_logs.archive_battery_log.datetime") as datetime_mock:
        datetime_mock.now.return_value = FIXED_DATETIME
        archiver.archive()

    archive_file = (
        tmp_path / "archive" / "2026-09-19_20-15-30" / "battery_wireless_charge_log.csv"
    )

    assert archive_file.exists()
    assert archive_file.read_text(encoding="utf-8") == content
    assert input_file.exists()
    assert input_file.read_text(encoding="utf-8") == content


def test_archive_both_logs_in_same_directory(tmp_path: Path) -> None:
    wired_content = (
        "timestamp,battery_percent,is_charging\n2026-09-19T20:00:00+02:00,42.3,True\n"
    )
    wireless_content = (
        "timestamp,battery_percent,is_charging\n2026-09-19T20:00:00+02:00,84.7,True\n"
    )

    _write_log(
        tmp_path,
        "battery_wired_charge_log.csv",
        wired_content,
    )
    _write_log(
        tmp_path,
        "battery_wireless_charge_log.csv",
        wireless_content,
    )

    archiver = BatteryLogArchiver(tmp_path)

    with patch("battery_logs.archive_battery_log.datetime") as datetime_mock:
        datetime_mock.now.return_value = FIXED_DATETIME
        archiver.archive()

    archive_directory = tmp_path / "archive" / "2026-09-19_20-15-30"

    assert archive_directory.is_dir()

    assert (archive_directory / "battery_wired_charge_log.csv").read_text(
        encoding="utf-8"
    ) == wired_content

    assert (archive_directory / "battery_wireless_charge_log.csv").read_text(
        encoding="utf-8"
    ) == wireless_content

    assert len(list((tmp_path / "archive").iterdir())) == 1


def test_archive_empty_logs(tmp_path: Path) -> None:
    wired_file = _write_log(
        tmp_path,
        "battery_wired_charge_log.csv",
        "",
    )
    wireless_file = _write_log(
        tmp_path,
        "battery_wireless_charge_log.csv",
        "",
    )

    archiver = BatteryLogArchiver(tmp_path)

    with patch("battery_logs.archive_battery_log.datetime") as datetime_mock:
        datetime_mock.now.return_value = FIXED_DATETIME
        archiver.archive()

    archive_directory = tmp_path / "archive" / "2026-09-19_20-15-30"

    assert archive_directory.is_dir()
    assert (archive_directory / wired_file.name).read_text(encoding="utf-8") == ""
    assert (archive_directory / wireless_file.name).read_text(encoding="utf-8") == ""


def test_archive_preserves_large_log_content(tmp_path: Path) -> None:
    content = "timestamp,battery_percent,is_charging\n" + "".join(
        f"2026-09-19T20:00:{index % 60:02d}+02:00,{index % 100}.5,True\n"
        for index in range(5000)
    )

    input_file = _write_log(
        tmp_path,
        "battery_wired_charge_log.csv",
        content,
    )

    archiver = BatteryLogArchiver(tmp_path)

    with patch("battery_logs.archive_battery_log.datetime") as datetime_mock:
        datetime_mock.now.return_value = FIXED_DATETIME
        archiver.archive()

    archive_file = (
        tmp_path / "archive" / "2026-09-19_20-15-30" / "battery_wired_charge_log.csv"
    )

    assert archive_file.read_text(encoding="utf-8") == content
    assert input_file.read_text(encoding="utf-8") == content


def test_archive_does_nothing_when_no_log_exists(tmp_path: Path) -> None:
    archiver = BatteryLogArchiver(tmp_path)

    with patch("battery_logs.archive_battery_log.datetime") as datetime_mock:
        datetime_mock.now.return_value = FIXED_DATETIME
        archiver.archive()

    assert not (tmp_path / "archive").exists()


def test_archive_directory_uses_expected_timestamp_format(
    tmp_path: Path,
) -> None:
    _write_log(
        tmp_path,
        "battery_wired_charge_log.csv",
        "content\n",
    )

    archiver = BatteryLogArchiver(tmp_path)

    with patch("battery_logs.archive_battery_log.datetime") as datetime_mock:
        datetime_mock.now.return_value = FIXED_DATETIME
        archiver.archive()

    archive_directory = tmp_path / "archive" / "2026-09-19_20-15-30"

    assert archive_directory.is_dir()
