import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from battery_logs.analyze_charge import ChargeAnalyzer


def _write_log(
    log_file: Path,
    rows: list[list[str]],
) -> None:
    log_file.write_text(
        "timestamp,battery_percent,is_charging\n"
        + "\n".join(",".join(row) for row in rows)
        + "\n",
        encoding="utf-8",
    )


def _write_json(
    file: Path,
    data: dict,
) -> None:
    with file.open(
        "w",
        encoding="utf-8",
    ) as json_file:
        json.dump(data, json_file)


def test_load_charge_log_converts_csv_values(tmp_path):
    analyzer = ChargeAnalyzer(tmp_path)
    input_file = tmp_path / "battery_wireless_charge_log.csv"

    _write_log(
        input_file,
        [
            ["2026-09-19T19:00:00+02:00", "42.5", "True"],
            ["2026-09-19T19:01:00+02:00", "41.8", "False"],
        ],
    )

    entries = analyzer._load_charge_log(input_file)

    assert entries == [
        {
            "timestamp": datetime.fromisoformat("2026-09-19T19:00:00+02:00"),
            "battery_percent": 42.5,
            "is_charging": True,
        },
        {
            "timestamp": datetime.fromisoformat("2026-09-19T19:01:00+02:00"),
            "battery_percent": 41.8,
            "is_charging": False,
        },
    ]


def test_load_charge_log_raises_when_file_does_not_exist(tmp_path):
    analyzer = ChargeAnalyzer(tmp_path)

    with pytest.raises(
        FileNotFoundError,
        match="File not found: missing.csv",
    ):
        analyzer._load_charge_log(
            tmp_path / "missing.csv",
        )


def test_get_charge_level_floors_raw_battery_value(tmp_path):
    analyzer = ChargeAnalyzer(tmp_path)

    entry = {
        "timestamp": datetime.fromisoformat("2026-09-19T19:00:00+02:00"),
        "battery_percent": 98.0392156862745,
        "is_charging": True,
    }

    assert analyzer._get_charge_level(entry) == 98


def test_get_charge_level_returns_none_for_zero_percent_while_charging(
    tmp_path,
):
    analyzer = ChargeAnalyzer(tmp_path)

    entry = {
        "timestamp": datetime.fromisoformat("2026-09-19T19:00:00+02:00"),
        "battery_percent": 0.0,
        "is_charging": True,
    }

    assert analyzer._get_charge_level(entry) is None


def test_get_charge_level_preserves_zero_percent_when_not_charging(
    tmp_path,
):
    analyzer = ChargeAnalyzer(tmp_path)

    entry = {
        "timestamp": datetime.fromisoformat("2026-09-19T19:00:00+02:00"),
        "battery_percent": 0.0,
        "is_charging": False,
    }

    assert analyzer._get_charge_level(entry) == 0


def test_build_charge_transitions_calculates_duration_between_levels(
    tmp_path,
):
    analyzer = ChargeAnalyzer(tmp_path)

    entries = [
        {
            "timestamp": datetime.fromisoformat("2026-09-19T19:00:00+02:00"),
            "battery_percent": 40.0,
            "is_charging": True,
        },
        {
            "timestamp": datetime.fromisoformat("2026-09-19T19:01:30+02:00"),
            "battery_percent": 41.0,
            "is_charging": True,
        },
        {
            "timestamp": datetime.fromisoformat("2026-09-19T19:04:00+02:00"),
            "battery_percent": 42.0,
            "is_charging": True,
        },
        {
            "timestamp": datetime.fromisoformat("2026-09-19T19:07:15+02:00"),
            "battery_percent": 43.0,
            "is_charging": True,
        },
    ]

    assert analyzer._build_charge_transitions(entries) == {
        "41": 150,
        "42": 195,
    }


def test_build_charge_transitions_ignores_initial_partial_transition(
    tmp_path,
):
    analyzer = ChargeAnalyzer(tmp_path)

    entries = [
        {
            "timestamp": datetime.fromisoformat("2026-09-19T19:00:00+02:00"),
            "battery_percent": 40.0,
            "is_charging": True,
        },
        {
            "timestamp": datetime.fromisoformat("2026-09-19T19:01:30+02:00"),
            "battery_percent": 41.0,
            "is_charging": True,
        },
        {
            "timestamp": datetime.fromisoformat("2026-09-19T19:04:00+02:00"),
            "battery_percent": 42.0,
            "is_charging": True,
        },
    ]

    assert analyzer._build_charge_transitions(entries) == {
        "41": 150,
    }


