import json
import os
import threading
import time

import utils


class Config:
    delay_update_ms: int = 1
    delay_chart_update_ms: int = 1000
    chart_power_points: int = 200
    chart_speed_points: int = 200

    nsec_calc_count: int = 0
    # wh_km_nsec_calc_interval: int = 15

    use_gui_lite: int = 0

    mtemp_insteadof_load: int = 0
    switch_a_b_esc: int = 0
    esc_b_id: int = -1

    write_logs: int = 0

    motor_magnets: int = 0
    wheel_diameter: int = 0
    battery_cells: int = 0
    battery_mah: int = 0
    hw_controller_current_limit: int = 135
    hw_controller_voltage_offset_mv: int = 0

    serial_vesc_api: str = "http://127.0.0.1:2002"  # invisible in settings
    serial_port: str = "/dev/ttyUSB0"
    serial_speed: int = 115200

    service_enable_debug: int = 0
    service_rcv_timeout_ms: int = 100

    gpio_enabled: int = 0                           # invisible in settings
    gpio_break_signal_pin: int = 0                  # invisible in settings
    gpio_1wire_bus_pin: int = 0                     # invisible in settings

    odometer_distance_km_backup: float = 0          # invisible in settings

    right_param_active_ind: str = "SessionDistance" # invisible in settings
    center_param_active_ind: str = "WhKm"           # invisible in settings
    left_param_active_ind: str = "BatteryPercent"   # invisible in settings

    # this option no save as dict
    invisible_in_settings_options = ['serial_vesc_api', 'gpio_enabled',
                                     'gpio_break_signal_pin', 'gpio_1wire_bus_pin',
                                     'odometer_distance_km_backup', 'left_param_active_ind',
                                     'right_param_active_ind', 'center_param_active_ind']

    @staticmethod
    def load():
        if not os.path.isfile(utils.get_script_dir() + "/configs/config.json") or os.path.getsize(utils.get_script_dir() + "/configs/config.json") < 10:
            Config.save()
        else:
            content = open(utils.get_script_dir() + "/configs/config.json", "r").read()
            conf_dict: dict = json.loads(content)
            for i in conf_dict.keys():
                if hasattr(Config, i):
                    setattr(Config, i, conf_dict[i])

    @staticmethod
    def save():
        with open(utils.get_script_dir() + "/configs/config.json", "w") as fp:
            content = json.dumps(Config.get_as_dict(), indent=4)
            fp.write(content)
            os.fsync(fp)

    @staticmethod
    def get_as_dict() -> dict:
        conf_dict = {}
        for i in Config.__dict__.keys():
            i = str(i)
            if i.startswith("__") or i == "load" or i == "save" or i == "get_as_dict" or i == "invisible_in_settings_options":
                continue
            conf_dict[i] = Config.__dict__[i]
        return conf_dict

class Odometer:
    __autosaving_enabled = True
    __autosaving_interval_s = 10

    __autosaving_thread: threading.Thread = None

    session_mileage: float = 0.0
    full_odometer: float = 0.0

    @staticmethod
    def load():
        if not os.path.isfile(utils.get_script_dir() + "/configs/odometer.json") or os.path.getsize(utils.get_script_dir() + "/configs/odometer.json") < 10:
            Odometer.save()
        else:
            content = open(utils.get_script_dir() + "/configs/odometer.json", "r").read()
            conf_dict: dict = json.loads(content)
            for i in conf_dict.keys():
                setattr(Odometer, i, conf_dict[i])
        Odometer.__check_and_start_autosaving()

    @staticmethod
    def save():
        with open(utils.get_script_dir() + "/configs/odometer.json", "w") as fp:
            content = json.dumps(Odometer.get_as_dict(), indent=4)
            fp.write(content)
            os.fsync(fp)
        Odometer.__check_and_start_autosaving()

    @staticmethod
    def __check_and_start_autosaving():
        if (Odometer.__autosaving_thread is None or not Odometer.__autosaving_thread.is_alive()) and Odometer.__autosaving_enabled:
            Odometer.__autosaving_thread = threading.Thread(target=Odometer.__autosaving_func, name="autosaving-odometer")
            Odometer.__autosaving_thread.start()

    @staticmethod
    def __autosaving_func():
        while Odometer.__autosaving_enabled:
            Odometer.save()
            time.sleep(utils.stab(Odometer.__autosaving_interval_s, 2, 1000))

    @staticmethod
    def get_as_dict() -> dict:
        conf_dict = {}
        for i in Odometer.__dict__.keys():
            i = str(i)
            if i.startswith("_") or i == "load" or i == "save" or i == "get_as_dict":
                continue
            conf_dict[i] = Odometer.__dict__[i]
        return conf_dict
