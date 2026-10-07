from razer.device import create_device_manager, find_viper_ultimate_device
from razer.mouse_state import DPIStage


class MouseController:
    def __init__(self) -> None:
        self._device_manager = create_device_manager()

    def set_dpi(self, x: int, y: int) -> bool:
        mouse = find_viper_ultimate_device(self._device_manager)

        if mouse is None:
            return False

        try:
            mouse.dpi = (x, y)
            return True

        except Exception:  # noqa: BLE001
            return False

    def set_dpi_stage(self, stage_number: int) -> bool:
        mouse = find_viper_ultimate_device(self._device_manager)

        if mouse is None:
            return False

        try:
            _, stages = mouse.dpi_stages
            mouse.dpi_stages = (stage_number, stages)
            return True

        except Exception:  # noqa: BLE001
            return False

    def set_dpi_stages(
        self,
        stages: list[DPIStage],
        active_stage: int,
    ) -> bool:
        mouse = find_viper_ultimate_device(self._device_manager)

        if mouse is None:
            return False

        try:
            mouse.dpi_stages = (
                active_stage,
                [(stage.dpi, stage.dpi) for stage in stages],
            )
            return True

        except Exception:  # noqa: BLE001
            return False

    def set_idle_time(self, minutes: int) -> bool:
        mouse = find_viper_ultimate_device(self._device_manager)

        if mouse is None:
            return False

        try:
            mouse.set_idle_time(minutes * 60)
            return True

        except Exception:  # noqa: BLE001
            return False

    def set_low_battery_threshold(self, threshold: int) -> bool:
        mouse = find_viper_ultimate_device(self._device_manager)

        if mouse is None:
            return False

        try:
            mouse.set_low_battery_threshold(threshold)
            return True

        except Exception:  # noqa: BLE001
            return False
