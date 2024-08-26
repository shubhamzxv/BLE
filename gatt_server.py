import dbus
import dbus.mainloop.glib
from gi.repository import GLib

from ble import (
    Application,
    Service,
    Characteristic,
    Descriptor,
    Advertisement,
    find_adapter,
    BLUEZ_SERVICE_NAME,
    LE_ADVERTISING_MANAGER_IFACE,
)

from constants import GATT_MANAGER_IFACE


class MyService(Service):
    def __init__(self, bus, index):
        Service.__init__(
            self,
            bus,
            index,
            "12345678-1234-5678-1234-56789abcdef0",
            True,
            "My Custom Service",
        )
        self.add_characteristic(MyCharacteristic(bus, 0, self))


class MyCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self,
            bus,
            index,
            "12345678-1234-5678-1234-56789abcdef1",
            ["read", "write", "notify"],
            service,
            "My Custom Characteristic",
        )
        self.value = []

    def ReadValue(self, options):
        print("Custom Characteristic Read: " + repr(self.value))
        return self.value

    def WriteValue(self, value, options):
        print("Custom Characteristic Write: " + repr(value))
        self.value = value


def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    adapter = find_adapter(bus)
    if not adapter:
        print("LEAdvertisingManager1 interface not found")
        return

    service_manager = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE_NAME, adapter), GATT_MANAGER_IFACE
    )
    ad_manager = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE_NAME, adapter), LE_ADVERTISING_MANAGER_IFACE
    )

    app = Application(bus)
    advertisement = Advertisement(bus, 0, "peripheral")

    advertisement.add_service_uuid("12345678-1234-5678-1234-56789abcdef0")
    advertisement.add_local_name("VRF PI")
    advertisement.add_include_tx_power(True)

    service = MyService(bus, 0)
    app.add_service(service)

    mainloop = GLib.MainLoop()

    service_manager.RegisterApplication(
        app.get_path(),
        {},
        reply_handler=register_app_cb,
        error_handler=register_app_error_cb,
    )
    ad_manager.RegisterAdvertisement(
        advertisement.get_path(),
        {},
        reply_handler=register_ad_cb,
        error_handler=register_ad_error_cb,
    )

    try:
        mainloop.run()
    except KeyboardInterrupt:
        ad_manager.UnregisterAdvertisement(advertisement)
        service_manager.UnregisterApplication(app)
        print("Unregistered Advertisement and Application")


def register_ad_cb():
    print("Advertisement registered")


def register_ad_error_cb(error):
    print("Failed to register advertisement: " + str(error))
    GLib.MainLoop().quit()


def register_app_cb():
    print("GATT application registered")


def register_app_error_cb(error):
    print("Failed to register application: " + str(error))
    GLib.MainLoop().quit()


if __name__ == "__main__":
    main()
