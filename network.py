import ujson as json

import requests
import urllib3

# curl -H "Content-Type: application/json" -X POST 'http://127.0.0.1:2002/uart/connect' --data '{"path": "/dev/ttyUSB0", "speed": 115200, "debug_enabled": 0}'
# curl 'http://127.0.0.1:2002/uart/status'
# curl 'http://127.0.0.1:2002/vesc/local/id'
# curl 'http://127.0.0.1:2002/vesc/local/can/scan'
# curl 'http://127.0.0.1:2002/vescs/command/COMM_FW_VERSION?vesc_id=-1'
# curl 'http://127.0.0.1:2002/vescs/command/COMM_GET_VALUES'
# curl 'http://127.0.0.1:2002/vescs/command/COMM_GET_MCCONF'
# curl -H "Content-Type: application/json" -X POST 'http://127.0.0.1:2002/vescs/command/COMM_GET_VALUES' --data '{"vesc_ids": [-1, 15]}'
from config import Config


# noinspection PyTypeChecker
class Network:
    session: requests.Session = requests.Session()
    http = urllib3.PoolManager()

    net_timeout = 1     # in seconds

    @staticmethod
    def get_uart_status() -> dict:
        try:
            content = Network.session.get(f"{Config.serial_vesc_api}/uart/status", timeout=Network.net_timeout).content
            answ = json.loads(content)
            if answ["success"]:
                return answ
            else:
                return None
        except:
            return None

    @staticmethod
    def connect() -> bool:
        try:

            js = {"path": Config.serial_port, "speed": Config.serial_speed, "debug_enabled": bool(Config.service_enable_debug)}
            content = Network.session.post(f"{Config.serial_vesc_api}/uart/connect",
                                            headers={'Content-Type': 'application/json'}, json=js,
                                            timeout=Network.net_timeout).content
            answ = json.loads(content)
            return answ["success"]
        except:
            return False

    @staticmethod
    def COMM_PING_CAN() -> list:
        try:
            data = json.dumps({"vesc_ids": [-1]})
            response = Network.http.request("POST", f"{Config.serial_vesc_api}/vescs/command/COMM_PING_CAN",
                                            headers={'Content-Type': 'application/json'},
                                            body=data, timeout=Network.net_timeout + 6)
            if response.status != 200:
                return None

            answ = json.loads(response.data)

            if answ["success"]:
                return answ["data"]
            else:
                return None
        except:
            return None

    @staticmethod
    def COMM_GET_VALUES_multi(controller_ids: list) -> dict:
        try:
            data = json.dumps({"vesc_ids": controller_ids})
            response = Network.http.request("POST", f"{Config.serial_vesc_api}/vescs/command/COMM_GET_VALUES",
                                            headers={'Content-Type': 'application/json'},
                                            body=data, timeout=Network.net_timeout)
            if response.status != 200:
                return None

            answ = json.loads(response.data)

            if answ["success"]:
                return answ["data"]
            else:
                return None
        except:
            return None

    @staticmethod
    def COMM_REBOOT(controller_ids: list) -> bool:
        try:
            data = json.dumps({"vesc_ids": controller_ids})
            response = Network.http.request("POST", f"{Config.serial_vesc_api}/vescs/command/COMM_REBOOT",
                                            headers={'Content-Type': 'application/json'},
                                            body=data, timeout=Network.net_timeout + 7)
            if response.status != 200:
                return False

            return True
        except:
            return False


    @staticmethod
    def COMM_FW_VERSION(controller_id: int = -1) -> dict:
        try:
            data = json.dumps({"vesc_ids": [controller_id]})
            content = Network.session.get(f"{Config.serial_vesc_api}/vescs/command/COMM_FW_VERSION",
                                          timeout=Network.net_timeout,
                                          headers={'Content-Type': 'application/json'}, body=data).content
            answ = json.loads(content)

            if answ["success"]:
                return answ["data"][controller_id]
            else:
                return None
        except:
            return None

    @staticmethod
    def COMM_GET_MCCONF(controller_id: int = -1) -> dict:
        try:
            if controller_id is None: controller_id = -1
            content = Network.session.get(f"{Config.serial_vesc_api}/vescs/command/COMM_GET_MCCONF?vesc_id={controller_id}",
                                          timeout=Network.net_timeout + 500).content
            answ = json.loads(content)

            if answ["success"]:
                return answ["data"][str(controller_id)]
            else:
                return None
        except:
            return None

