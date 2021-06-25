import time
from threading import Thread

import network
from config import Config
from gui_state import GUIState


class WorkerThread(Thread):
    callback = None
    stopped_flag = False

    def __init__(self, callback):
        Thread.__init__(self)
        self.callback = callback

    def run(self):
        state = GUIState()
        state.chart_current = []
        for i in range(0, Config.chart_points):
            state.chart_current.append(0)
            state.chart_speed.append(0)

        time.sleep(0.5)

        while True:
            if self.stopped_flag: return

            if Config.esc_b_id >= 0:
                result = network.Network.COMM_GET_VALUES_multi([-1, Config.esc_b_id])
                if result is None: continue

                if Config.switch_a_b_esc > 0:
                    state.esc_a_state.parse_from_json(result[str(Config.esc_b_id)], "A")
                    state.esc_b_state.parse_from_json(result["-1"], "B")
                else:
                    state.esc_a_state.parse_from_json(result["-1"], "A")
                    state.esc_b_state.parse_from_json(result[str(Config.esc_b_id)], "B")
            else:
                content_esc_local = network.Network.COMM_GET_VALUES(-1)
                if content_esc_local is None: continue
                state.esc_a_state.parse_from_json(content_esc_local, "A")

            state.full_power = state.esc_a_state.power + state.esc_b_state.power

            while len(state.chart_current) > Config.chart_points:
                state.chart_current.pop(0)
            state.chart_current.append(state.full_power)

            self.callback(state)

            time.sleep(float(Config.delay_update_ms) / 1000.0)