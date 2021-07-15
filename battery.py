from utils import map_ard, stab


class Battery:

    MIN_CELL_VOLTAGE: float = 2.9
    NOM_CELL_VOLTAGE: float = 3.7
    MAX_CELL_VOLTAGE: float = 4.2

    full_battery_wh: int = 0
    display_start_voltage: float = 0
    full_tracking_disabled: bool = False

    last_percent: int = -100

    @staticmethod
    def init(now_voltage, now_distance):
        from config import Config
        if Config.battery_cells < 1 or Config.battery_mah < 500:
            return
        Battery.full_battery_wh = int((Config.battery_cells * Battery.NOM_CELL_VOLTAGE * Config.battery_mah) / 1000)
        Battery.display_start_voltage = now_voltage

        if Battery.is_full_charged(now_voltage, now_distance):
            Battery.full_tracking_disabled = False
        else:
            Battery.full_tracking_disabled = True

    @staticmethod
    def recalc_full_battery_wh() -> None:
        from config import Config
        Battery.full_battery_wh = int((Config.battery_cells * Battery.NOM_CELL_VOLTAGE * Config.battery_mah) / 1000)

    @staticmethod
    def is_full_charged(now_voltage: int, now_distance) -> bool:
        from config import Config
        max_battery_voltage = Config.battery_cells * Battery.MAX_CELL_VOLTAGE
        min_voltage_for_full_charge = max_battery_voltage - (max_battery_voltage / 100 / 2) # max_voltage - 0.5%
        full_battery = now_voltage >= min_voltage_for_full_charge

        return full_battery and now_distance < 1.1

    @staticmethod
    def calculate_battery_percent(voltage: float, watt_hours: int) -> int:
        if Battery.full_battery_wh == 0:
            return 0

        if Battery.full_tracking_disabled:
            from config import Config
            percent_by_voltage = map_ard(voltage,
                                         Battery.MIN_CELL_VOLTAGE * Config.battery_cells,
                                         Battery.MAX_CELL_VOLTAGE * Config.battery_cells,
                                         0, 100)

            return percent_by_voltage

        estimated_wh = Battery.full_battery_wh - watt_hours
        battery_percent = int(100 / (Battery.full_battery_wh / estimated_wh))

        if Battery.last_percent == -100:
            Battery.last_percent = battery_percent
        else:
            if abs(Battery.last_percent - battery_percent) > 3:
                if Battery.last_percent < battery_percent:
                    battery_percent = Battery.last_percent + 1
                else:
                    battery_percent = Battery.last_percent - 1
            Battery.last_percent = battery_percent

        battery_percent = stab(battery_percent, 0, 100)
        return battery_percent