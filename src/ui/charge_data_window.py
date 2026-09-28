from collections.abc import Callable
from datetime import datetime
from typing import Any

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPaintEvent, QPalette, QPen
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.paths import MENU_ICON_DIR, QMESSAGEBOX_ICON_DIR


class ChargeModelHeader(QHeaderView):
    """Two-level header for the charge model table."""

    _HEADER_HEIGHT = 56
    _GROUP_ROW_HEIGHT = 28

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)

        self.setFixedHeight(self._HEADER_HEIGHT)
        self.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSectionsClickable(False)
        self.setHighlightSections(False)

    def paintEvent(self, event: QPaintEvent) -> None:
        del event

        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        palette = self.palette()

        background = palette.color(QPalette.ColorRole.Button)
        foreground = palette.color(QPalette.ColorRole.ButtonText)
        border = QColor("#666666")

        painter.fillRect(self.rect(), background)

        font = self.font()

        group_font = QFont(font)
        group_font.setBold(True)

        # Percent column spanning both header rows.
        self._draw_cell(
            painter,
            self.sectionViewportPosition(0),
            0,
            self.sectionSize(0),
            self._HEADER_HEIGHT,
            "%",
            foreground,
            group_font,
        )

        # First group: average duration per battery level.
        average_x = self.sectionViewportPosition(1)
        average_width = self.sectionSize(1) + self.sectionSize(2) + self.sectionSize(3)

        self._draw_cell(
            painter,
            average_x,
            0,
            average_width,
            self._GROUP_ROW_HEIGHT,
            "Durée moyenne par %",
            foreground,
            group_font,
        )

        # Second group: cumulative duration up to 100%.
        cumulative_x = self.sectionViewportPosition(4)
        cumulative_width = (
            self.sectionSize(4) + self.sectionSize(5) + self.sectionSize(6)
        )

        self._draw_cell(
            painter,
            cumulative_x,
            0,
            cumulative_width,
            self._GROUP_ROW_HEIGHT,
            "Jusqu'à 100 %",
            foreground,
            group_font,
        )

        # Second-level headers.
        subheader_font = QFont(font)
        subheader_font.setBold(False)

        for column, label in (
            (1, "Filaire"),
            (2, "Sans fil"),
            (3, "Différence"),
            (4, "Filaire"),
            (5, "Sans fil"),
            (6, "Différence"),
        ):
            self._draw_cell(
                painter,
                self.sectionViewportPosition(column),
                self._GROUP_ROW_HEIGHT,
                self.sectionSize(column),
                self._GROUP_ROW_HEIGHT,
                label,
                foreground,
                subheader_font,
            )

        # Horizontal separator between the two header levels.
        painter.setPen(QPen(border))
        painter.drawLine(
            average_x,
            self._GROUP_ROW_HEIGHT,
            cumulative_x + cumulative_width - 1,
            self._GROUP_ROW_HEIGHT,
        )

        # Column separators.
        painter.setPen(QPen(border))

        for column in (1, 2, 4, 5):
            x = (self.sectionViewportPosition(column) + self.sectionSize(column)) - 1
            painter.drawLine(
                x,
                self._GROUP_ROW_HEIGHT,
                x,
                self._HEADER_HEIGHT,
            )

        # Strong group separators.
        painter.setPen(QPen(border, 2))

        for column in (0, 3, 6):
            x = (self.sectionViewportPosition(column) + self.sectionSize(column)) - 1
            painter.drawLine(
                x,
                0,
                x,
                self._HEADER_HEIGHT,
            )

        # Outer bottom border.
        painter.setPen(QPen(border))
        painter.drawLine(
            0,
            self._HEADER_HEIGHT - 1,
            self.width(),
            self._HEADER_HEIGHT - 1,
        )

    @staticmethod
    def _draw_cell(
        painter: QPainter,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        color: QColor,
        font: QFont,
    ) -> None:
        painter.setPen(color)
        painter.setFont(font)

        painter.drawText(
            QRect(x, y, width, height),
            Qt.AlignmentFlag.AlignCenter,
            text,
        )


