from typing import Any

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox, QTableWidget

from ui.charge_data_window import ChargeDataWindow


@pytest.fixture
def app() -> QApplication:
    application = QApplication.instance()

    if application is None:
        application = QApplication([])

    return application


@pytest.fixture
def samples() -> dict[str, list[dict[str, Any]]]:
    return {
        "wired": [
            {
                "created_at": "2026-07-29T11:44:19+02:00",
                "transitions": {
                    "0": 126,
                    "1": 84,
                    "2": 86,
                    "4": 100,
                },
            },
        ],
        "wireless": [
            {
                "created_at": "2026-08-05T09:42:26+02:00",
                "transitions": {
                    "0": 125,
                    "1": 83,
                    "2": 85,
                },
            },
        ],
    }


def test_initial_state(app: QApplication) -> None:
    window = ChargeDataWindow()
    window.show()
    app.processEvents()

    assert window.tabs.count() == 2
    assert window.tabs.tabText(0) == "Échantillons"
    assert window.tabs.tabText(1) == "Modèle"

    assert window.edit_sample_button.isVisible()
    assert window.delete_sample_button.isVisible()
    assert not window.save_sample_button.isVisible()
    assert not window.cancel_sample_button.isVisible()

    assert (
        window.sample_transitions_table.editTriggers()
        == QTableWidget.EditTrigger.NoEditTriggers
    )

    window.close()


def test_set_samples(
    app: QApplication,
    samples: dict[str, list[dict[str, Any]]],
) -> None:
    window = ChargeDataWindow()
    window.set_samples(samples)

    assert window.samples_tree.topLevelItemCount() == 2

    wired_group = window.samples_tree.topLevelItem(0)
    wireless_group = window.samples_tree.topLevelItem(1)

    assert wired_group is not None
    assert wireless_group is not None

    assert wired_group.text(0) == "Filaire"
    assert wireless_group.text(0) == "Sans fil"

    assert wired_group.isExpanded()
    assert wireless_group.isExpanded()

    assert wired_group.childCount() == 1
    assert wireless_group.childCount() == 1

    wired_item = wired_group.child(0)
    wireless_item = wireless_group.child(0)

    assert wired_item is not None
    assert wireless_item is not None

    assert wired_item.text(0) == "29-07-2026_11:44:19"
    assert wireless_item.text(0) == "05-08-2026_09:42:26"

    assert wired_item.data(0, Qt.ItemDataRole.UserRole) == (
        "wired",
        samples["wired"][0],
    )
    assert wireless_item.data(0, Qt.ItemDataRole.UserRole) == (
        "wireless",
        samples["wireless"][0],
    )

    window.close()


def test_select_sample(
    app: QApplication,
    samples: dict[str, list[dict[str, Any]]],
) -> None:
    window = ChargeDataWindow()
    window.set_samples(samples)

    wired_group = window.samples_tree.topLevelItem(0)
    assert wired_group is not None

    wired_item = wired_group.child(0)
    assert wired_item is not None

    window.samples_tree.setCurrentItem(wired_item)
    app.processEvents()

    assert window.sample_mode_label.text() == "Mode : Filaire"
    assert window.sample_created_at_label.text() == ("Créé le : 29-07-2026_11:44:19")

    table = window.sample_transitions_table

    assert table.rowCount() == 4

    assert table.item(0, 0).text() == "0 %"
    assert table.item(0, 1).text() == "126 s"

    assert table.item(1, 0).text() == "1 %"
    assert table.item(1, 1).text() == "84 s"

    assert table.item(2, 0).text() == "2 %"
    assert table.item(2, 1).text() == "86 s"

    assert table.item(3, 0).text() == "4 %"
    assert table.item(3, 1).text() == "100 s"

    window.close()


def test_select_group_clears_detail(
    app: QApplication,
    samples: dict[str, list[dict[str, Any]]],
) -> None:
    window = ChargeDataWindow()
    window.set_samples(samples)

    wired_group = window.samples_tree.topLevelItem(0)
    assert wired_group is not None

    wired_item = wired_group.child(0)
    assert wired_item is not None

    window.samples_tree.setCurrentItem(wired_item)
    app.processEvents()

    assert window.sample_transitions_table.rowCount() == 4

    window.samples_tree.setCurrentItem(wired_group)
    app.processEvents()

    assert window.sample_mode_label.text() == ""
    assert window.sample_created_at_label.text() == ""
    assert window.sample_transitions_table.rowCount() == 0

    window.close()


