from pathlib import Path

import gi

gi.require_version("AppIndicator3", "0.1")

from gi.repository import AppIndicator3


def create_indicator(
    icon_dir: Path,
) -> AppIndicator3.Indicator:
    indicator = AppIndicator3.Indicator.new(
        "viper-ultimate-tray",
        str(icon_dir / "mouse.svg"),
        AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
    )

    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    return indicator