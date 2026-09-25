# TODO

## Battery data

### Battery logger

* Improve the battery logger window presentation if needed.
* Consider adding pause and resume support.

### Samples and charge models

* Add a dedicated window for inspecting battery samples and charge models.
* Provide tools for viewing and manipulating recorded battery data.
* Provide tools for inspecting, rebuilding and managing wired and wireless charge models.
* Consider introducing sample and model management progressively across different releases rather than implementing everything at once.

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

## Mouse polling performance

* Investigate whether OpenRazer mouse state values can be cached and refreshed only when their underlying configuration or state changes, while preserving the complete `MouseState` data exposed to the application.
* Measure the impact of reducing redundant D-Bus reads before changing the polling strategy.

## Ideas to revisit

* Add future ideas here as they come up.