def test_edit_sample(
    app: QApplication,
    samples: dict[str, list[dict[str, Any]]],
) -> None:
    window = ChargeDataWindow()
    window.set_samples(samples)
    window.show()
    app.processEvents()

    wired_group = window.samples_tree.topLevelItem(0)
    assert wired_group is not None

    wired_item = wired_group.child(0)
    assert wired_item is not None

    window.samples_tree.setCurrentItem(wired_item)
    app.processEvents()

    window._edit_sample()

    assert window._sample_backup == {
        "transitions": samples["wired"][0]["transitions"],
    }

    assert window.sample_transitions_table.editTriggers() == (
        QTableWidget.EditTrigger.DoubleClicked
        | QTableWidget.EditTrigger.EditKeyPressed
        | QTableWidget.EditTrigger.AnyKeyPressed
    )

    assert not (
        window.sample_transitions_table.item(0, 0).flags() & Qt.ItemFlag.ItemIsEditable
    )
    assert window.sample_transitions_table.item(0, 1).text() == "126"

    assert not window.edit_sample_button.isVisible()
    assert not window.delete_sample_button.isVisible()
    assert window.save_sample_button.isVisible()
    assert window.cancel_sample_button.isVisible()

    window.close()


def test_cancel_edit_restores_values(
    app: QApplication,
    samples: dict[str, list[dict[str, Any]]],
) -> None:
    window = ChargeDataWindow()
    window.set_samples(samples)
    window.show()
    app.processEvents()

    wired_group = window.samples_tree.topLevelItem(0)
    assert wired_group is not None

    wired_item = wired_group.child(0)
    assert wired_item is not None

    window.samples_tree.setCurrentItem(wired_item)
    app.processEvents()

    window._edit_sample()

    duration_item = window.sample_transitions_table.item(0, 1)
    assert duration_item is not None

    duration_item.setText("999")

    window._cancel_edit()

    assert window._sample_backup is None
    assert duration_item.text() == "126 s"

    assert (
        window.sample_transitions_table.editTriggers()
        == QTableWidget.EditTrigger.NoEditTriggers
    )

    assert window.edit_sample_button.isVisible()
    assert window.delete_sample_button.isVisible()
    assert not window.save_sample_button.isVisible()
    assert not window.cancel_sample_button.isVisible()

    window.close()


