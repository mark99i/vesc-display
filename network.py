import json

import requests


# curl -H "Content-Type: application/json" -X POST 'http://127.0.0.1:2002/uart/connect' --data '{"path": "/dev/ttyUSB0", "speed": 115200, "debug_enabled": 1}'
# curl 'http://127.0.0.1:2002/vesc/local/id'
# curl 'http://127.0.0.1:2002/vesc/local/can/scan'
# curl 'http://127.0.0.1:2002/vesc/local/command/COMM_FW_VERSION'
# curl 'http://127.0.0.1:2002/vesc/local/command/COMM_GET_VALUES'
from config import Config

ENABLE_UART_DEBUG = False


# noinspection PyTypeChecker
class Network:

    @staticmethod
    def connect() -> bool:
        js = {"path": Config.serial_port, "speed": Config.serial_speed, "debug_enabled": ENABLE_UART_DEBUG}
        content = requests.post(Config.serial_vesc_api + "/uart/connect", headers={"Content-Type: application/json"}, json=js).content
        answ = json.loads(content)
        return answ["success"]
        pass

    @staticmethod
    def scan_can() -> list:
        try:
            content = requests.get(Config.serial_vesc_api + "/vesc/local/can/scan", timeout=30).content
        except:
            return []
        answ = json.loads(content)

        if answ["success"]:
            return answ["vesc_ids_on_bus"]
        else:
            return []

    @staticmethod
    def COMM_FW_VERSION(controller_id: int = -1) -> dict:
        if controller_id < 0:
            controller_id = "local"
        content = requests.get(Config.serial_vesc_api + f"/vesc/{controller_id}/command/COMM_FW_VERSION").content
        answ = json.loads(content)

        if answ["success"]:
            return answ["data"]
        else:
            return None

    @staticmethod
    def COMM_GET_VALUES(controller_id: int = -1) -> dict:
        if controller_id < 0:
            controller_id = "local"
        content = requests.get(Config.serial_vesc_api + f"/vesc/{controller_id}/command/COMM_GET_VALUES").content
        answ = json.loads(content)

        if answ["success"]:
            return answ["data"]
        else:
            return None