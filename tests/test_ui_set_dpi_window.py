from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from razer.mouse_state import DPIStage
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

    window = SetDPIWindow(
        (1600, 3200),
        [DPIStage(800), DPIStage(1600), DPIStage(3200)],
        2,
    )

    assert window.x_spinbox.value() == 1600
    assert window.y_spinbox.value() == 3200
    assert window.selector.x_scrollbar.dpi_value() == 1600
    assert window.selector.y_scrollbar.dpi_value() == 3200


def test_spinboxes_update_scrollbars() -> None:
    _get_app()

    window = SetDPIWindow(
        (800, 800),
        [DPIStage(800), DPIStage(1600), DPIStage(3200)],
        2,
    )

    window.x_spinbox.setValue(1600)
    window.y_spinbox.setValue(3200)

    assert window.selector.x_scrollbar.dpi_value() == 1600
    assert window.selector.y_scrollbar.dpi_value() == 3200


def test_scrollbars_update_spinboxes() -> None:
    _get_app()

    window = SetDPIWindow(
        (800, 800),
        [DPIStage(800), DPIStage(1600), DPIStage(3200)],
        2,
    )

    window.selector.x_scrollbar.set_dpi_value(1600)
    window.selector.y_scrollbar.set_dpi_value(3200)

    assert window.x_spinbox.value() == 1600
    assert window.y_spinbox.value() == 3200


def test_lock_synchronizes_both_axes() -> None:
    _get_app()

    window = SetDPIWindow(
        (800, 1600),
        [DPIStage(800), DPIStage(1600), DPIStage(3200)],
        2,
    )

    window.selector.lock_button.setChecked(True)

    assert window.x_spinbox.value() == 800
    assert window.y_spinbox.value() == 800
    assert window.selector.x_scrollbar.dpi_value() == 800
    assert window.selector.y_scrollbar.dpi_value() == 800

    window.x_spinbox.setValue(3200)

    assert window.y_spinbox.value() == 3200
    assert window.selector.x_scrollbar.dpi_value() == 3200
    assert window.selector.y_scrollbar.dpi_value() == 3200


def test_save_emits_dpi_and_preserves_active_stage_when_none_is_selected() -> None:
    _get_app()

    stages = [
        DPIStage(800),
        DPIStage(1600),
        DPIStage(3200),
    ]
    window = SetDPIWindow((800, 800), stages, 2)
    emitted = []

    window.settings_changed.connect(
        lambda x, y, emitted_stages, active_stage: emitted.append(
            (x, y, emitted_stages, active_stage)
        )
    )

    window.x_spinbox.setValue(1600)
    window.y_spinbox.setValue(3200)
    window._save()

    assert emitted == [(1600, 3200, stages, 2)]
    assert window.isVisible() is False


def test_save_emits_selected_stage_and_synchronized_dpi() -> None:
    _get_app()

    stages = [
        DPIStage(800),
        DPIStage(1600),
        DPIStage(3200),
    ]
    window = SetDPIWindow((800, 800), stages, 2)
    emitted = []

    window.settings_changed.connect(
        lambda x, y, emitted_stages, active_stage: emitted.append(
            (x, y, emitted_stages, active_stage)
        )
    )

    window.stage_buttons[2].click()
    window._save()

    assert emitted == [(3200, 3200, stages, 3)]


def test_stage_buttons_allow_only_one_selection() -> None:
    _get_app()

    window = SetDPIWindow(
        (800, 800),
        [
            DPIStage(800),
            DPIStage(1600),
            DPIStage(3200),
        ],
        2,
    )

    assert [button.isChecked() for button in window.stage_buttons] == [
        True,
        False,
        False,
    ]

    window.stage_buttons[0].click()

    assert [button.isChecked() for button in window.stage_buttons] == [
        False,
        False,
        False,
    ]

    window.stage_buttons[1].click()

    assert [button.isChecked() for button in window.stage_buttons] == [
        False,
        True,
        False,
    ]

    window.stage_buttons[1].click()

    assert [button.isChecked() for button in window.stage_buttons] == [
        False,
        False,
        False,
    ]


def test_selecting_stage_synchronizes_current_dpi() -> None:
    _get_app()

    window = SetDPIWindow(
        (800, 1600),
        [
            DPIStage(800),
            DPIStage(1600),
            DPIStage(3200),
        ],
        2,
    )

    window.stage_buttons[2].click()

    assert window.x_spinbox.value() == 3200
    assert window.y_spinbox.value() == 3200
    assert window.selector.x_scrollbar.dpi_value() == 3200
    assert window.selector.y_scrollbar.dpi_value() == 3200
    assert window.stage_buttons[2].isChecked()


