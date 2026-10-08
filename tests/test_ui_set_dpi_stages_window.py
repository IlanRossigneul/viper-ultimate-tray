from PySide6.QtWidgets import QApplication

from razer.mouse_state import DPIStage
from ui.set_dpi_stages_window import (
    MAX_STAGES,
    MIN_STAGES,
    SetDPIStagesWindow,
)


def _get_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_window_initializes_stage_spinboxes() -> None:
    _get_app()

    stages = [
        DPIStage(800),
        DPIStage(1600),
        DPIStage(3200),
    ]
    window = SetDPIStagesWindow(stages)

    assert [spinbox.value() for spinbox in window._spinboxes] == [
        800,
        1600,
        3200,
    ]


def test_window_copies_stages() -> None:
    _get_app()

    stages = [
        DPIStage(800),
        DPIStage(1600),
    ]
    window = SetDPIStagesWindow(stages)

    assert window._stages is not stages
    assert window._stages[0] is not stages[0]
    assert window._stages[1] is not stages[1]


def test_add_stage_copies_last_stage_dpi() -> None:
    _get_app()

    window = SetDPIStagesWindow(
        [
            DPIStage(800),
            DPIStage(1600),
            DPIStage(3200),
        ]
    )

    window._add_stage()

    assert [stage.dpi for stage in window._stages] == [
        800,
        1600,
        3200,
        3200,
    ]
    assert [spinbox.value() for spinbox in window._spinboxes] == [
        800,
        1600,
        3200,
        3200,
    ]


def test_add_stage_is_disabled_at_maximum() -> None:
    _get_app()

    window = SetDPIStagesWindow(
        [DPIStage(800)] * MAX_STAGES,
    )

    assert not window._add_button.isEnabled()


def test_remove_stage_removes_last_stage() -> None:
    _get_app()

    window = SetDPIStagesWindow(
        [
            DPIStage(800),
            DPIStage(1600),
            DPIStage(3200),
        ]
    )

    window._remove_stage()

    assert [stage.dpi for stage in window._stages] == [
        800,
        1600,
    ]
    assert [spinbox.value() for spinbox in window._spinboxes] == [
        800,
        1600,
    ]


def test_remove_stage_is_disabled_at_minimum() -> None:
    _get_app()

    window = SetDPIStagesWindow([DPIStage(800)])

    assert len(window._stages) == MIN_STAGES
    assert not window._remove_button.isEnabled()


def test_spinboxes_are_saved_to_stage_values() -> None:
    _get_app()

    original_stages = [
        DPIStage(800),
        DPIStage(1600),
        DPIStage(3200),
    ]
    window = SetDPIStagesWindow(original_stages)
    emitted = []

    window.settings_changed.connect(
        emitted.append,
    )

    window._spinboxes[0].setValue(1000)
    window._spinboxes[1].setValue(1800)
    window._spinboxes[2].setValue(4000)

    window._save()

    assert [stage.dpi for stage in emitted[0]] == [
        1000,
        1800,
        4000,
    ]

    assert [stage.dpi for stage in original_stages] == [
        800,
        1600,
        3200,
    ]


def test_cancel_does_not_emit_settings_changed() -> None:
    _get_app()

    window = SetDPIStagesWindow(
        [
            DPIStage(800),
            DPIStage(1600),
        ]
    )
    emitted = []

    window.settings_changed.connect(
        emitted.append,
    )

    window._spinboxes[0].setValue(1200)
    window.close()

    assert emitted == []
