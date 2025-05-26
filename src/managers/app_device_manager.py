from managers.device.device_manager import DeviceManager


class AppDeviceManager(DeviceManager):
    def __init__(self):
        super().__init__()


DM = AppDeviceManager()
