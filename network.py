import ujson as json

import requests
import urllib3

# curl -H "Content-Type: application/json" -X POST 'http://127.0.0.1:2002/uart/connect' --data '{"path": "/dev/ttyUSB0", "speed": 115200, "debug_enabled": 1}'
# curl 'http://127.0.0.1:2002/vesc/local/id'
# curl 'http://127.0.0.1:2002/vesc/local/can/scan'
# curl 'http://127.0.0.1:2002/vesc/local/command/COMM_FW_VERSION'
# curl 'http://127.0.0.1:2002/vesc/local/command/COMM_GET_VALUES'
# curl -H "Content-Type: application/json" -X POST 'http://192.168.15.30:2002/vescs/command/COMM_GET_VALUES' --data '{"vesc_ids": [-1, 15]}'
from config import Config

ENABLE_UART_DEBUG = False


# noinspection PyTypeChecker
class Network:
    session: requests.Session = requests.Session()
    http = urllib3.PoolManager()

    @staticmethod
    def connect() -> bool:
        js = {"path": Config.serial_port, "speed": Config.serial_speed, "debug_enabled": ENABLE_UART_DEBUG}
        content = Network.session.post(f"{Config.serial_vesc_api}/uart/connect", headers={"Content-Type: application/json"}, json=js).content
        answ = json.loads(content)
        return answ["success"]
        pass

    @staticmethod
    def scan_can() -> list:
        try:
            content = Network.session.get(f"{Config.serial_vesc_api}/vesc/local/can/scan", timeout=30).content
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
        content = Network.session.get(f"{Config.serial_vesc_api}/vesc/{controller_id}/command/COMM_FW_VERSION").content
        answ = json.loads(content)

        if answ["success"]:
            return answ["data"]
        else:
            return None

    @staticmethod
    def COMM_GET_VALUES(controller_id: int = -1) -> dict:
        if controller_id < 0:
            controller_id = "local"
        #req = Network.session.get(f"{Config.serial_vesc_api}/vesc/{controller_id}/command/COMM_GET_VALUES", stream=True, verify=False)
        response = Network.http.request('GET', f"{Config.serial_vesc_api}/vesc/{controller_id}/command/COMM_GET_VALUES")
        if response.status != 200:
            return None

        answ = json.loads(response.data)

        if answ["success"]:
            return answ["data"]
        else:
            return None

    @staticmethod
    def COMM_GET_VALUES_multi(controller_ids: list) -> dict:
        data = json.dumps({"vesc_ids": controller_ids})
        response = Network.http.request("POST", f"{Config.serial_vesc_api}/vescs/command/COMM_GET_VALUES",
                                        headers={'Content-Type': 'application/json'},
                                        body=data)
        if response.status != 200:
            return None

        answ = json.loads(response.data)

        if answ["success"]:
            return answ["data"]
        else:
            return None
