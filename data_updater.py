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
        time.sleep(1)

        state = GUIState()
        while True:
            if self.stopped_flag: return

            content_esc_local = network.Network.COMM_GET_VALUES(-1)
            if content_esc_local is not None:
                state.esc_a_state.parse_from_json(content_esc_local, "A")

            if Config.esc_b_id >= 0:
                content_esc_remote = network.Network.COMM_GET_VALUES(Config.esc_b_id)
                if content_esc_remote is not None:
                    state.esc_b_state.parse_from_json(content_esc_remote, "B")

            if Config.switch_a_b_esc > 0:
                tmp = state.esc_a_state
                state.esc_a_state = state.esc_b_state
                state.esc_b_state = tmp
                state.esc_a_state.controller_a_b = "A"
                state.esc_b_state.controller_a_b = "B"

            state.full_power = state.esc_a_state.power + state.esc_b_state.power

            if len(state.chart_current) > Config.chart_points:
                state.chart_current.pop(0)
            state.chart_current.append(state.full_power)



            self.callback(state)

            #state.speed += 0.1

            #if state.speed > 100:
            #    state.speed = 0

            time.sleep(1000.0 / float(Config.refresh_rate) / 1000.0)