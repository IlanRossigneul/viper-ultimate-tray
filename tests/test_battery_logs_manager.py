from pathlib import Path
from unittest.mock import MagicMock, patch

from battery_logs.manager import LogManager


def test_logger_is_not_running_initially(tmp_path: Path) -> None:
    manager = LogManager(tmp_path)

    assert not manager.is_logger_running()


def test_start_logger_starts_battery_logger(tmp_path: Path) -> None:
    manager = LogManager(tmp_path)

    mock_logger = MagicMock()
    mock_thread = MagicMock()
    mock_thread.is_alive.return_value = True

    with (
        patch(
            "battery_logs.manager.BatteryLogger",
            return_value=mock_logger,
        ) as logger_class,
        patch(
            "battery_logs.manager.Thread",
            return_value=mock_thread,
        ) as thread_class,
    ):
        assert manager.start_logger()

    logger_class.assert_called_once_with(tmp_path)
    thread_class.assert_called_once_with(
        target=mock_logger.run,
        daemon=True,
        name="BatteryLogger",
    )
    mock_thread.start.assert_called_once()
    assert manager.logger is mock_logger
    assert manager.logger_thread is mock_thread


def test_start_logger_refuses_when_already_running(tmp_path: Path) -> None:
    manager = LogManager(tmp_path)

    mock_thread = MagicMock()
    mock_thread.is_alive.return_value = True
    manager.logger_thread = mock_thread

    with patch("battery_logs.manager.BatteryLogger") as logger_class:
        assert not manager.start_logger()

    logger_class.assert_not_called()


def test_stop_logger_refuses_when_not_running(tmp_path: Path) -> None:
    manager = LogManager(tmp_path)

    assert not manager.stop_logger()


def test_stop_logger_processes_logs_after_thread_stops(
    tmp_path: Path,
) -> None:
    manager = LogManager(tmp_path)

    mock_logger = MagicMock()
    mock_thread = MagicMock()
    mock_thread.is_alive.return_value = True

    manager.logger = mock_logger
    manager.logger_thread = mock_thread

    with patch.object(
        manager,
        "_process_battery_logs",
    ) as process_logs:
        assert manager.stop_logger()

    mock_logger.stop.assert_called_once()
    mock_thread.join.assert_called_once()
    process_logs.assert_called_once()

    assert manager.logger is None
    assert manager.logger_thread is None


def test_process_battery_logs_runs_steps_in_order(
    tmp_path: Path,
) -> None:
    manager = LogManager(tmp_path)
    calls: list[str] = []

    def clean() -> bool:
        calls.append("clean")
        return True

    def analyze() -> bool:
        calls.append("analyze")
        return True

    def archive() -> bool:
        calls.append("archive")
        return True

    def delete() -> bool:
        calls.append("delete")
        return True

    with (
        patch.object(manager, "clean_battery_logs", side_effect=clean),
        patch.object(manager, "analyze_charge_logs", side_effect=analyze),
        patch.object(manager, "archive_battery_logs", side_effect=archive),
        patch.object(manager, "delete_battery_logs", side_effect=delete),
    ):
        manager._process_battery_logs()

    assert calls == ["clean", "analyze", "archive", "delete"]


def test_process_battery_logs_stops_after_clean_failure(
    tmp_path: Path,
) -> None:
    manager = LogManager(tmp_path)

    with (
        patch.object(
            manager,
            "clean_battery_logs",
            return_value=False,
        ) as clean,
        patch.object(
            manager,
            "analyze_charge_logs",
        ) as analyze,
        patch.object(
            manager,
            "archive_battery_logs",
        ) as archive,
        patch.object(
            manager,
            "delete_battery_logs",
        ) as delete,
    ):
        manager._process_battery_logs()

    clean.assert_called_once()
    analyze.assert_not_called()
    archive.assert_not_called()
    delete.assert_not_called()


def test_process_battery_logs_stops_after_analyze_failure(
    tmp_path: Path,
) -> None:
    manager = LogManager(tmp_path)

    with (
        patch.object(
            manager,
            "clean_battery_logs",
            return_value=True,
        ) as clean,
        patch.object(
            manager,
            "analyze_charge_logs",
            return_value=False,
        ) as analyze,
        patch.object(
            manager,
            "archive_battery_logs",
        ) as archive,
        patch.object(
            manager,
            "delete_battery_logs",
        ) as delete,
    ):
        manager._process_battery_logs()

    clean.assert_called_once()
    analyze.assert_called_once()
    archive.assert_not_called()
    delete.assert_not_called()


def test_process_battery_logs_stops_after_archive_failure(
    tmp_path: Path,
) -> None:
    manager = LogManager(tmp_path)

    with (
        patch.object(
            manager,
            "clean_battery_logs",
            return_value=True,
        ) as clean,
        patch.object(
            manager,
            "analyze_charge_logs",
            return_value=True,
        ) as analyze,
        patch.object(
            manager,
            "archive_battery_logs",
            return_value=False,
        ) as archive,
        patch.object(
            manager,
            "delete_battery_logs",
        ) as delete,
    ):
        manager._process_battery_logs()

    clean.assert_called_once()
    analyze.assert_called_once()
    archive.assert_called_once()
    delete.assert_not_called()