def test_save_sample(
    app: QApplication,
    samples: dict[str, list[dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    updated: list[tuple[str, str, dict[str, int]]] = []

    def on_update(
        mode: str,
        created_at: str,
        transitions: dict[str, int],
    ) -> None:
        updated.append((mode, created_at, transitions))

    window = ChargeDataWindow(on_update_sample=on_update)
    window.set_samples(samples)
    window.show()
    app.processEvents()

    wired_group = window.samples_tree.topLevelItem(0)
    assert wired_group is not None

    wired_item = wired_group.child(0)
    assert wired_item is not None

    window.samples_tree.setCurrentItem(wired_item)
    app.processEvents()

    window._edit_sample()

    duration_item = window.sample_transitions_table.item(0, 1)
    assert duration_item is not None
    duration_item.setText("130")

    monkeypatch.setattr(
        QMessageBox,
        "exec",
        lambda self: QMessageBox.StandardButton.Ok,
    )

    window._save_sample()

    assert updated == [
        (
            "wired",
            "2026-07-29T11:44:19+02:00",
            {
                "0": 130,
                "1": 84,
                "2": 86,
                "4": 100,
            },
        ),
    ]

    assert samples["wired"][0]["transitions"] == {
        "0": 130,
        "1": 84,
        "2": 86,
        "4": 100,
    }

    assert window._sample_backup is None

    assert (
        window.sample_transitions_table.editTriggers()
        == QTableWidget.EditTrigger.NoEditTriggers
    )

    duration_item = window.sample_transitions_table.item(0, 1)
    assert duration_item is not None
    assert duration_item.text() == "130 s"

    assert window.edit_sample_button.isVisible()
    assert window.delete_sample_button.isVisible()
    assert not window.save_sample_button.isVisible()
    assert not window.cancel_sample_button.isVisible()

    window.close()


@pytest.mark.parametrize(
    "value",
    [
        "abc",
        "-1",
    ],
)
def test_save_sample_rejects_invalid_duration(
    app: QApplication,
    samples: dict[str, list[dict[str, Any]]],
    value: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    updated: list[tuple[str, str, dict[str, int]]] = []

    def on_update(
        mode: str,
        created_at: str,
        transitions: dict[str, int],
    ) -> None:
        updated.append((mode, created_at, transitions))

    window = ChargeDataWindow(on_update_sample=on_update)
    window.set_samples(samples)

    wired_group = window.samples_tree.topLevelItem(0)
    assert wired_group is not None

    wired_item = wired_group.child(0)
    assert wired_item is not None

    window.samples_tree.setCurrentItem(wired_item)
    app.processEvents()

    window._edit_sample()

    duration_item = window.sample_transitions_table.item(0, 1)
    assert duration_item is not None
    duration_item.setText(value)

    monkeypatch.setattr(
        QMessageBox,
        "exec",
        lambda self: QMessageBox.StandardButton.Ok,
    )

    window._save_sample()

    assert updated == []
    assert duration_item.text() == value

    window.close()


def test_save_sample_rejects_duration_after_started_sequence_is_ignored(
    app: QApplication,
    samples: dict[str, list[dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    updated: list[tuple[str, str, dict[str, int]]] = []

    def on_update(
        mode: str,
        created_at: str,
        transitions: dict[str, int],
    ) -> None:
        updated.append((mode, created_at, transitions))

    window = ChargeDataWindow(on_update_sample=on_update)
    window.set_samples(samples)

    wired_group = window.samples_tree.topLevelItem(0)
    assert wired_group is not None

    wired_item = wired_group.child(0)
    assert wired_item is not None

    window.samples_tree.setCurrentItem(wired_item)
    app.processEvents()

    window._edit_sample()

    first_duration = window.sample_transitions_table.item(0, 1)
    second_duration = window.sample_transitions_table.item(1, 1)

    assert first_duration is not None
    assert second_duration is not None

    first_duration.setText("50")
    second_duration.setText("0")

    third_duration = window.sample_transitions_table.item(2, 1)
    assert third_duration is not None

    third_duration.setText("86")

    monkeypatch.setattr(
        QMessageBox,
        "exec",
        lambda self: QMessageBox.StandardButton.Ok,
    )

    window._save_sample()

    assert updated == []

    window.close()


def test_save_sample_allows_zero_and_blank_tail(
    app: QApplication,
    samples: dict[str, list[dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    updated: list[tuple[str, str, dict[str, int]]] = []

    def on_update(
        mode: str,
        created_at: str,
        transitions: dict[str, int],
    ) -> None:
        updated.append((mode, created_at, transitions))

    window = ChargeDataWindow(on_update_sample=on_update)
    window.set_samples(samples)

    wired_group = window.samples_tree.topLevelItem(0)
    assert wired_group is not None

    wired_item = wired_group.child(0)
    assert wired_item is not None

    window.samples_tree.setCurrentItem(wired_item)
    app.processEvents()

    window._edit_sample()

    first_duration = window.sample_transitions_table.item(0, 1)
    second_duration = window.sample_transitions_table.item(1, 1)
    third_duration = window.sample_transitions_table.item(2, 1)
    fourth_duration = window.sample_transitions_table.item(3, 1)

    assert first_duration is not None
    assert second_duration is not None
    assert third_duration is not None
    assert fourth_duration is not None

    first_duration.setText("0")
    second_duration.setText("")
    third_duration.setText("")
    fourth_duration.setText("")

    monkeypatch.setattr(
        QMessageBox,
        "exec",
        lambda self: QMessageBox.StandardButton.Ok,
    )

    window._save_sample()

    assert updated == [
        (
            "wired",
            "2026-07-29T11:44:19+02:00",
            {},
        ),
    ]

    assert samples["wired"][0]["transitions"] == {}

    window.close()


def test_save_sample_allows_leading_and_trailing_zeros(
    app: QApplication,
    samples: dict[str, list[dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    updated: list[tuple[str, str, dict[str, int]]] = []

    def on_update(
        mode: str,
        created_at: str,
        transitions: dict[str, int],
    ) -> None:
        updated.append((mode, created_at, transitions))

    samples["wired"][0]["transitions"].update(
        {
            "5": 0,
            "6": 0,
        }
    )

    window = ChargeDataWindow(on_update_sample=on_update)
    window.set_samples(samples)

    wired_group = window.samples_tree.topLevelItem(0)
    assert wired_group is not None

    wired_item = wired_group.child(0)
    assert wired_item is not None

    window.samples_tree.setCurrentItem(wired_item)
    app.processEvents()

    window._edit_sample()

    first_duration = window.sample_transitions_table.item(0, 1)
    second_duration = window.sample_transitions_table.item(1, 1)
    third_duration = window.sample_transitions_table.item(2, 1)
    fourth_duration = window.sample_transitions_table.item(3, 1)
    fifth_duration = window.sample_transitions_table.item(4, 1)
    sixth_duration = window.sample_transitions_table.item(5, 1)

    assert first_duration is not None
    assert second_duration is not None
    assert third_duration is not None
    assert fourth_duration is not None
    assert fifth_duration is not None
    assert sixth_duration is not None

    first_duration.setText("0")
    second_duration.setText("0")
    third_duration.setText("80")
    fourth_duration.setText("120")
    fifth_duration.setText("0")
    sixth_duration.setText("0")

    monkeypatch.setattr(
        QMessageBox,
        "exec",
        lambda self: QMessageBox.StandardButton.Ok,
    )

    window._save_sample()

    assert updated == [
        (
            "wired",
            "2026-07-29T11:44:19+02:00",
            {
                "2": 80,
                "4": 120,
            },
        ),
    ]

    assert samples["wired"][0]["transitions"] == {
        "2": 80,
        "4": 120,
    }

    window.close()


def test_set_samples_preserves_selection(
    app: QApplication,
    samples: dict[str, list[dict[str, Any]]],
) -> None:
    window = ChargeDataWindow()
    window.set_samples(samples)

    wired_group = window.samples_tree.topLevelItem(0)
    assert wired_group is not None

    wired_item = wired_group.child(0)
    assert wired_item is not None

    window.samples_tree.setCurrentItem(wired_item)
    app.processEvents()

    window.set_samples(samples)

    current = window.samples_tree.currentItem()

    assert current is not None
    assert current.text(0) == "29-07-2026_11:44:19"

    mode, sample = current.data(0, Qt.ItemDataRole.UserRole)

    assert mode == "wired"
    assert sample == samples["wired"][0]

    window.close()


def test_delete_sample_without_selection(
    app: QApplication,
) -> None:
    deleted: list[tuple[str, str]] = []

    def on_delete(mode: str, created_at: str) -> None:
        deleted.append((mode, created_at))

    window = ChargeDataWindow(on_delete_sample=on_delete)

    window._delete_sample()

    assert deleted == []

    window.close()


def test_delete_sample_cancelled(
    app: QApplication,
    samples: dict[str, list[dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deleted: list[tuple[str, str]] = []

    def on_delete(mode: str, created_at: str) -> None:
        deleted.append((mode, created_at))

    window = ChargeDataWindow(on_delete_sample=on_delete)
    window.set_samples(samples)
    window.show()
    app.processEvents()

    wired_group = window.samples_tree.topLevelItem(0)
    assert wired_group is not None

    wired_item = wired_group.child(0)
    assert wired_item is not None

    window.samples_tree.setCurrentItem(wired_item)
    app.processEvents()

    monkeypatch.setattr(
        QMessageBox,
        "exec",
        lambda self: QMessageBox.StandardButton.No,
    )

    window._delete_sample()

    assert deleted == []
    assert window.samples_tree.currentItem() is wired_item
    assert window.sample_mode_label.text() == "Mode : Filaire"
    assert window.sample_transitions_table.rowCount() == 4

    window.close()


def test_delete_sample(
    app: QApplication,
    samples: dict[str, list[dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deleted: list[tuple[str, str]] = []

    def on_delete(mode: str, created_at: str) -> None:
        deleted.append((mode, created_at))

    window = ChargeDataWindow(on_delete_sample=on_delete)
    window.set_samples(samples)
    window.show()
    app.processEvents()

    wired_group = window.samples_tree.topLevelItem(0)
    assert wired_group is not None

    wired_item = wired_group.child(0)
    assert wired_item is not None

    window.samples_tree.setCurrentItem(wired_item)
    app.processEvents()

    monkeypatch.setattr(
        QMessageBox,
        "exec",
        lambda self: QMessageBox.StandardButton.Yes,
    )

    window._delete_sample()

    assert deleted == [
        ("wired", "2026-07-29T11:44:19+02:00"),
    ]

    assert window.samples_tree.currentItem() is None
    assert window.sample_mode_label.text() == ""
    assert window.sample_created_at_label.text() == ""
    assert window.sample_transitions_table.rowCount() == 0

    assert window._sample_backup is None

    assert window.edit_sample_button.isVisible()
    assert window.delete_sample_button.isVisible()
    assert not window.save_sample_button.isVisible()
    assert not window.cancel_sample_button.isVisible()

    window.close()


def test_close_event_resets_state(
    app: QApplication,
    samples: dict[str, list[dict[str, Any]]],
) -> None:
    window = ChargeDataWindow()
    window.set_samples(samples)

    wired_group = window.samples_tree.topLevelItem(0)
    assert wired_group is not None

    wired_item = wired_group.child(0)
    assert wired_item is not None

    window.samples_tree.setCurrentItem(wired_item)
    app.processEvents()

    window._edit_sample()
    window.close()

    assert window._sample_backup is None
    assert window.samples_tree.currentItem() is None
    assert window.sample_mode_label.text() == ""
    assert window.sample_created_at_label.text() == ""
    assert window.sample_transitions_table.rowCount() == 0


def test_set_model(app: QApplication) -> None:
    window = ChargeDataWindow()

    model = {
        "wired": {
            "statistics": {
                "sample_count": 3,
                "last_updated": "2026-09-26T00:00:00",
            },
            "average": {
                "0": 120,
                "1": 118,
                "10": 105,
            },
        },
        "wireless": {
            "statistics": {
                "sample_count": 2,
                "last_updated": "2026-09-26T00:00:00",
            },
            "average": {
                "0": 150,
                "1": 148,
                "10": 130,
            },
        },
    }

    window.set_model(model)

    table = window.model_table

    assert table.rowCount() == 3

    assert table.item(0, 0).text() == "0 %"
    assert table.item(0, 1).text() == "120 s"
    assert table.item(0, 2).text() == "150 s"
    assert table.item(0, 3).text() == "+30 s"
    assert table.item(0, 4).text() == "343 s"
    assert table.item(0, 5).text() == "428 s"
    assert table.item(0, 6).text() == "+85 s"

    assert table.item(1, 0).text() == "1 %"
    assert table.item(1, 1).text() == "118 s"
    assert table.item(1, 2).text() == "148 s"
    assert table.item(1, 3).text() == "+30 s"
    assert table.item(1, 4).text() == "223 s"
    assert table.item(1, 5).text() == "278 s"
    assert table.item(1, 6).text() == "+55 s"

    assert table.item(2, 0).text() == "10 %"
    assert table.item(2, 1).text() == "105 s"
    assert table.item(2, 2).text() == "130 s"
    assert table.item(2, 3).text() == "+25 s"
    assert table.item(2, 4).text() == "105 s"
    assert table.item(2, 5).text() == "130 s"
    assert table.item(2, 6).text() == "+25 s"

    assert table.editTriggers() == QTableWidget.EditTrigger.NoEditTriggers
    assert table.selectionMode() == QTableWidget.SelectionMode.NoSelection

    window.close()


def test_set_model_empty_clears_table(app: QApplication) -> None:
    window = ChargeDataWindow()

    window.set_model(
        {
            "wired": {
                "average": {"0": 120, "1": 118},
            },
            "wireless": {
                "average": {"0": 150, "1": 148},
            },
        }
    )

    assert window.model_table.rowCount() == 2

    window.set_model(
        {
            "wired": {"average": {}},
            "wireless": {"average": {}},
        }
    )

    assert window.model_table.rowCount() == 0

    window.close()


def test_set_model_missing_modes_clears_table(
    app: QApplication,
) -> None:
    window = ChargeDataWindow()

    window.set_model(
        {
            "wired": {"average": {"0": 120}},
            "wireless": {"average": {"0": 150}},
        }
    )

    assert window.model_table.rowCount() == 1

    window.set_model({})

    assert window.model_table.rowCount() == 0

    window.close()


def test_set_model_clears_stale_cells(
    app: QApplication,
) -> None:
    window = ChargeDataWindow()

    window.set_model(
        {
            "wired": {
                "average": {
                    "0": 120,
                    "1": 118,
                    "10": 105,
                },
            },
            "wireless": {
                "average": {
                    "0": 150,
                    "1": 148,
                    "10": 130,
                },
            },
        }
    )

    window.set_model(
        {
            "wired": {
                "average": {
                    "0": 120,
                    "1": 118,
                    "10": 105,
                },
            },
            "wireless": {
                "average": {},
            },
        }
    )

    table = window.model_table

    assert table.rowCount() == 3

    for row in range(3):
        assert table.item(row, 1) is not None
        assert table.item(row, 2) is None
        assert table.item(row, 3) is None
        assert table.item(row, 4) is not None
        assert table.item(row, 5) is None
        assert table.item(row, 6) is None

    window.close()
