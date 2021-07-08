import json
import os
import threading
import time

import utils


class Config:
    delay_update_ms: int = 30
    chart_current_points: int = 200
    chart_speed_points: int = 200

    hw_controller_current_limit: int = 135

    switch_a_b_esc: int = 0
    esc_b_id: int = -1

    motor_magnets: int = 30
    wheel_diameter: int = 250
    battery_cells: int = 14
    battery_mah: int = 18200

    serial_vesc_api: str = "http://127.0.0.1:2002"  # invisible in settings
    serial_port: str = "/dev/ttyUSB0"
    serial_speed: int = 115200

    service_enable_debug: int = 0
    service_rcv_timeout_ms: int = 100

    gpio_enabled: int = 0                           # invisible in settings
    gpio_break_signal_pin: int = 0                  # invisible in settings
    gpio_1wire_bus_pin: int = 0                     # invisible in settings

    odometer_distance_km_backup: float = 0          # invisible in settings

    @staticmethod
    def load():
        if not os.path.isfile(utils.get_script_dir() + "/config.json") or os.path.getsize(utils.get_script_dir() + "/config.json") < 10:
            Config.save()
        else:
            content = open(utils.get_script_dir() + "/config.json", "r").read()
            conf_dict: dict = json.loads(content)
            for i in conf_dict.keys():
                setattr(Config, i, conf_dict[i])

    @staticmethod
    def save():
        with open(utils.get_script_dir() + "/config.json", "w") as fp:
            content = json.dumps(Config.get_as_dict(), indent=4)
            fp.write(content)
            os.fsync(fp)

    @staticmethod
    def get_as_dict() -> dict:
        conf_dict = {}
        for i in Config.__dict__.keys():
            i = str(i)
            if i.startswith("__") or i == "load" or i == "save" or i == "get_as_dict":
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
        if not os.path.isfile(utils.get_script_dir() + "/odometer.json") or os.path.getsize(utils.get_script_dir() + "/odometer.json") < 10:
            Odometer.save()
        else:
            content = open(utils.get_script_dir() + "/odometer.json", "r").read()
            conf_dict: dict = json.loads(content)
            for i in conf_dict.keys():
                setattr(Odometer, i, conf_dict[i])
        Odometer.__check_and_start_autosaving()

    @staticmethod
    def save():
        with open(utils.get_script_dir() + "/odometer.json", "w") as fp:
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
