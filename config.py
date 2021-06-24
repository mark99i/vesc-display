import json
import os

import utils


class Config:
    refresh_rate: int = 25
    hw_controller_current_limit: int = 135

    esc_b_id: int = -1

    battery_capacity_wh: int = 18200

    serial_vesc_api: str = "http://127.0.0.1:2002"
    serial_port: str = "/dev/ttyUSB0"
    serial_speed: int = 115200

    @staticmethod
    def load():
        if not os.path.isfile(utils.get_script_dir() + "/config.json"):
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

    @staticmethod
    def get_as_dict() -> dict:
        conf_dict = {}
        for i in Config.__dict__.keys():
            i = str(i)
            if i.startswith("__") or i == "load" or i == "save" or i == "get_as_dict":
                continue
            conf_dict[i] = Config.__dict__[i]
        return conf_dict