def test_changing_spinbox_deselects_selected_stage() -> None:
    _get_app()

    window = SetDPIWindow(
        (800, 800),
        [
            DPIStage(800),
            DPIStage(1600),
            DPIStage(3200),
        ],
        2,
    )

    window.stage_buttons[1].click()
    assert window.stage_buttons[1].isChecked()

    window.x_spinbox.setValue(1000)

    assert not window.stage_buttons[1].isChecked()


def test_changing_y_spinbox_deselects_selected_stage() -> None:
    _get_app()

    window = SetDPIWindow(
        (800, 800),
        [
            DPIStage(800),
            DPIStage(1600),
            DPIStage(3200),
        ],
        2,
    )

    window.stage_buttons[1].click()
    assert window.stage_buttons[1].isChecked()

    window.y_spinbox.setValue(1000)

    assert not window.stage_buttons[1].isChecked()


def test_changing_x_scrollbar_deselects_selected_stage() -> None:
    _get_app()

    window = SetDPIWindow(
        (800, 800),
        [
            DPIStage(800),
            DPIStage(1600),
            DPIStage(3200),
        ],
        2,
    )

    window.stage_buttons[1].click()
    assert window.stage_buttons[1].isChecked()

    window.selector.x_scrollbar.set_dpi_value(1000)

    assert not window.stage_buttons[1].isChecked()


def test_changing_y_scrollbar_deselects_selected_stage() -> None:
    _get_app()

    window = SetDPIWindow(
        (800, 800),
        [
            DPIStage(800),
            DPIStage(1600),
            DPIStage(3200),
        ],
        2,
    )

    window.stage_buttons[1].click()
    assert window.stage_buttons[1].isChecked()

    window.selector.y_scrollbar.set_dpi_value(1000)

    assert not window.stage_buttons[1].isChecked()


def test_quit_does_not_emit_settings_changed() -> None:
    _get_app()

    window = SetDPIWindow(
        (800, 800),
        [DPIStage(800), DPIStage(1600), DPIStage(3200)],
        2,
    )
    emitted = []

    window.settings_changed.connect(
        lambda x, y, stages, active_stage: emitted.append((x, y, stages, active_stage))
    )

    window.close()

    assert emitted == []


def test_window_close_does_not_emit_settings_changed() -> None:
    _get_app()

    window = SetDPIWindow(
        (800, 800),
        [DPIStage(800), DPIStage(1600), DPIStage(3200)],
        2,
    )
    emitted = []

    window.settings_changed.connect(
        lambda x, y, stages, active_stage: emitted.append((x, y, stages, active_stage))
    )

    window.show()
    window.close()

    assert emitted == []


def test_edit_stages_updates_local_stage_configuration() -> None:
    _get_app()

    stages = [
        DPIStage(800),
        DPIStage(1600),
        DPIStage(3200),
    ]
    window = SetDPIWindow((800, 800), stages, 2)

    window._edit_stages()

    assert window.set_dpi_stages_window is not None

    child = window.set_dpi_stages_window
    child._spinboxes[1].setValue(1800)
    child._save()

    assert [stage.dpi for stage in window._stages] == [
        800,
        1800,
        3200,
    ]


def test_edit_stages_does_not_emit_main_settings_changed() -> None:
    _get_app()

    window = SetDPIWindow(
        (800, 800),
        [
            DPIStage(800),
            DPIStage(1600),
            DPIStage(3200),
        ],
        2,
    )
    emitted = []

    window.settings_changed.connect(
        lambda x, y, stages, active_stage: emitted.append((x, y, stages, active_stage))
    )

    window._edit_stages()

    assert window.set_dpi_stages_window is not None

    window.set_dpi_stages_window._spinboxes[1].setValue(1800)
    window.set_dpi_stages_window._save()

    assert emitted == []
    assert [stage.dpi for stage in window._stages] == [
        800,
        1800,
        3200,
    ]


def test_matching_stage_is_selected_on_initialization() -> None:
    _get_app()

    window = SetDPIWindow(
        (1600, 1600),
        [
            DPIStage(400),
            DPIStage(800),
            DPIStage(1600),
            DPIStage(2400),
        ],
        3,
    )

    assert [button.isChecked() for button in window.stage_buttons] == [
        False,
        False,
        True,
        False,
    ]


def test_editing_stages_preserves_matching_stage_selection() -> None:
    _get_app()

    window = SetDPIWindow(
        (1600, 1600),
        [
            DPIStage(400),
            DPIStage(800),
            DPIStage(1600),
            DPIStage(2400),
            DPIStage(3200),
        ],
        3,
    )

    window._stages_changed(
        [
            DPIStage(400),
            DPIStage(800),
            DPIStage(1600),
            DPIStage(2400),
        ]
    )

    assert [button.isChecked() for button in window.stage_buttons] == [
        False,
        False,
        True,
        False,
    ]
