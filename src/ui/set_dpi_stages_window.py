from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from config.paths import MENU_ICON_DIR
from razer.mouse_state import DPIStage

MIN_DPI = 100
MAX_DPI = 20_000
DPI_STEP = 100

SPINBOX_WIDTH = 70
AXIS_SPACING = 8

MIN_STAGES = 1
MAX_STAGES = 5


class SetDPIStagesWindow(QWidget):
    """Window used to configure the DPI stages."""

    settings_changed = Signal(list)

    def __init__(
        self,
        stages: list[DPIStage],
    ) -> None:
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        self.setWindowTitle("Modification des Plages DPI")
        self.setWindowIcon(
            QIcon(str(MENU_ICON_DIR / "mouse.svg")),
        )

        self._stages: list[DPIStage] = []
        self._spinboxes: list[QSpinBox] = []

        stages_widget = QWidget()
        self._stages_layout = QHBoxLayout(stages_widget)
        self._stages_layout.setContentsMargins(0, 0, 0, 0)
        self._stages_layout.setSpacing(AXIS_SPACING)

        self._add_button = QPushButton("+")
        self._remove_button = QPushButton("-")

        self._add_button.clicked.connect(self._add_stage)
        self._remove_button.clicked.connect(self._remove_stage)

        stage_buttons_layout = QHBoxLayout()
        stage_buttons_layout.setContentsMargins(0, 0, 0, 0)
        stage_buttons_layout.setSpacing(AXIS_SPACING)
        stage_buttons_layout.addWidget(self._remove_button)
        stage_buttons_layout.addWidget(self._add_button)

        self._stages_layout.addLayout(stage_buttons_layout)

        self._save_button = QPushButton("Enregistrer")
        cancel_button = QPushButton("Annuler")

        self._save_button.clicked.connect(self._save)
        cancel_button.clicked.connect(self.close)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(AXIS_SPACING)
        buttons_layout.addWidget(self._save_button)
        buttons_layout.addWidget(cancel_button)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(AXIS_SPACING)
        main_layout.addWidget(
            stages_widget,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )
        main_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        self.set_stages(stages)

    def set_stages(self, stages: list[DPIStage]) -> None:
        """Replace the editable copy of the DPI stages."""
        self._clear_stages()

        self._stages = [DPIStage(stage.dpi) for stage in stages]

        for stage in self._stages:
            self._create_stage_spinbox(stage.dpi)

        self._update_buttons()

    def _create_stage_spinbox(self, value: int) -> None:
        """Create and add a spinbox for a DPI stage."""
        spinbox = QSpinBox()
        spinbox.setRange(MIN_DPI, MAX_DPI)
        spinbox.setSingleStep(DPI_STEP)
        spinbox.setValue(value)
        spinbox.setFixedWidth(SPINBOX_WIDTH)
        spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._stages_layout.insertWidget(
            len(self._spinboxes),
            spinbox,
        )

        self._spinboxes.append(spinbox)

    def _add_stage(self) -> None:
        """Add a new stage using the last stage's DPI value."""
        if len(self._stages) >= MAX_STAGES:
            return

        dpi = self._stages[-1].dpi

        self._stages.append(DPIStage(dpi))
        self._create_stage_spinbox(dpi)

        self._update_buttons()

    def _remove_stage(self) -> None:
        """Remove the last DPI stage."""
        if len(self._stages) <= MIN_STAGES:
            return

        self._stages.pop()

        spinbox = self._spinboxes.pop()
        self._stages_layout.removeWidget(spinbox)
        spinbox.deleteLater()

        self._update_buttons()

    def _clear_stages(self) -> None:
        """Remove all stage spinboxes."""
        while self._spinboxes:
            spinbox = self._spinboxes.pop()
            self._stages_layout.removeWidget(spinbox)
            spinbox.deleteLater()

        self._stages.clear()

    def _update_buttons(self) -> None:
        """Update the stage count controls."""
        stage_count = len(self._stages)

        self._add_button.setEnabled(stage_count < MAX_STAGES)
        self._remove_button.setEnabled(stage_count > MIN_STAGES)

    def _save(self) -> None:
        """Emit the edited stages and close the window."""
        for stage, spinbox in zip(self._stages, self._spinboxes):
            stage.dpi = spinbox.value()

        self.settings_changed.emit([DPIStage(stage.dpi) for stage in self._stages])
        self.close()
