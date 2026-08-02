import gi

gi.require_version(
    "Gtk",
    "3.0",
)

from gi.repository import Gtk
from collections.abc import Callable


def create_dpi_stage_menu(
    stage_menu: Gtk.Menu,
    stages,
    callback: Callable[[int], None],
) -> list[Gtk.RadioMenuItem]:
    stage_items = []

    stage_group = None

    for index, stage in enumerate(
        stages,
        start=1,
    ):
        item = Gtk.RadioMenuItem.new_with_label(
            stage_group,
            f"{stage.x:>4}",
        )

        stage_group = item.get_group()

        item.connect(
            "toggled",
            lambda item, stage=index:
                callback(stage)
                if item.get_active()
                else None,
        )

        stage_menu.append(item)
        stage_items.append(item)

    return stage_items