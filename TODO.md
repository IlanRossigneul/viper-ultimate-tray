# TODO

## Mouse polling performance

* Rework `MousePoller` to avoid repeatedly reading unchanged OpenRazer mouse state values.
* Cache mouse state values and refresh each value only when its underlying configuration or state may have changed.
* Preserve the complete `MouseState` exposed to the application.
* Keep connection, battery, charging, DPI, hibernation, and low-power state updates responsive.
* Measure the impact of the new polling strategy before and after the rework.

## DPI

* Add support for configuring arbitrary DPI values outside the existing DPI Stages.
* Add support for configuring the mouse DPI Stages directly.

## OpenRazer

* Add an interface for configuring OpenRazer settings.
* Add the ability to reload or restart `openrazer-daemon` from the application.

## RGB and low-battery state

* Synchronize the mouse RGB with the dock RGB when the mouse enters the low-battery state.
* At 5% battery, make the mouse blink red and apply the same RGB state to the dock.
* When the mouse is removed from the dock, restore the dock RGB state together with the mouse RGB state.
* Preserve the RGB configuration that was active before entering the low-battery state and restore it afterwards.

## Low-battery thresholds

* Make the three low-battery notification thresholds configurable.
* Use the configured thresholds when generating the tray battery icons.
* Ensure the notification thresholds and tray icon ranges remain synchronized.

## Icons and themes

* Detect the user's current theme and adapt the battery icons accordingly.
* Provide light and dark theme variants for the battery icons.
* Keep a single SVG per battery percentage and charging state, with the SVG adapting to the active user theme rather than maintaining separate icon files for each theme.
* Ensure both charging and non-charging battery icons remain readable and visually consistent in light and dark themes.

## Ideas to revisit

* Add future ideas here as they come up.