def test_build_charge_transitions_ignores_non_increasing_levels(
    tmp_path,
):
    analyzer = ChargeAnalyzer(tmp_path)

    entries = [
        {
            "timestamp": datetime.fromisoformat("2026-09-19T19:00:00+02:00"),
            "battery_percent": 40.0,
            "is_charging": True,
        },
        {
            "timestamp": datetime.fromisoformat("2026-09-19T19:01:00+02:00"),
            "battery_percent": 41.0,
            "is_charging": True,
        },
        {
            "timestamp": datetime.fromisoformat("2026-09-19T19:02:00+02:00"),
            "battery_percent": 40.0,
            "is_charging": True,
        },
        {
            "timestamp": datetime.fromisoformat("2026-09-19T19:04:00+02:00"),
            "battery_percent": 42.0,
            "is_charging": True,
        },
    ]

    assert analyzer._build_charge_transitions(entries) == {
        "41": 180,
    }


def test_build_charge_transitions_ignores_zero_percent_while_charging(
    tmp_path,
):
    analyzer = ChargeAnalyzer(tmp_path)

    entries = [
        {
            "timestamp": datetime.fromisoformat("2026-09-19T19:00:00+02:00"),
            "battery_percent": 0.0,
            "is_charging": True,
        },
        {
            "timestamp": datetime.fromisoformat("2026-09-19T19:01:00+02:00"),
            "battery_percent": 1.0,
            "is_charging": True,
        },
        {
            "timestamp": datetime.fromisoformat("2026-09-19T19:03:00+02:00"),
            "battery_percent": 2.0,
            "is_charging": True,
        },
        {
            "timestamp": datetime.fromisoformat("2026-09-19T19:06:00+02:00"),
            "battery_percent": 3.0,
            "is_charging": True,
        },
    ]

    assert analyzer._build_charge_transitions(entries) == {
        "2": 180,
    }


def test_build_charge_transitions_raises_without_durations(tmp_path):
    analyzer = ChargeAnalyzer(tmp_path)

    entries = [
        {
            "timestamp": datetime.fromisoformat("2026-09-19T19:00:00+02:00"),
            "battery_percent": 40.0,
            "is_charging": True,
        },
    ]

    with pytest.raises(
        ValueError,
        match="No charge level durations found.",
    ):
        analyzer._build_charge_transitions(entries)


def test_load_samples_returns_empty_structure_when_file_is_missing(
    tmp_path,
):
    analyzer = ChargeAnalyzer(tmp_path)

    assert analyzer._load_samples() == {
        "wired": [],
        "wireless": [],
    }


def test_load_model_returns_default_structure_when_file_is_missing(
    tmp_path,
):
    analyzer = ChargeAnalyzer(tmp_path)

    assert analyzer._load_model() == {
        "wired": {
            "statistics": {
                "sample_count": 0,
                "last_updated": None,
            },
            "average": {},
        },
        "wireless": {
            "statistics": {
                "sample_count": 0,
                "last_updated": None,
            },
            "average": {},
        },
    }


def test_calculate_average_transitions_averages_each_level(tmp_path):
    analyzer = ChargeAnalyzer(tmp_path)

    samples = [
        {
            "created_at": "2026-09-19T19:00:00+02:00",
            "transitions": {
                "40": 100,
                "41": 200,
            },
        },
        {
            "created_at": "2026-09-19T20:00:00+02:00",
            "transitions": {
                "40": 200,
                "41": 300,
            },
        },
    ]

    assert analyzer._calculate_average_transitions(samples) == {
        "40": 150,
        "41": 250,
    }


def test_sample_already_exists_only_checks_latest_sample(tmp_path):
    analyzer = ChargeAnalyzer(tmp_path)

    samples = [
        {
            "created_at": "2026-09-19T19:00:00+02:00",
            "transitions": {
                "40": 100,
            },
        },
        {
            "created_at": "2026-09-19T20:00:00+02:00",
            "transitions": {
                "40": 200,
            },
        },
    ]

    assert analyzer._sample_already_exists(
        samples,
        {"40": 200},
    )

    assert not analyzer._sample_already_exists(
        samples,
        {"40": 100},
    )


