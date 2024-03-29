from threading import Thread

import ujson as json
from platform import uname
from socket import AF_INET, SOCK_DGRAM, socket

def __internal_discovery_thread(ss: socket, sc: socket, port: int):
    payload = {
        "t": "sc",
        "act": "found",
        "from": "VescDesplayDiscovery",
        "sys": uname().system,
        "name": uname().node,
        "arch": uname().machine
    }
    payload = json.dumps(payload).encode()

    while True:
        try:
            data, src = ss.recvfrom(1024)
        except:
            break

        try:
            data = json.loads(data.decode())

            if data['t'] != 'cs' and data['act'] != "search_vb":
                continue
        except:
            continue

        print(src, data)
        sc.sendto(payload, (src[0], port))


def start_discovery_server(port: int = 2002):
    ss = socket(AF_INET, SOCK_DGRAM)
    ss.bind(('', port))
    sc = socket(AF_INET, SOCK_DGRAM)

    Thread(target=__internal_discovery_thread, name='discovery_server_thread', args=(ss, sc, port,)).start()



