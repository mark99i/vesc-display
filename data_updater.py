import time
from threading import Thread

import network
from config import Config
from gui_state import GUIState, ESCState


class WorkerThread(Thread):
    callback = None
    stopped_flag = False

    state = GUIState()

    def __init__(self, callback):
        Thread.__init__(self)
        self.callback = callback

    def setup(self):
        res = network.Network.connect()
        if res:
            self.state.uart_status = GUIState.UART_STATUS_WORKING_ERROR
        else:
            self.state.uart_status = GUIState.UART_STATUS_ERROR

    def run(self):
        state = self.state
        state.chart_current = []
        for i in range(0, Config.chart_current_points):
            state.chart_current.append(0)
        for i in range(0, Config.chart_speed_points):
            state.chart_speed.append(0)

        time.sleep(0.5)
        self.setup()

        while True:
            if self.stopped_flag: return

            if self.state.uart_status == GUIState.UART_STATUS_WORKING_ERROR or \
                    self.state.uart_status == GUIState.UART_STATUS_WORKING_SUCCESS:

                if Config.esc_b_id >= 0:
                    result = network.Network.COMM_GET_VALUES_multi([-1, Config.esc_b_id])
                    if result is None:
                        self.state.uart_status = GUIState.UART_STATUS_WORKING_ERROR
                        self.callback(state)
                        continue

                    if Config.switch_a_b_esc > 0:
                        state.esc_a_state.parse_from_json(result[str(Config.esc_b_id)], "A")
                        state.esc_b_state.parse_from_json(result["-1"], "B")
                    else:
                        state.esc_a_state.parse_from_json(result["-1"], "A")
                        state.esc_b_state.parse_from_json(result[str(Config.esc_b_id)], "B")
                else:
                    result = network.Network.COMM_GET_VALUES_multi([-1])
                    if result is None:
                        self.state.uart_status = GUIState.UART_STATUS_WORKING_ERROR
                        self.callback(state)
                        continue
                    state.esc_a_state.parse_from_json(result["-1"], "A")
                    if state.esc_b_state.controller_a_b != "?":
                        state.esc_b_state = ESCState("?")
                self.state.uart_status = GUIState.UART_STATUS_WORKING_SUCCESS

                if state.esc_b_state.controller_a_b != "?":
                    erpm = (state.esc_a_state.erpm + state.esc_b_state.erpm) / 2
                else:
                    erpm = state.esc_a_state.erpm

                rpm = erpm / (Config.motor_magnets / 2)
                speed = (Config.wheel_diameter / 10) * rpm * 0.001885
                state.speed = round(speed, 1)

                state.full_power = state.esc_a_state.power + state.esc_b_state.power

                while len(state.chart_current) > Config.chart_current_points:
                    state.chart_current.pop(0)
                if Config.chart_current_points > 0:
                    state.chart_current.append(state.full_power)

                while len(state.chart_speed) > Config.chart_speed_points:
                    state.chart_speed.pop(0)
                if Config.chart_speed_points > 0:
                    state.chart_speed.append(state.speed)

            else:
                time.sleep(0.1)

            self.callback(state)

            time.sleep(float(Config.delay_update_ms) / 1000.0)