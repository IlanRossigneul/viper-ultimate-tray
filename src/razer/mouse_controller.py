from razer.device import (
    RazerMouse,
    create_device_manager,
    find_viper_ultimate_device,
)
from razer.mouse_state import DPIStage, MousePollingSession


class MouseController:
    def __init__(self, session: MousePollingSession | None = None) -> None:
        self._device_manager = create_device_manager()
        self._session = session
        self._connection_generation = (
            session.connection_generation if session is not None else None
        )

    def _find_mouse(self) -> RazerMouse | None:
        state = self._session.get_cached_state() if self._session is not None else None
        if state is not None and not state.connected:
            return None

        if self._session is not None:
            generation = self._session.connection_generation
            if generation != self._connection_generation:
                try:
                    self._device_manager = create_device_manager()
                except Exception:  # noqa: BLE001
                    return None
                self._connection_generation = generation

        try:
            mouse = find_viper_ultimate_device(self._device_manager)
        except Exception:  # noqa: BLE001
            mouse = None

        if mouse is not None and state is not None and mouse.name != state.device_name:
            mouse = None

        if mouse is None:
            try:
                self._device_manager = create_device_manager()
                mouse = find_viper_ultimate_device(self._device_manager)
            except Exception:  # noqa: BLE001
                return None

        if mouse is not None and state is not None and mouse.name != state.device_name:
            return None

        return mouse

    def set_dpi(self, x: int, y: int) -> bool:
        mouse = self._find_mouse()

        if mouse is None:
            return False

        try:
            mouse.dpi = (x, y)
            if self._session is not None:
                self._session.update_dpi((x, y))
            return True

        except Exception:  # noqa: BLE001
            return False

    def set_dpi_stage(self, stage_number: int) -> bool:
        mouse = self._find_mouse()

        if mouse is None:
            return False

        try:
            _, stages = mouse.dpi_stages
            if not 1 <= stage_number <= len(stages):
                return False

            mouse.dpi_stages = (stage_number, stages)
            stage_dpi = stages[stage_number - 1]
            mouse.dpi = stage_dpi

            if self._session is not None:
                self._session.update_active_stage(stage_number)
                self._session.update_dpi(stage_dpi)
            return True

        except Exception:  # noqa: BLE001
            return False

    def set_dpi_stages(
        self,
        stages: list[DPIStage],
        active_stage: int,
    ) -> bool:
        mouse = self._find_mouse()

        if mouse is None:
            return False

        try:
            mouse.dpi_stages = (
                active_stage,
                [(stage.dpi, stage.dpi) for stage in stages],
            )
            if self._session is not None:
                self._session.update_dpi_stages(stages, active_stage)
            return True

        except Exception:  # noqa: BLE001
            return False

    def set_idle_time(self, minutes: int) -> bool:
        mouse = self._find_mouse()

        if mouse is None:
            return False

        try:
            mouse.set_idle_time(minutes * 60)
            if self._session is not None:
                self._session.update_idle_minutes(minutes)
            return True

        except Exception:  # noqa: BLE001
            return False

    def set_low_battery_threshold(self, threshold: int) -> bool:
        mouse = self._find_mouse()

        if mouse is None:
            return False

        try:
            mouse.set_low_battery_threshold(threshold)
            if self._session is not None:
                self._session.update_low_battery_threshold(threshold)
            return True

        except Exception:  # noqa: BLE001
            return False
