from managers.device.device_manager import DeviceManager


class ServiceDeviceManager(DeviceManager):
    def __init__(self):
        super().__init__()


DM = ServiceDeviceManager()
