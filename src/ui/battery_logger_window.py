from datetime import datetime, timedelta, timezone

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from battery_logs.battery_logger import BatteryLogEntry
from config.paths import MENU_ICON_DIR


class BatteryLoggerWindow(QDialog):
    """Battery logger window."""

    start_requested = Signal()
    stop_requested = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Journalisation de la batterie")
        self.setWindowIcon(QIcon(str(MENU_ICON_DIR / "mouse.svg")))

        self.start_button = QPushButton("Démarrer")
        self.stop_button = QPushButton("Arrêter")

        self.logging_status = QLabel()

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumSize(
            self.log_view.sizeHint().width() * 3,
            self.log_view.sizeHint().height() * 2,
        )

        self.quit_button = QPushButton("Quitter")

        self.start_button.clicked.connect(self._start_logging)
        self.stop_button.clicked.connect(self._stop_logging)
        self.quit_button.clicked.connect(self.close)

        self._logging_started_at: datetime | None = None
        self._last_logging_duration: timedelta | None = None

        self._duration_timer = QTimer(self)
        self._duration_timer.setInterval(1000)
        self._duration_timer.timeout.connect(self._update_logging_status)

        self.set_idle_state(None)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)

        layout = QVBoxLayout()
        layout.addLayout(controls_layout)
        layout.addWidget(self.logging_status)
        layout.addWidget(self.log_view)
        layout.addWidget(self.quit_button)

        self.setLayout(layout)

    def set_idle_state(self, last_duration: timedelta | None) -> None:
        """Set the initial and stopped state."""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        self._logging_started_at = None
        self._last_logging_duration = last_duration
        self._duration_timer.stop()

        self._update_logging_status()

    def set_logging_state(self, started_at: datetime) -> None:
        """Set the active logging state."""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self._logging_started_at = started_at
        self._last_logging_duration = None
        self._duration_timer.start()

        self._update_logging_status()

    def _remove_logging_status(self) -> None:
        """Remove the current logging status line."""
        cursor = self.log_view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.movePosition(cursor.MoveOperation.StartOfBlock)
        cursor.select(cursor.SelectionType.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deleteChar()

    def display_start(
        self,
        mode: str,
        interval_seconds: int,
    ) -> None:
        self.log_view.clear()
        self.log_view.appendPlainText("Début de la journalisation")
        self.log_view.appendPlainText(f"Mode initial détecté : {mode}")
        self.log_view.appendPlainText(
            "Rafraîchissement de la journalisation toutes les "
            f"{interval_seconds} seconde(s)"
        )
        self.log_view.appendPlainText(
            "Une nouvelle entrée est enregistrée uniquement lorsque "
            "le pourcentage de batterie ou l’état de charge change"
        )
        self.log_view.appendPlainText("Journalisation en cours...")

    def display_log_entry(self, entry: BatteryLogEntry) -> None:
        self._remove_logging_status()

        timestamp = entry.timestamp[11:19]

        battery = int(entry.battery_percent)

        charging_state = "en charge" if entry.is_charging else "non chargé"

        self.log_view.appendPlainText(
            f"[{timestamp}] Batterie : {battery} % | État : {charging_state}"
        )
        self.log_view.appendPlainText("Journalisation en cours...")

    def display_stop(self) -> None:
        self._remove_logging_status()
        self.log_view.appendPlainText("Fin de la journalisation")

    def display_session_change(
        self,
        old_mode: str,
        new_mode: str,
    ) -> None:
        self._remove_logging_status()

        self.log_view.appendPlainText(
            f"Changement de connexion détecté : {old_mode} → {new_mode}"
        )
        self.log_view.appendPlainText(
            f"La session {old_mode} a été terminée et traitée."
        )
        self.log_view.appendPlainText(f"Nouvelle session {new_mode} démarrée.")
        self.log_view.appendPlainText("Journalisation en cours...")

    def _start_logging(self) -> None:
        """Request logger start."""
        self.start_requested.emit()

    def _stop_logging(self) -> None:
        """Request logger stop."""
        self.stop_requested.emit()

    @staticmethod
    def _format_duration(duration: timedelta) -> str:
        """Format a duration as HH:MM:SS."""
        total_seconds = max(0, int(duration.total_seconds()))

        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def _update_logging_status(self) -> None:
        """Update the logging duration display."""
        if self._logging_started_at is not None:
            duration = datetime.now(timezone.utc) - self._logging_started_at

            self.logging_status.setText(
                f"En cours de journalisation depuis : {self._format_duration(duration)}"
            )
            return

        if self._last_logging_duration is not None:
            self.logging_status.setText(
                "Durée de la dernière journalisation : "
                f"{self._format_duration(self._last_logging_duration)}"
            )
            return

        self.logging_status.clear()
