from razer.device import (
    create_device_manager,
    find_viper_ultimate_device,
)


class MouseController:

    def __init__(self):
        self._device_manager = create_device_manager()

    def set_dpi_stage(
        self,
        stage_number: int,
    ) -> bool:
        mouse = find_viper_ultimate_device(
            self._device_manager
        )

        if mouse is None:
            return False

        try:
            _, stages = mouse.dpi_stages

            mouse.dpi_stages = (
                stage_number,
                stages,
            )

            return True

        except Exception:
            return False