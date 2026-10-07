from PySide6.QtCore import QPointF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QScrollBar,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from config.paths import MENU_ICON_DIR, MENU_WINDOW_ICON_DIR
from razer.mouse_state import DPIStage

MIN_DPI = 100
MAX_DPI = 20_000
DPI_STEP = 100

GRID_COLOR = QColor("#00FF00")
GRID_BACKGROUND = QColor("#151515")

SPINBOX_WIDTH = 70
AXIS_SPACING = 8


class DPIGridWidget(QWidget):
    """Display the DPI grid and the fixed center cursor."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._x_dpi = 800
        self._y_dpi = 800

        self._cursor = QPixmap(
            str(MENU_WINDOW_ICON_DIR / "cursor.svg"),
        )

        self.setMinimumSize(100, 100)

    def set_dpi(self, x_dpi: int, y_dpi: int) -> None:
        """Update the displayed X and Y DPI values."""
        self._x_dpi = x_dpi
        self._y_dpi = y_dpi
        self.update()

    @staticmethod
    def _grid_spacing(dpi: int) -> float:
        """Return the grid spacing corresponding to a DPI value."""
        dpi_ratio = (dpi - MIN_DPI) / (MAX_DPI - MIN_DPI)
        maximum_spacing = 48.0
        minimum_spacing = 8.0

        return maximum_spacing - (dpi_ratio * (maximum_spacing - minimum_spacing))

    def paintEvent(self, event) -> None:
        """Paint the square DPI grid and its center cursor."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), GRID_BACKGROUND)

        width = self.width()
        height = self.height()

        x_spacing = self._grid_spacing(self._x_dpi)
        y_spacing = self._grid_spacing(self._y_dpi)

        painter.setPen(GRID_COLOR)

        x = 0.0
        while x <= width:
            painter.drawLine(QPointF(x, 0), QPointF(x, height))
            x += x_spacing

        y = 0.0
        while y <= height:
            painter.drawLine(QPointF(0, y), QPointF(width, y))
            y += y_spacing

        cursor_size = min(32, width, height)
        cursor = self._cursor.scaled(
            cursor_size,
            cursor_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        cursor_x = (width - cursor.width()) // 2
        cursor_y = (height - cursor.height()) // 2

        painter.drawPixmap(cursor_x, cursor_y, cursor)


class DPIScrollBar(QScrollBar):
    """Scroll bar used to select DPI in 100-point increments."""

    def __init__(
        self,
        orientation: Qt.Orientation,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(orientation, parent)

        self.setRange(
            0,
            (MAX_DPI - MIN_DPI) // DPI_STEP,
        )
        self.setSingleStep(1)
        self.setPageStep(1)

    def dpi_value(self) -> int:
        """Return the selected DPI value."""
        return MIN_DPI + self.value() * DPI_STEP

    def set_dpi_value(self, dpi: int) -> None:
        """Set the selected DPI value."""
        dpi = max(MIN_DPI, min(dpi, MAX_DPI))
        self.setValue((dpi - MIN_DPI) // DPI_STEP)


class DPISelectorWidget(QWidget):
    """Arrange the square DPI grid and its two scrollbars."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.grid = DPIGridWidget(self)

        self.x_scrollbar = DPIScrollBar(
            Qt.Orientation.Horizontal,
            self,
        )
        self.y_scrollbar = DPIScrollBar(
            Qt.Orientation.Vertical,
            self,
        )

        self.lock_button = QPushButton(self)
        self.lock_button.setCheckable(True)
        self.lock_button.setIconSize(QSize(20, 16))

        self.lock_button.toggled.connect(self._update_lock_icon)

        self.y_scrollbar.setInvertedAppearance(True)
        self.y_scrollbar.setInvertedControls(True)

        self.x_scrollbar.valueChanged.connect(
            self._x_scrollbar_changed,
        )
        self.y_scrollbar.valueChanged.connect(
            self._y_scrollbar_changed,
        )

        self.setStyleSheet(
            """
            QScrollBar {
                background: #252525;
                border: none;
            }

            QScrollBar::handle {
                background: #00FF00;
                border-radius: 2px;
                min-width: 8px;
                min-height: 8px;
            }

            QScrollBar::add-line,
            QScrollBar::sub-line {
                background: transparent;
                border: none;
            }

            QScrollBar::add-page,
            QScrollBar::sub-page {
                background: #252525;
            }

            QPushButton {
                background: transparent;
            }

            QPushButton:checked {
                background: #8000FF00;
            }
            """
        )

        self._update_lock_icon(self.lock_button.isChecked())

    def _update_lock_icon(self, locked: bool) -> None:
        """Update the lock icon according to the current state."""
        icon_name = "lock.svg" if locked else "unlock.svg"

        self.lock_button.setIcon(
            QIcon(str(MENU_WINDOW_ICON_DIR / icon_name)),
        )

        if locked:
            self.y_scrollbar.blockSignals(True)
            self.y_scrollbar.setValue(
                self.x_scrollbar.value(),
            )
            self.y_scrollbar.blockSignals(False)

    def _x_scrollbar_changed(self, value: int) -> None:
        """Handle X DPI changes."""
        if self.lock_button.isChecked():
            self.y_scrollbar.blockSignals(True)
            self.y_scrollbar.setValue(value)
            self.y_scrollbar.blockSignals(False)

        self._update_grid()

    def _y_scrollbar_changed(self, value: int) -> None:
        """Handle Y DPI changes."""
        if self.lock_button.isChecked():
            self.x_scrollbar.blockSignals(True)
            self.x_scrollbar.setValue(value)
            self.x_scrollbar.blockSignals(False)

        self._update_grid()

    def _update_grid(self) -> None:
        """Update the grid according to the current DPI values."""
        self.grid.set_dpi(
            self.x_scrollbar.dpi_value(),
            self.y_scrollbar.dpi_value(),
        )

    def resizeEvent(self, event) -> None:
        """Keep the grid square and align the scrollbars around it."""
        x_scrollbar_height = self.x_scrollbar.sizeHint().height()
        y_scrollbar_width = self.y_scrollbar.sizeHint().width()

        available_width = self.width() - AXIS_SPACING - y_scrollbar_width
        available_height = self.height() - AXIS_SPACING - x_scrollbar_height

        grid_size = min(
            available_width,
            available_height,
        )

        if grid_size <= 0:
            return

        self.grid.setGeometry(
            0,
            0,
            grid_size,
            grid_size,
        )

        self.x_scrollbar.setGeometry(
            0,
            grid_size + AXIS_SPACING,
            grid_size,
            x_scrollbar_height,
        )

        self.y_scrollbar.setGeometry(
            grid_size + AXIS_SPACING,
            0,
            y_scrollbar_width,
            grid_size,
        )

        self.lock_button.setGeometry(
            grid_size + AXIS_SPACING,
            grid_size + AXIS_SPACING,
            y_scrollbar_width,
            x_scrollbar_height,
        )

        super().resizeEvent(event)


class DPIContentWidget(QWidget):
    """Arrange the DPI selector and its spinboxes."""

    def __init__(
        self,
        selector: DPISelectorWidget,
        x_spinbox: QSpinBox,
        y_spinbox: QSpinBox,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.selector = selector
        self.x_spinbox = x_spinbox
        self.y_spinbox = y_spinbox

        self.selector.setParent(self)
        self.x_spinbox.setParent(self)
        self.y_spinbox.setParent(self)

        self.x_spinbox.raise_()
        self.y_spinbox.raise_()

    def _update_geometry(self) -> None:
        """Keep the selector and spinboxes aligned."""
        x_scrollbar_height = self.selector.x_scrollbar.sizeHint().height()
        y_scrollbar_width = self.selector.y_scrollbar.sizeHint().width()

        x_spinbox_height = self.x_spinbox.sizeHint().height()
        y_spinbox_height = self.y_spinbox.sizeHint().height()
        y_spinbox_width = self.y_spinbox.width()

        available_width = (
            self.width()
            - AXIS_SPACING
            - y_scrollbar_width
            - AXIS_SPACING
            - y_spinbox_width
        )

        available_height = (
            self.height()
            - AXIS_SPACING
            - x_scrollbar_height
            - AXIS_SPACING
            - x_spinbox_height
        )

        grid_size = min(
            available_width,
            available_height,
        )

        if grid_size <= 0:
            return

        selector_width = grid_size + AXIS_SPACING + y_scrollbar_width
        selector_height = grid_size + AXIS_SPACING + x_scrollbar_height

        self.selector.setGeometry(
            0,
            0,
            selector_width,
            selector_height,
        )

        self.x_spinbox.move(
            (grid_size - self.x_spinbox.width()) // 2,
            selector_height + AXIS_SPACING,
        )

        self.y_spinbox.move(
            selector_width + AXIS_SPACING,
            (grid_size - y_spinbox_height) // 2,
        )

    def resizeEvent(self, event) -> None:
        """Keep the spinboxes aligned when resized."""
        super().resizeEvent(event)
        self._update_geometry()

    def showEvent(self, event) -> None:
        """Position the spinboxes after their initial geometry is finalized."""
        super().showEvent(event)
        self._update_geometry()


class SetDPIWindow(QWidget):
    """Window used to configure the current mouse DPI."""

    settings_changed = Signal(int, int, list, int)

    def __init__(
        self,
        current_dpi: tuple[int, int],
        stages: list[DPIStage],
        active_stage: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("Modification du DPI")
        self.setWindowIcon(
            QIcon(str(MENU_ICON_DIR / "mouse.svg")),
        )
        self.setFixedSize(790, 900)

        self._stages = stages
        self._active_stage = active_stage
        self._updating_from_stage = False

        self._original_dpi = current_dpi

        self.selector = DPISelectorWidget(self)

        self.x_spinbox = self._create_spinbox(
            current_dpi[0],
        )
        self.y_spinbox = self._create_spinbox(
            current_dpi[1],
        )

        self.selector.x_scrollbar.set_dpi_value(current_dpi[0])
        self.selector.y_scrollbar.set_dpi_value(current_dpi[1])

        self.content = DPIContentWidget(
            self.selector,
            self.x_spinbox,
            self.y_spinbox,
            self,
        )

        self.x_spinbox.valueChanged.connect(
            self._x_spinbox_changed,
        )
        self.y_spinbox.valueChanged.connect(
            self._y_spinbox_changed,
        )

        self.selector.x_scrollbar.valueChanged.connect(
            self._x_scrollbar_changed,
        )
        self.selector.y_scrollbar.valueChanged.connect(
            self._y_scrollbar_changed,
        )

        self.selector.lock_button.toggled.connect(
            self._lock_toggled,
        )

        self._create_layout()

    def _create_stages_group(self) -> QGroupBox:
        """Create the DPI stages group."""
        group = QGroupBox("Plages DPI")

        group.setStyleSheet(
            """
            QPushButton:checked {
                background: #8000FF00;
            }
            """
        )

        layout = QHBoxLayout(group)
        layout.setSpacing(AXIS_SPACING)

        self.stage_button_group = QButtonGroup(self)
        self.stage_button_group.setExclusive(False)

        self.stage_buttons: list[QPushButton] = []

        for stage in self._stages:
            button = QPushButton(str(stage.dpi))
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked, button=button: self._toggle_stage_button(
                    button,
                    checked,
                )
            )

            self.stage_button_group.addButton(button)
            self.stage_buttons.append(button)
            layout.addWidget(button)

        edit_button = QPushButton("Éditer")
        layout.addWidget(edit_button)

        return group

    def _toggle_stage_button(
        self,
        button: QPushButton,
        checked: bool,
    ) -> None:
        """Allow at most one stage button to be selected, with deselection."""
        if not checked:
            return

        for stage_button in self.stage_buttons:
            if stage_button is not button:
                stage_button.setChecked(False)

        stage_number = self.stage_buttons.index(button)
        dpi = self._stages[stage_number].dpi

        self._updating_from_stage = True

        try:
            self.x_spinbox.setValue(dpi)
            self.y_spinbox.setValue(dpi)
        finally:
            self._updating_from_stage = False

    def _deselect_stage(self) -> None:
        """Deselect the currently selected DPI stage."""
        if self._updating_from_stage:
            return

        for button in self.stage_buttons:
            if button.isChecked():
                button.setChecked(False)

    def _selected_stage(self) -> int | None:
        """Return the selected DPI stage number, if any."""
        for index, button in enumerate(self.stage_buttons, start=1):
            if button.isChecked():
                return index

        return None

    @staticmethod
    def _create_spinbox(value: int) -> QSpinBox:
        """Create a DPI spinbox."""
        spinbox = QSpinBox()
        spinbox.setRange(MIN_DPI, MAX_DPI)
        spinbox.setSingleStep(DPI_STEP)
        spinbox.setValue(value)
        spinbox.setFixedWidth(SPINBOX_WIDTH)
        spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)

        return spinbox

    def _create_layout(self) -> None:
        """Create the window layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(AXIS_SPACING)

        main_layout.addWidget(self._create_stages_group())

        current_dpi_group = QGroupBox("DPI courant")
        current_dpi_layout = QVBoxLayout(current_dpi_group)
        current_dpi_layout.addWidget(self.content)

        main_layout.addWidget(current_dpi_group, 1)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(AXIS_SPACING)

        save_button = QPushButton("Enregistrer")
        quit_button = QPushButton("Quitter")

        save_button.clicked.connect(self._save)
        quit_button.clicked.connect(self.close)

        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(quit_button)

        main_layout.addLayout(buttons_layout)

    def _x_scrollbar_changed(self, _value: int) -> None:
        """Handle X DPI scrollbar changes."""
        if not self._updating_from_stage:
            self._deselect_stage()

        value = self.selector.x_scrollbar.dpi_value()

        if self.x_spinbox.value() != value:
            self.x_spinbox.setValue(value)

        if self.selector.lock_button.isChecked() and self.y_spinbox.value() != value:
            self.y_spinbox.setValue(value)

    def _y_scrollbar_changed(self, _value: int) -> None:
        """Handle Y DPI scrollbar changes."""
        if not self._updating_from_stage:
            self._deselect_stage()

        value = self.selector.y_scrollbar.dpi_value()

        if self.y_spinbox.value() != value:
            self.y_spinbox.setValue(value)

        if self.selector.lock_button.isChecked() and self.x_spinbox.value() != value:
            self.x_spinbox.setValue(value)

    def _x_spinbox_changed(self, value: int) -> None:
        """Handle X DPI spinbox changes."""
        if not self._updating_from_stage:
            self._deselect_stage()

        if self.selector.x_scrollbar.dpi_value() != value:
            self.selector.x_scrollbar.set_dpi_value(value)

    def _y_spinbox_changed(self, value: int) -> None:
        """Handle Y DPI spinbox changes."""
        if not self._updating_from_stage:
            self._deselect_stage()

        if self.selector.y_scrollbar.dpi_value() != value:
            self.selector.y_scrollbar.set_dpi_value(value)

    def _lock_toggled(self, locked: bool) -> None:
        """Synchronize both spinboxes when DPI locking is enabled."""
        if not locked:
            return

        value = self.selector.x_scrollbar.dpi_value()

        if self.x_spinbox.value() != value:
            self.x_spinbox.setValue(value)

        if self.y_spinbox.value() != value:
            self.y_spinbox.setValue(value)

    def _save(self) -> None:
        """Save the selected DPI values and active stage."""
        self._original_dpi = (
            self.x_spinbox.value(),
            self.y_spinbox.value(),
        )

        active_stage = self._selected_stage()

        if active_stage is None:
            active_stage = self._active_stage
        else:
            self._active_stage = active_stage

        self.settings_changed.emit(
            self._original_dpi[0],
            self._original_dpi[1],
            self._stages,
            active_stage,
        )
        self.close()
