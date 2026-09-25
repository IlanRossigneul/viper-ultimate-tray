from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
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

        self.set_idle_state()

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)

        layout = QVBoxLayout()
        layout.addLayout(controls_layout)
        layout.addWidget(self.log_view)
        layout.addWidget(self.quit_button)

        self.setLayout(layout)

    def set_idle_state(self) -> None:
        """Set the initial and stopped state."""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def set_logging_state(self) -> None:
        """Set the active logging state."""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

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

    def _start_logging(self) -> None:
        """Request logger start."""
        self.start_requested.emit()

    def _stop_logging(self) -> None:
        """Request logger stop."""
        self.stop_requested.emit()
