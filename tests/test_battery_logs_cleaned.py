import csv
from pathlib import Path

from battery_logs.clean_battery_log import BatteryLogCleaner


def _write_log(
    log_file: Path,
    rows: list[list[str]],
) -> None:
    with log_file.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            ["timestamp", "battery_percent", "is_charging"],
        )

        writer.writerows(rows)


def _read_log(log_file: Path) -> list[list[str]]:
    with log_file.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.reader(file))


def test_clean_file_returns_none_when_file_does_not_exist(tmp_path):
    cleaner = BatteryLogCleaner(tmp_path)
    input_file = tmp_path / "battery_wireless_charge_log.csv"

    assert cleaner._clean_file(input_file) is None
    assert not input_file.with_name("battery_wireless_charge_log_cleaned.csv").exists()


def test_clean_file_returns_none_for_empty_log(tmp_path):
    cleaner = BatteryLogCleaner(tmp_path)
    input_file = tmp_path / "battery_wireless_charge_log.csv"

    _write_log(input_file, [])

    assert cleaner._clean_file(input_file) is None
    assert not input_file.with_name("battery_wireless_charge_log_cleaned.csv").exists()


def test_clean_file_preserves_single_row(tmp_path):
    cleaner = BatteryLogCleaner(tmp_path)
    input_file = tmp_path / "battery_wireless_charge_log.csv"

    _write_log(
        input_file,
        [
            ["2026-09-19T19:00:00+02:00", "42.5", "False"],
        ],
    )

    output_file = cleaner._clean_file(input_file)

    assert output_file is not None
    assert _read_log(output_file) == [
        ["timestamp", "battery_percent", "is_charging"],
        ["2026-09-19T19:00:00+02:00", "42.5", "False"],
    ]


def test_clean_file_preserves_first_and_last_occurrence_of_each_state(
    tmp_path,
):
    cleaner = BatteryLogCleaner(tmp_path)
    input_file = tmp_path / "battery_wireless_charge_log.csv"

    _write_log(
        input_file,
        [
            ["19:00:00", "42.5", "False"],
            ["19:00:01", "42.5", "False"],
            ["19:00:02", "42.5", "False"],
            ["19:00:03", "41.8", "False"],
            ["19:00:04", "41.8", "False"],
            ["19:00:05", "40.7", "False"],
            ["19:00:06", "40.7", "False"],
            ["19:00:07", "40.7", "False"],
        ],
    )

    output_file = cleaner._clean_file(input_file)

    assert output_file is not None
    assert _read_log(output_file) == [
        ["timestamp", "battery_percent", "is_charging"],
        ["19:00:00", "42.5", "False"],
        ["19:00:02", "42.5", "False"],
        ["19:00:03", "41.8", "False"],
        ["19:00:04", "41.8", "False"],
        ["19:00:05", "40.7", "False"],
        ["19:00:07", "40.7", "False"],
    ]


def test_clean_file_treats_charging_state_as_part_of_state(tmp_path):
    cleaner = BatteryLogCleaner(tmp_path)
    input_file = tmp_path / "battery_wireless_charge_log.csv"

    _write_log(
        input_file,
        [
            ["19:00:00", "98.0", "False"],
            ["19:00:01", "98.0", "False"],
            ["19:00:02", "98.0", "True"],
            ["19:00:03", "98.0", "True"],
            ["19:00:04", "98.0", "True"],
        ],
    )

    output_file = cleaner._clean_file(input_file)

    assert output_file is not None
    assert _read_log(output_file) == [
        ["timestamp", "battery_percent", "is_charging"],
        ["19:00:00", "98.0", "False"],
        ["19:00:01", "98.0", "False"],
        ["19:00:02", "98.0", "True"],
        ["19:00:04", "98.0", "True"],
    ]


def test_clean_file_preserves_separate_occurrences_of_same_state(
    tmp_path,
):
    cleaner = BatteryLogCleaner(tmp_path)
    input_file = tmp_path / "battery_wireless_charge_log.csv"

    _write_log(
        input_file,
        [
            ["19:00:00", "50.0", "False"],
            ["19:00:01", "50.0", "False"],
            ["19:00:02", "51.0", "False"],
            ["19:00:03", "51.0", "False"],
            ["19:00:04", "50.0", "False"],
            ["19:00:05", "50.0", "False"],
        ],
    )

    output_file = cleaner._clean_file(input_file)

    assert output_file is not None
    assert _read_log(output_file) == [
        ["timestamp", "battery_percent", "is_charging"],
        ["19:00:00", "50.0", "False"],
        ["19:00:01", "50.0", "False"],
        ["19:00:02", "51.0", "False"],
        ["19:00:03", "51.0", "False"],
        ["19:00:04", "50.0", "False"],
        ["19:00:05", "50.0", "False"],
    ]


def test_clean_file_preserves_raw_battery_values(tmp_path):
    cleaner = BatteryLogCleaner(tmp_path)
    input_file = tmp_path / "battery_wired_charge_log.csv"

    raw_value = "98.0392156862745"

    _write_log(
        input_file,
        [
            ["19:00:00", raw_value, "True"],
            ["19:00:01", raw_value, "True"],
            ["19:00:02", "97.6470588235294", "True"],
        ],
    )

    output_file = cleaner._clean_file(input_file)

    assert output_file is not None
    assert _read_log(output_file) == [
        ["timestamp", "battery_percent", "is_charging"],
        ["19:00:00", raw_value, "True"],
        ["19:00:01", raw_value, "True"],
        ["19:00:02", "97.6470588235294", "True"],
    ]


def test_clean_file_preserves_csv_structure(tmp_path):
    cleaner = BatteryLogCleaner(tmp_path)
    input_file = tmp_path / "battery_wireless_charge_log.csv"

    _write_log(
        input_file,
        [
            ["19:00:00", "42.5", "False"],
            ["19:00:01", "42.5", "False"],
        ],
    )

    output_file = cleaner._clean_file(input_file)

    assert output_file is not None
    assert output_file.name == "battery_wireless_charge_log_cleaned.csv"
    assert _read_log(output_file)[0] == [
        "timestamp",
        "battery_percent",
        "is_charging",
    ]


def test_clean_processes_existing_wired_and_wireless_logs(tmp_path):
    cleaner = BatteryLogCleaner(tmp_path)

    _write_log(
        tmp_path / "battery_wired_charge_log.csv",
        [
            ["19:00:00", "50.0", "True"],
            ["19:00:01", "50.0", "True"],
        ],
    )

    _write_log(
        tmp_path / "battery_wireless_charge_log.csv",
        [
            ["19:01:00", "40.0", "False"],
            ["19:01:01", "40.0", "False"],
        ],
    )

    cleaner.clean()

    assert (tmp_path / "battery_wired_charge_log_cleaned.csv").exists()
    assert (tmp_path / "battery_wireless_charge_log_cleaned.csv").exists()
