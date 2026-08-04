from collections.abc import Callable

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

from razer.mouse_state import DPIStage


def create_dpi_stage_menu(
    stage_menu: Gtk.Menu,
    stages: list[DPIStage],
    callback: Callable[[int], None],
) -> list[Gtk.RadioMenuItem]:
    stage_items: list[Gtk.RadioMenuItem] = []

    stage_group = None

    for index, stage in enumerate(stages, start=1):
        item = Gtk.RadioMenuItem.new_with_label(stage_group, f"{stage.x:>4}")

        stage_group = item.get_group()

        def on_toggled(
            item,
            stage: int = index,
        ) -> None:
            if item.get_active():
                callback(stage)

        item.connect("toggled", on_toggled)

        stage_menu.append(item)
        stage_items.append(item)

    return stage_items