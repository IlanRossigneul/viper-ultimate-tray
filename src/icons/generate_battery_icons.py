from __future__ import annotations

import argparse
import math
import xml.etree.ElementTree as ET
from pathlib import Path

BATTERY_LEVELS = range(101)

NORMAL_COLORS = {
    "red": "#FF0000",
    "orange": "#FF6600",
    "yellow": "#FFFF00",
    "green": "#00FF00",
}

CHARGING_COLOR = "#00FFFF"

SVG_NAMESPACE = "http://www.w3.org/2000/svg"


def get_progress_color(battery_level: int, is_charging: bool) -> str:
    """Return the progress color for a battery level."""
    if is_charging:
        return CHARGING_COLOR

    if battery_level <= 5:
        return NORMAL_COLORS["red"]

    if battery_level <= 15:
        return NORMAL_COLORS["orange"]

    if battery_level <= 30:
        return NORMAL_COLORS["yellow"]

    return NORMAL_COLORS["green"]


def get_arc_path(battery_level: int) -> str:
    """Return the SVG path for a clockwise battery progress arc."""
    if battery_level <= 0:
        return ""

    if battery_level >= 100:
        return "M 128 10 A 118 118 0 1 1 128 246 A 118 118 0 1 1 128 10"

    start_angle = -90
    end_angle = start_angle + (battery_level * 3.6)

    radius = 118
    center = 128

    start_x = center + radius * math.cos(math.radians(start_angle))
    start_y = center + radius * math.sin(math.radians(start_angle))

    end_x = center + radius * math.cos(math.radians(end_angle))
    end_y = center + radius * math.sin(math.radians(end_angle))

    large_arc = 1 if battery_level > 50 else 0

    return (
        f"M {start_x:.6f} {start_y:.6f} "
        f"A {radius} {radius} 0 {large_arc} 1 "
        f"{end_x:.6f} {end_y:.6f}"
    )


def generate_icon(
    master_path: Path,
    output_path: Path,
    battery_level: int,
    is_charging: bool,
) -> None:
    """Generate one battery icon from the master SVG."""
    tree = ET.parse(master_path)
    root = tree.getroot()

    progress = root.find(f".//{{{SVG_NAMESPACE}}}path[@id='battery-progress']")
    percentage = root.find(f".//{{{SVG_NAMESPACE}}}text[@id='battery-percentage']")

    if progress is None:
        raise ValueError("Master SVG is missing 'battery-progress'.")

    if percentage is None:
        raise ValueError("Master SVG is missing 'battery-percentage'.")

    progress.set("d", get_arc_path(battery_level))
    progress.set("stroke", get_progress_color(battery_level, is_charging))
    percentage.text = str(battery_level)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(tree, space="    ")
    tree.write(
        output_path,
        encoding="utf-8",
        xml_declaration=True,
    )

    with output_path.open("a", encoding="utf-8") as file:
        file.write("\n")


def generate_icons(
    master_path: Path,
    output_directory: Path,
) -> None:
    """Generate all normal and charging battery icons."""
    for battery_level in BATTERY_LEVELS:
        generate_icon(
            master_path,
            output_directory / f"battery-{battery_level}.svg",
            battery_level,
            False,
        )

        generate_icon(
            master_path,
            output_directory / f"battery-charging-{battery_level}.svg",
            battery_level,
            True,
        )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate battery tray SVG icons from the master SVG."
    )
    parser.add_argument(
        "--master",
        type=Path,
        default=Path(__file__).with_name("tray") / "battery.svg",
        help="Path to the master battery SVG.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("tray"),
        help="Directory where generated icons are written.",
    )

    return parser.parse_args()


def main() -> None:
    """Run the battery icon generator."""
    args = parse_arguments()

    generate_icons(
        master_path=args.master,
        output_directory=args.output,
    )


if __name__ == "__main__":
    main()
