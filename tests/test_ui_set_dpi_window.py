from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from ui.set_dpi_window import (
    DPI_STEP,
    MAX_DPI,
    MIN_DPI,
    DPIScrollBar,
    SetDPIWindow,
)


def _get_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_dpi_scrollbar_converts_value_to_dpi() -> None:
    _get_app()

    scrollbar = DPIScrollBar(Qt.Orientation.Horizontal)

    scrollbar.setValue(0)
    assert scrollbar.dpi_value() == MIN_DPI

    scrollbar.setValue(5)
    assert scrollbar.dpi_value() == MIN_DPI + 5 * DPI_STEP

    scrollbar.setValue(199)
    assert scrollbar.dpi_value() == MAX_DPI


def test_dpi_scrollbar_sets_dpi_value() -> None:
    _get_app()

    scrollbar = DPIScrollBar(Qt.Orientation.Horizontal)

    scrollbar.set_dpi_value(1600)

    assert scrollbar.dpi_value() == 1600


def test_dpi_scrollbar_clamps_dpi_value() -> None:
    _get_app()

    scrollbar = DPIScrollBar(Qt.Orientation.Horizontal)

    scrollbar.set_dpi_value(MIN_DPI - DPI_STEP)
    assert scrollbar.dpi_value() == MIN_DPI

    scrollbar.set_dpi_value(MAX_DPI + DPI_STEP)
    assert scrollbar.dpi_value() == MAX_DPI


def test_set_dpi_window_initializes_current_dpi() -> None:
    _get_app()

    window = SetDPIWindow((1600, 3200))

    assert window.x_spinbox.value() == 1600
    assert window.y_spinbox.value() == 3200
    assert window.selector.x_scrollbar.dpi_value() == 1600
    assert window.selector.y_scrollbar.dpi_value() == 3200


def test_spinboxes_update_scrollbars() -> None:
    _get_app()

    window = SetDPIWindow((800, 800))

    window.x_spinbox.setValue(1600)
    window.y_spinbox.setValue(3200)

    assert window.selector.x_scrollbar.dpi_value() == 1600
    assert window.selector.y_scrollbar.dpi_value() == 3200


def test_scrollbars_update_spinboxes() -> None:
    _get_app()

    window = SetDPIWindow((800, 800))

    window.selector.x_scrollbar.set_dpi_value(1600)
    window.selector.y_scrollbar.set_dpi_value(3200)

    assert window.x_spinbox.value() == 1600
    assert window.y_spinbox.value() == 3200


def test_lock_synchronizes_both_axes() -> None:
    _get_app()

    window = SetDPIWindow((800, 1600))

    window.selector.lock_button.setChecked(True)

    assert window.x_spinbox.value() == 800
    assert window.y_spinbox.value() == 800
    assert window.selector.x_scrollbar.dpi_value() == 800
    assert window.selector.y_scrollbar.dpi_value() == 800

    window.x_spinbox.setValue(3200)

    assert window.y_spinbox.value() == 3200
    assert window.selector.x_scrollbar.dpi_value() == 3200
    assert window.selector.y_scrollbar.dpi_value() == 3200


def test_save_emits_selected_dpi_and_closes_window() -> None:
    _get_app()

    window = SetDPIWindow((800, 800))
    emitted = []

    window.dpi_changed.connect(
        lambda x, y: emitted.append((x, y)),
    )

    window.x_spinbox.setValue(1600)
    window.y_spinbox.setValue(3200)

    window._save()

    assert emitted == [(1600, 3200)]
    assert window.isVisible() is False


def test_quit_does_not_emit_dpi_changed() -> None:
    _get_app()

    window = SetDPIWindow((800, 800))
    emitted = []

    window.dpi_changed.connect(
        lambda x, y: emitted.append((x, y)),
    )

    window.close()

    assert emitted == []


def test_window_close_does_not_emit_dpi_changed() -> None:
    _get_app()

    window = SetDPIWindow((800, 800))
    emitted = []

    window.dpi_changed.connect(
        lambda x, y: emitted.append((x, y)),
    )

    window.show()
    window.close()

    assert emitted == []