def test_sample_already_exists_returns_false_without_samples(tmp_path):
    analyzer = ChargeAnalyzer(tmp_path)

    assert not analyzer._sample_already_exists(
        [],
        {"40": 100},
    )


def test_format_duration_formats_minutes_and_seconds(tmp_path):
    analyzer = ChargeAnalyzer(tmp_path)

    assert analyzer._format_duration(125) == "2 min 05 s"


def test_format_duration_formats_hours_minutes_and_seconds(tmp_path):
    analyzer = ChargeAnalyzer(tmp_path)

    assert analyzer._format_duration(3725) == "1 h 02 min 05 s"


def test_analyze_adds_sample_and_updates_model(tmp_path):
    analyzer = ChargeAnalyzer(tmp_path)

    input_file = tmp_path / "battery_wireless_charge_log.csv"

    _write_log(
        input_file,
        [
            ["2026-09-19T19:00:00+02:00", "40.0", "True"],
            ["2026-09-19T19:01:00+02:00", "41.0", "True"],
            ["2026-09-19T19:03:00+02:00", "42.0", "True"],
            ["2026-09-19T19:06:00+02:00", "43.0", "True"],
        ],
    )

    fixed_now = "2026-09-19T20:00:00+02:00"

    with patch("battery_logs.analyze_charge.datetime") as datetime_mock:
        datetime_mock.fromisoformat.side_effect = datetime.fromisoformat
        datetime_mock.now.return_value.astimezone.return_value.isoformat.return_value = fixed_now

        analyzer.analyze()

    with analyzer.samples_file.open(
        "r",
        encoding="utf-8",
    ) as file:
        samples = json.load(file)

    with analyzer.model_file.open(
        "r",
        encoding="utf-8",
    ) as file:
        model = json.load(file)

    assert samples["wireless"] == [
        {
            "created_at": fixed_now,
            "transitions": {
                "41": 120,
                "42": 180,
            },
        }
    ]

    assert samples["wired"] == []

    assert model["wireless"]["average"] == {
        "41": 120,
        "42": 180,
    }

    assert model["wireless"]["statistics"] == {
        "sample_count": 1,
        "last_updated": fixed_now,
    }


def test_analyze_does_not_add_duplicate_latest_sample(tmp_path):
    analyzer = ChargeAnalyzer(tmp_path)

    input_file = tmp_path / "battery_wireless_charge_log.csv"

    _write_log(
        input_file,
        [
            ["2026-09-19T19:00:00+02:00", "40.0", "True"],
            ["2026-09-19T19:01:00+02:00", "41.0", "True"],
            ["2026-09-19T19:03:00+02:00", "42.0", "True"],
        ],
    )

    existing_samples = {
        "wired": [],
        "wireless": [
            {
                "created_at": "2026-09-19T18:00:00+02:00",
                "transitions": {
                    "41": 120,
                },
            },
        ],
    }

    _write_json(analyzer.samples_file, existing_samples)

    with patch("battery_logs.analyze_charge.datetime") as datetime_mock:
        datetime_mock.now.return_value.astimezone.return_value.isoformat.return_value = "2026-09-19T20:00:00+02:00"

        analyzer.analyze()

    with analyzer.samples_file.open(
        "r",
        encoding="utf-8",
    ) as file:
        samples = json.load(file)

    assert len(samples["wireless"]) == 2


def test_analyze_creates_empty_files_when_no_log_exists(tmp_path):
    analyzer = ChargeAnalyzer(tmp_path)

    analyzer.analyze()

    assert analyzer.samples_file.exists()
    assert analyzer.model_file.exists()

    with analyzer.samples_file.open(
        "r",
        encoding="utf-8",
    ) as file:
        samples = json.load(file)

    with analyzer.model_file.open(
        "r",
        encoding="utf-8",
    ) as file:
        model = json.load(file)

    assert samples == {
        "wired": [],
        "wireless": [],
    }

    assert model["wired"]["statistics"]["sample_count"] == 0
    assert model["wireless"]["statistics"]["sample_count"] == 0
