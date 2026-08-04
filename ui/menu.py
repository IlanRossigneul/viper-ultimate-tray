import subprocess
from dataclasses import dataclass
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk


@dataclass(slots=True)
class MenuWidgets:
    menu: Gtk.Menu

    name_item: Gtk.MenuItem
    battery_item: Gtk.MenuItem
    dpi_item: Gtk.MenuItem
    stage_item: Gtk.MenuItem
    idle_item: Gtk.MenuItem
    low_battery_item: Gtk.MenuItem

    stage_menu: Gtk.Menu
    stage_items: list[Gtk.RadioMenuItem]

    polychromatic_action: Gtk.MenuItem
    input_remapper_action: Gtk.MenuItem
    quit_action: Gtk.MenuItem

def create_menu_item(
    icon_path: Path | None = None,
    text: str = "",
) -> Gtk.MenuItem:
    item = Gtk.MenuItem()

    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

    image = None

    if icon_path is not None:
        image = Gtk.Image.new_from_file(str(icon_path))

        box.pack_start(
            image,
            False,
            False,
            0,
        )

    label = Gtk.Label(label=text, xalign=0)

    box.pack_start(
        label,
        True,
        True,
        0,
    )

    item.add(box)

    item.label_widget = label
    item.image_widget = image

    item.show_all()

    return item


def add_separator(
    menu: Gtk.Menu,
) -> None:
    separator = Gtk.SeparatorMenuItem()
    separator.show()

    menu.append(separator)


def create_menu(
    menu_icon_dir: Path,
    menu_battery_icon_dir: Path,
    device_name: str,
) -> MenuWidgets:
    menu = Gtk.Menu()

    name_item = create_menu_item(menu_icon_dir / "mouse.svg", device_name)

    battery_item = create_menu_item(menu_battery_icon_dir / "battery-4.svg")

    dpi_item = create_menu_item(menu_icon_dir / "dpi.svg")

    stage_item = create_menu_item(menu_icon_dir / "stages-dpi.svg")

    idle_item = create_menu_item(menu_icon_dir / "hibernation.svg")

    low_battery_item = create_menu_item(menu_icon_dir / "low-conso.svg")

    stage_menu = Gtk.Menu()

    stage_item.set_submenu(stage_menu)

    stage_items: list[Gtk.RadioMenuItem] = []

    polychromatic_action = create_menu_item(
        menu_icon_dir / "polychromatic.svg",
        "Ouvrir Polychromatic",
    )

    polychromatic_action.connect(
        "activate",
        lambda *_:
            subprocess.Popen(
                ["polychromatic-controller"],
                start_new_session=True,
            ),
    )

    input_remapper_action = create_menu_item(
        menu_icon_dir / "input-remapper.svg",
        "Ouvrir Input Remapper",
    )

    input_remapper_action.connect(
        "activate",
        lambda *_:
            subprocess.Popen(
                ["input-remapper-gtk"],
                start_new_session=True,
            ),
    )

    quit_action = create_menu_item(text="Quitter")

    quit_action.connect(
        "activate",
        lambda *_:
            Gtk.main_quit(),
    )

    menu.append(name_item)

    add_separator(menu)

    menu.append(battery_item)

    add_separator(menu)

    menu.append(dpi_item)
    menu.append(stage_item)

    add_separator(menu)

    menu.append(idle_item)
    menu.append(low_battery_item)

    add_separator(menu)

    menu.append(polychromatic_action)
    menu.append(input_remapper_action)

    add_separator(menu)

    menu.append(quit_action)

    return MenuWidgets(
        menu=menu,
        name_item=name_item,
        battery_item=battery_item,
        dpi_item=dpi_item,
        stage_item=stage_item,
        idle_item=idle_item,
        low_battery_item=low_battery_item,
        stage_menu=stage_menu,
        stage_items=stage_items,
        polychromatic_action=polychromatic_action,
        input_remapper_action=input_remapper_action,
        quit_action=quit_action,
    )