class ChargeDataWindow(QMainWindow):
    """Charge data window"""

    def __init__(
        self,
        on_update_sample: Callable[[str, str, dict[str, int]], None] | None = None,
        on_delete_sample: Callable[[str, str], None] | None = None,
    ) -> None:
        super().__init__()

        self._on_update_sample = on_update_sample
        self._on_delete_sample = on_delete_sample

        self.setWindowTitle("Données de charge")
        self.setWindowIcon(QIcon(str(MENU_ICON_DIR / "mouse.svg")))
        self.resize(790, 790)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.samples_tab = QWidget()
        self.model_tab = QWidget()

        self.tabs.addTab(self.samples_tab, "Échantillons")
        self.tabs.addTab(self.model_tab, "Modèle")

        self._sample_backup: dict[str, Any] | None = None

        self._setup_samples_tab()
        self._setup_model_tab()

    def _setup_samples_tab(self) -> None:
        layout = QVBoxLayout(self.samples_tab)

        samples_group = QGroupBox("Échantillons")
        samples_layout = QVBoxLayout(samples_group)

        self.samples_tree = QTreeWidget()
        self.samples_tree.setHeaderHidden(True)
        self.samples_tree.currentItemChanged.connect(
            self._handle_sample_selection,
        )

        samples_layout.addWidget(self.samples_tree)

        detail_group = QGroupBox("Détail de l'échantillon")
        detail_layout = QVBoxLayout(detail_group)

        self.sample_mode_label = QLabel()
        self.sample_created_at_label = QLabel()

        self.sample_transitions_table = QTableWidget()
        self.sample_transitions_table.setColumnCount(2)
        self.sample_transitions_table.verticalHeader().setVisible(False)
        self.sample_transitions_table.setHorizontalHeaderLabels(
            ["%", "Durée par %"],
        )
        self.sample_transitions_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers,
        )
        self.sample_transitions_table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection,
        )

        detail_layout.addWidget(self.sample_mode_label)
        detail_layout.addWidget(self.sample_created_at_label)
        detail_layout.addWidget(self.sample_transitions_table)

        self.sample_help_label = QLabel(
            "Une durée peut être définie à 0 ou laissée vide pour que ce "
            "niveau ne soit pas pris en compte. Dans ce cas, tous les "
            "niveaux suivants doivent également avoir une durée à 0 ou "
            "être laissés vides.",
        )
        self.sample_help_label.setWordWrap(True)
        self.sample_help_label.setStyleSheet("font-size: 9pt;")

        detail_layout.addWidget(self.sample_help_label)

        buttons_layout = QHBoxLayout()

        self.edit_sample_button = QPushButton("Modifier")
        self.save_sample_button = QPushButton("Enregistrer")
        self.cancel_sample_button = QPushButton("Annuler")
        self.delete_sample_button = QPushButton("Supprimer")

        self.save_sample_button.hide()
        self.cancel_sample_button.hide()

        self.edit_sample_button.clicked.connect(self._edit_sample)
        self.save_sample_button.clicked.connect(self._save_sample)
        self.cancel_sample_button.clicked.connect(self._cancel_edit)
        self.delete_sample_button.clicked.connect(self._delete_sample)

        buttons_layout.addWidget(self.edit_sample_button)
        buttons_layout.addWidget(self.save_sample_button)
        buttons_layout.addWidget(self.cancel_sample_button)
        buttons_layout.addWidget(self.delete_sample_button)

        detail_layout.addLayout(buttons_layout)

        layout.addWidget(samples_group, 4)
        layout.addWidget(detail_group, 10)

        samples_quit_button = QPushButton("Quitter")
        samples_quit_button.clicked.connect(self.close)

        layout.addWidget(samples_quit_button)

    def _setup_model_tab(self) -> None:
        layout = QVBoxLayout(self.model_tab)

        self.model_table = QTableWidget()
        self.model_table.setColumnCount(7)
        self.model_table.verticalHeader().setVisible(False)

        self.model_table.setHorizontalHeaderLabels(
            [
                "%",
                "Filaire",
                "Sans fil",
                "Différence",
                "Filaire",
                "Sans fil",
                "Différence",
            ],
        )

        self.model_table.setHorizontalHeader(
            ChargeModelHeader(self.model_table),
        )

        self.model_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers,
        )
        self.model_table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection,
        )

        layout.addWidget(self.model_table)

        model_quit_button = QPushButton("Quitter")
        model_quit_button.clicked.connect(self.close)

        layout.addWidget(model_quit_button)

    def set_samples(self, samples: dict[str, list[dict[str, Any]]]) -> None:
        current = self.samples_tree.currentItem()

        selected_mode: str | None = None
        selected_created_at: str | None = None

        if current is not None and current.childCount() == 0:
            selected_mode, selected_sample = current.data(
                0,
                Qt.ItemDataRole.UserRole,
            )
            selected_created_at = selected_sample["created_at"]

        self.samples_tree.clear()
        self._clear_sample_detail()

        selected_item: QTreeWidgetItem | None = None

        for mode, label in (
            ("wired", "Filaire"),
            ("wireless", "Sans fil"),
        ):
            samples_group = QTreeWidgetItem([label])
            self.samples_tree.addTopLevelItem(samples_group)

            for sample in samples.get(mode, []):
                created_at = sample["created_at"]
                item = QTreeWidgetItem(
                    [self._format_created_at(created_at)],
                )
                item.setData(0, Qt.ItemDataRole.UserRole, (mode, sample))
                samples_group.addChild(item)

                if mode == selected_mode and created_at == selected_created_at:
                    selected_item = item

            samples_group.setExpanded(True)

        if selected_item is not None:
            self.samples_tree.setCurrentItem(selected_item)

    def set_model(self, model: dict[str, Any]) -> None:
        wired_average = model.get("wired", {}).get("average", {})
        wireless_average = model.get("wireless", {}).get("average", {})

        levels = sorted(
            set(wired_average) | set(wireless_average),
            key=int,
        )

        self.model_table.setRowCount(len(levels))

        wired_cumulative = self._calculate_cumulative_durations(
            wired_average,
        )
        wireless_cumulative = self._calculate_cumulative_durations(
            wireless_average,
        )

        for row, level in enumerate(levels):
            wired_duration = wired_average.get(level)
            wireless_duration = wireless_average.get(level)

            # Battery level.
            self.model_table.setItem(
                row,
                0,
                QTableWidgetItem(f"{level} %"),
            )

            # Average duration per level.
            if wired_duration is not None:
                self.model_table.setItem(
                    row,
                    1,
                    QTableWidgetItem(f"{wired_duration} s"),
                )

            if wireless_duration is not None:
                self.model_table.setItem(
                    row,
                    2,
                    QTableWidgetItem(f"{wireless_duration} s"),
                )

            if wired_duration is not None and wireless_duration is not None:
                difference = wireless_duration - wired_duration

                difference_item = QTableWidgetItem(
                    f"{difference:+d} s",
                )
                font = difference_item.font()
                font.setBold(True)
                difference_item.setFont(font)

                if difference < 0:
                    difference_item.setForeground(QColor("#FF0000"))
                else:
                    difference_item.setForeground(QColor("#00FF00"))

                self.model_table.setItem(
                    row,
                    3,
                    difference_item,
                )

            # Cumulative duration up to 100%.
            if wired_duration is not None:
                self.model_table.setItem(
                    row,
                    4,
                    QTableWidgetItem(
                        f"{wired_cumulative[level]} s",
                    ),
                )

            if wireless_duration is not None:
                self.model_table.setItem(
                    row,
                    5,
                    QTableWidgetItem(
                        f"{wireless_cumulative[level]} s",
                    ),
                )

            if level in wired_cumulative and level in wireless_cumulative:
                difference = wireless_cumulative[level] - wired_cumulative[level]

                difference_item = QTableWidgetItem(
                    f"{difference:+d} s",
                )
                font = difference_item.font()
                font.setBold(True)
                difference_item.setFont(font)

                if difference < 0:
                    difference_item.setForeground(QColor("#FF0000"))
                else:
                    difference_item.setForeground(QColor("#00FF00"))

                self.model_table.setItem(
                    row,
                    6,
                    difference_item,
                )

        self.model_table.resizeColumnsToContents()

        for column, minimum_width in enumerate(
            (50, 90, 90, 100, 110, 110, 100),
        ):
            self.model_table.setColumnWidth(
                column,
                max(
                    self.model_table.columnWidth(column),
                    minimum_width,
                ),
            )

    @staticmethod
    def _calculate_cumulative_durations(
        average: dict[str, int],
    ) -> dict[str, int]:
        cumulative: dict[str, int] = {}
        total = 0

        for level in sorted(average, key=int, reverse=True):
            total += average[level]
            cumulative[level] = total

        return cumulative

    def _handle_sample_selection(
        self,
        current: QTreeWidgetItem | None,
        previous: QTreeWidgetItem | None,
    ) -> None:
        del previous

        if current is None or current.childCount() > 0:
            self._clear_sample_detail()
            return

        mode, sample = current.data(0, Qt.ItemDataRole.UserRole)

        self.sample_mode_label.setText(
            f"Mode : {'Filaire' if mode == 'wired' else 'Sans fil'}",
        )
        self.sample_created_at_label.setText(
            f"Créé le : {self._format_created_at(sample['created_at'])}",
        )

        transitions = sample["transitions"]

        self.sample_transitions_table.setRowCount(len(transitions))

        for row, (level, duration) in enumerate(transitions.items()):
            self.sample_transitions_table.setItem(
                row,
                0,
                QTableWidgetItem(f"{level} %"),
            )
            self.sample_transitions_table.setItem(
                row,
                1,
                QTableWidgetItem(f"{duration} s"),
            )

        self.sample_transitions_table.resizeColumnsToContents()

    def _clear_sample_detail(self) -> None:
        self.sample_mode_label.clear()
        self.sample_created_at_label.clear()
        self.sample_transitions_table.setRowCount(0)

    @staticmethod
    def _format_created_at(created_at: str) -> str:
        return datetime.fromisoformat(created_at).strftime(
            "%d-%m-%Y_%H:%M:%S",
        )

    def _edit_sample(self) -> None:
        current = self.samples_tree.currentItem()

        if current is None or current.childCount() > 0:
            return

        _, sample = current.data(0, Qt.ItemDataRole.UserRole)

        self._sample_backup = {
            "transitions": sample["transitions"].copy(),
        }

        self.sample_transitions_table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked
            | QTableWidget.EditTrigger.EditKeyPressed
            | QTableWidget.EditTrigger.AnyKeyPressed,
        )

        for row in range(self.sample_transitions_table.rowCount()):
            item = self.sample_transitions_table.item(row, 0)

            if item is not None:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        for row in range(self.sample_transitions_table.rowCount()):
            item = self.sample_transitions_table.item(row, 1)

            if item is not None:
                item.setText(item.text().removesuffix(" s"))

        self.edit_sample_button.hide()
        self.delete_sample_button.hide()
        self.save_sample_button.show()
        self.cancel_sample_button.show()

    def _save_sample(self) -> None:
        durations: list[int | None] = []
        ignored_levels_started = False

        for row in range(self.sample_transitions_table.rowCount()):
            item = self.sample_transitions_table.item(row, 1)

            if item is None:
                value = ""
            else:
                value = item.text().strip()

            if not value:
                durations.append(None)
                ignored_levels_started = True
                continue

            try:
                duration = int(value)
            except ValueError:
                self._show_invalid_save_message()
                return

            if duration < 0:
                self._show_invalid_save_message()
                return

            if ignored_levels_started and duration > 0:
                self._show_invalid_save_message()
                return

            durations.append(duration)

            if duration == 0:
                ignored_levels_started = True

        current = self.samples_tree.currentItem()

        if current is None or current.childCount() > 0:
            return

        mode, sample = current.data(0, Qt.ItemDataRole.UserRole)

        transitions: dict[str, int] = {}

        for row, duration in enumerate(durations):
            if duration is None or duration == 0:
                break

            level_item = self.sample_transitions_table.item(row, 0)

            if level_item is None:
                continue

            level = level_item.text().removesuffix(" %")
            transitions[level] = duration

        if self._on_update_sample is not None:
            self._on_update_sample(
                mode,
                sample["created_at"],
                transitions,
            )

        sample["transitions"] = transitions

        self._sample_backup = None

        self.sample_transitions_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers,
        )

        for row, duration in enumerate(durations):
            item = self.sample_transitions_table.item(row, 1)

            if item is None:
                continue

            if duration is None:
                item.setText("")
            else:
                item.setText(f"{duration} s")

        self.edit_sample_button.show()
        self.delete_sample_button.show()
        self.save_sample_button.hide()
        self.cancel_sample_button.hide()

        message_box = QMessageBox(self)
        message_box.setWindowTitle("Modifications enregistrées")
        message_box.setIconPixmap(
            QIcon(str(QMESSAGEBOX_ICON_DIR / "info.svg")).pixmap(48, 48),
        )
        message_box.setText("Les modifications ont été enregistrées avec succès.")
        message_box.exec()

    def _show_invalid_save_message(self) -> None:
        message_box = QMessageBox(self)
        message_box.setWindowTitle("Modifications non enregistrées")
        message_box.setIconPixmap(
            QIcon(str(QMESSAGEBOX_ICON_DIR / "warning.svg")).pixmap(48, 48),
        )
        message_box.setText("Les modifications n'ont pas été prises en compte.")
        message_box.setInformativeText("Vérifiez les valeurs saisies.")
        message_box.exec()

    def _cancel_edit(self) -> None:
        if self._sample_backup is None:
            return

        transitions = self._sample_backup["transitions"]

        for row, duration in enumerate(transitions.values()):
            item = self.sample_transitions_table.item(row, 1)

            if item is not None:
                item.setText(f"{duration} s")

        self._sample_backup = None

        self.sample_transitions_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers,
        )

        self.edit_sample_button.show()
        self.delete_sample_button.show()
        self.save_sample_button.hide()
        self.cancel_sample_button.hide()

    def _delete_sample(self) -> None:
        current = self.samples_tree.currentItem()

        if current is None or current.childCount() > 0:
            return

        mode, sample = current.data(
            0,
            Qt.ItemDataRole.UserRole,
        )

        message_box = QMessageBox(self)
        message_box.setWindowTitle("Supprimer l'échantillon ?")
        message_box.setIconPixmap(
            QIcon(str(QMESSAGEBOX_ICON_DIR / "question.svg")).pixmap(48, 48),
        )
        message_box.setText("Voulez-vous vraiment supprimer cet échantillon ?")
        message_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        message_box.setDefaultButton(QMessageBox.StandardButton.No)

        answer = message_box.exec()

        if answer != QMessageBox.StandardButton.Yes:
            return

        if self._on_delete_sample is not None:
            self._on_delete_sample(
                mode,
                sample["created_at"],
            )

        self._sample_backup = None

        self.samples_tree.clearSelection()
        self.samples_tree.setCurrentItem(None)
        self._clear_sample_detail()

        self.edit_sample_button.show()
        self.delete_sample_button.show()
        self.save_sample_button.hide()
        self.cancel_sample_button.hide()

        message_box = QMessageBox(self)
        message_box.setWindowTitle("Échantillon supprimé")
        message_box.setIconPixmap(
            QIcon(str(QMESSAGEBOX_ICON_DIR / "info.svg")).pixmap(48, 48),
        )
        message_box.setText("L'échantillon a été supprimé avec succès.")
        message_box.exec()

    def closeEvent(self, event) -> None:
        self._sample_backup = None

        self.sample_transitions_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers,
        )

        self.edit_sample_button.show()
        self.delete_sample_button.show()
        self.save_sample_button.hide()
        self.cancel_sample_button.hide()

        self.samples_tree.clearSelection()
        self.samples_tree.setCurrentItem(None)
        self._clear_sample_detail()

        event.accept()
