from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from battery_logs.battery_logger import BatteryLogEntry
from ui.battery_logger_window import BatteryLoggerWindow


def _get_app() -> QApplication:
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    return app


def test_window_initializes_in_idle_state() -> None:
    _get_app()

    window = BatteryLoggerWindow()

    assert window.windowTitle() == "Journalisation de la batterie"
    assert window.log_view.isReadOnly()
    assert window.start_button.isEnabled()
    assert not window.stop_button.isEnabled()


def test_set_logging_state() -> None:
    _get_app()

    window = BatteryLoggerWindow()

    started_at = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)

    with patch("ui.battery_logger_window.datetime") as datetime_mock:
        datetime_mock.now.return_value = datetime(
            2026,
            9,
            28,
            12,
            17,
            32,
            tzinfo=timezone.utc,
        )

        window.set_logging_state(started_at)

    assert not window.start_button.isEnabled()
    assert window.stop_button.isEnabled()
    assert (
        window.logging_status.text() == "En cours de journalisation depuis : 00:17:32"
    )


def test_set_idle_state() -> None:
    _get_app()

    window = BatteryLoggerWindow()

    started_at = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)
    last_duration = timedelta(minutes=17, seconds=32)

    window.set_logging_state(started_at)
    window.set_idle_state(last_duration)

    assert window.start_button.isEnabled()
    assert not window.stop_button.isEnabled()
    assert (
        window.logging_status.text() == "Durée de la dernière journalisation : 00:17:32"
    )


def test_start_logging_emits_signal() -> None:
    _get_app()

    window = BatteryLoggerWindow()

    received = []
    window.start_requested.connect(lambda: received.append(True))

    window._start_logging()

    assert received == [True]


def test_stop_logging_emits_signal() -> None:
    _get_app()

    window = BatteryLoggerWindow()

    received = []
    window.stop_requested.connect(lambda: received.append(True))

    window._stop_logging()

    assert received == [True]


def test_display_start() -> None:
    _get_app()

    window = BatteryLoggerWindow()

    window.display_start(
        "Razer Viper Ultimate (Wireless)",
        1,
    )

    assert window.log_view.toPlainText() == (
        "Début de la journalisation\n"
        "Mode initial détecté : Razer Viper Ultimate (Wireless)\n"
        "Rafraîchissement de la journalisation toutes les 1 seconde(s)\n"
        "Une nouvelle entrée est enregistrée uniquement lorsque le "
        "pourcentage de batterie ou l’état de charge change\n"
        "Journalisation en cours..."
    )


def test_display_log_entry() -> None:
    _get_app()

    window = BatteryLoggerWindow()

    window.display_start(
        "Razer Viper Ultimate (Wireless)",
        1,
    )

    window.display_log_entry(
        BatteryLogEntry(
            timestamp="2026-09-24T15:28:54+02:00",
            battery_percent=81,
            is_charging=False,
        )
    )

    assert window.log_view.toPlainText().endswith(
        "[15:28:54] Batterie : 81 % | État : non chargé\nJournalisation en cours..."
    )


def test_display_log_entry_charging() -> None:
    _get_app()

    window = BatteryLoggerWindow()

    window.display_start(
        "Razer Viper Ultimate (Wireless)",
        1,
    )

    window.display_log_entry(
        BatteryLogEntry(
            timestamp="2026-09-24T15:28:58+02:00",
            battery_percent=81,
            is_charging=True,
        )
    )

    assert window.log_view.toPlainText().endswith(
        "[15:28:58] Batterie : 81 % | État : en charge\nJournalisation en cours..."
    )


def test_display_log_entry_replaces_logging_status() -> None:
    _get_app()

    window = BatteryLoggerWindow()

    window.display_start(
        "Razer Viper Ultimate (Wireless)",
        1,
    )

    window.display_log_entry(
        BatteryLogEntry(
            timestamp="2026-09-24T15:28:54+02:00",
            battery_percent=81,
            is_charging=False,
        )
    )

    window.display_log_entry(
        BatteryLogEntry(
            timestamp="2026-09-24T15:28:58+02:00",
            battery_percent=81,
            is_charging=True,
        )
    )

    assert window.log_view.toPlainText().count("Journalisation en cours...") == 1
    assert (
        "[15:28:54] Batterie : 81 % | État : non chargé"
        in window.log_view.toPlainText()
    )
    assert (
        "[15:28:58] Batterie : 81 % | État : en charge" in window.log_view.toPlainText()
    )


def test_display_stop() -> None:
    _get_app()

    window = BatteryLoggerWindow()

    window.display_start(
        "Razer Viper Ultimate (Wireless)",
        1,
    )

    window.display_log_entry(
        BatteryLogEntry(
            timestamp="2026-09-24T15:28:54+02:00",
            battery_percent=81,
            is_charging=False,
        )
    )

    window.display_stop()

    assert window.log_view.toPlainText().endswith(
        "[15:28:54] Batterie : 81 % | État : non chargé\nFin de la journalisation"
    )


def test_idle_state_without_previous_logging_clears_status() -> None:
    _get_app()

    window = BatteryLoggerWindow()

    window.set_idle_state(None)

    assert window.logging_status.text() == ""


def test_format_duration() -> None:
    assert BatteryLoggerWindow._format_duration(timedelta()) == "00:00:00"
    assert (
        BatteryLoggerWindow._format_duration(
            timedelta(hours=1, minutes=2, seconds=3),
        )
        == "01:02:03"
    )
    assert (
        BatteryLoggerWindow._format_duration(
            timedelta(hours=27, minutes=45, seconds=12),
        )
        == "27:45:12"
    )


def test_logging_duration_timer_follows_logging_state() -> None:
    _get_app()

    window = BatteryLoggerWindow()
    started_at = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)

    assert not window._duration_timer.isActive()

    window.set_logging_state(started_at)

    assert window._duration_timer.isActive()

    window.set_idle_state(timedelta(minutes=1))

    assert not window._duration_timer.isActive()
