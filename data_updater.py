import json
import threading
import time
from threading import Thread

import network
from utils import distance_km_from_tachometer, stab
from battery import Battery
from config import Config, Odometer
from gui_state import GUIState, ESCState
from session_log import SessionLog


class WorkerThread(Thread):
    AVERAGE_MAX_SPEED_UPDATE_INTERVAL_SEC = 30

    callback = None
    stopped_flag = False
    play_log_path = None
    play_log_js_arr = None
    play_log_state_arr = None
    play_log_time_offset = None

    class WH_KM_Ns:
        last_update_ts_s: int = -1
        calculated_value: float = 0.0
        watts: float = 0.0
        distance: float = -1

        def get_value(self, watts_used: float, now_distance: float) -> float:
            if Config.wh_km_nsec_calc_interval == -1: return 0.0

            now_time_s = int(time.time())

            if self.distance == -1:
                self.distance = now_distance
                self.watts = watts_used
                self.last_update_ts_s = now_time_s
                return self.calculated_value

            if now_time_s - self.last_update_ts_s > Config.wh_km_nsec_calc_interval:
                watt_used_in_n_sec = watts_used - self.watts
                distance_in_n_sec = now_distance - self.distance
                if distance_in_n_sec > 0:
                    self.calculated_value = watt_used_in_n_sec / distance_in_n_sec
                else:
                    self.calculated_value = 0.0
                self.distance = now_distance
                self.watts = watts_used
                self.last_update_ts_s = now_time_s

            return self.calculated_value

    class SessionHolder:
        speed_arr = []

        av: float = 0.0
        mx: float = 0.0
        ft_max: float = 0.0

        def __init__(self):
            threading.Thread(target=self.update_thread_func, name="speed_updater_thread").start()
            pass

        def update_thread_func(self):
            while True:
                if len(self.speed_arr) > 0:
                    self.av = round(sum(self.speed_arr) / len(self.speed_arr), 2)
                    self.mx = round(max(self.speed_arr), 2)
                else:
                    self.av = 0.00
                    self.mx = 0.00
                try: time.sleep(WorkerThread.AVERAGE_MAX_SPEED_UPDATE_INTERVAL_SEC)
                except: return

        def get_info(self):
            return self.av, self.mx, self.ft_max

        def append_ft_max(self, fet_temp: float):
            self.ft_max = max(self.ft_max, fet_temp)

    wh_km_Ns_calc = WH_KM_Ns()
    session_holder = SessionHolder()
    state = GUIState()
    log = SessionLog()

    def __init__(self, callback):
        Thread.__init__(self)
        self.callback = callback

    def setup(self):
        Odometer.load()
        if Config.odometer_distance_km_backup != Odometer.full_odometer:
            # restore backup from config
            Odometer.full_odometer = Config.odometer_distance_km_backup
            Odometer.save()
        else:
            Config.odometer_distance_km_backup = Odometer.full_odometer
            Config.save()

        status = network.Network.get_uart_status()
        if status is None: self.state.uart_status = GUIState.UART_STATUS_ERROR; return

        if status["status"] != "connected":
            res = network.Network.connect()
        else:
            res = True

        if res:
            self.state.uart_status = GUIState.UART_STATUS_WORKING_ERROR
        else:
            self.state.uart_status = GUIState.UART_STATUS_ERROR

    def run(self):
        state = self.state
        state.chart_power = []
        for i in range(0, Config.chart_power_points):
            state.chart_power.append(0)
        for i in range(0, Config.chart_speed_points):
            state.chart_speed.append(0)

        time.sleep(0.5)

        if self.play_log_path is not None:
            self.play_log_setup()
            while not self.stopped_flag: self.play_log_run()
            return

        self.setup()

        while not self.stopped_flag:

            if self.state.uart_status == GUIState.UART_STATUS_WORKING_ERROR or \
                    self.state.uart_status == GUIState.UART_STATUS_WORKING_SUCCESS:

                # if set esc_b_id get info from -1 (local) and remote esc
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
                # if not set esc_b_id get info from -1 (local) only
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

                # if have info from esc_b
                if state.esc_b_state.controller_a_b != "?":
                    voltage = (state.esc_a_state.voltage + state.esc_b_state.voltage) / 2
                    watt_hours_used = state.esc_a_state.watt_hours_used + state.esc_b_state.watt_hours_used
                    fet_temp_max = max(state.esc_a_state.temperature, state.esc_b_state.temperature)
                    state.full_power = state.esc_a_state.power + state.esc_b_state.power
                else:
                    voltage = state.esc_a_state.voltage
                    watt_hours_used = state.esc_a_state.watt_hours_used
                    fet_temp_max = state.esc_a_state.temperature
                    state.full_power = state.esc_a_state.power

                # calculate rpm only if Config.motor_magnets > 0
                if Config.motor_magnets < 1:
                    rpm = 0
                else:
                    rpm = state.esc_a_state.erpm / (Config.motor_magnets / 2)
                state.speed = (Config.wheel_diameter / 10) * rpm * 0.001885

                if state.speed > 99: state.speed = 0.0   # TODO: need remove after tests

                if state.speed > 0.5:
                    self.session_holder.speed_arr.append(state.speed)
                self.session_holder.append_ft_max(fet_temp_max)

                state.average_speed, state.maximum_speed, state.fet_temp = self.session_holder.get_info()

                # chart points remove last if more Config.chart_*_points and append new value
                if Config.chart_power_points > 0:
                    while len(state.chart_power) > Config.chart_power_points:
                        state.chart_power.pop(0)
                    state.chart_power.append(state.full_power)

                if Config.chart_speed_points > 0:
                    while len(state.chart_speed) > Config.chart_speed_points:
                        state.chart_speed.pop(0)
                    state.chart_speed.append(state.speed)

                # calculate distance from tachometer
                # adding session to odometer and clear session distance if now_distance > Odometer.session
                now_distance = distance_km_from_tachometer(state.esc_a_state.tachometer)
                if now_distance < Odometer.session_mileage:
                    Odometer.full_odometer += Odometer.session_mileage
                    Odometer.session_mileage = 0
                    Config.odometer_distance_km_backup = Odometer.full_odometer
                    Config.save()
                    Odometer.save()
                Odometer.session_mileage = now_distance
                state.session_distance = now_distance

                # init battery calculation
                if Battery.display_start_voltage == 0:
                    Battery.init(voltage, now_distance)

                state.battery_percent = Battery.calculate_battery_percent(voltage, watt_hours_used)

                # calc indicators
                if now_distance > 0:
                    state.wh_km = watt_hours_used / now_distance
                if state.wh_km > 0 and not Battery.full_tracking_disabled:
                    state.estimated_battery_distance = (Battery.full_battery_wh - watt_hours_used) / state.wh_km
                else:
                    state.estimated_battery_distance = 0
                state.wh_km_Ns = self.wh_km_Ns_calc.get_value(watt_hours_used, now_distance)

                if state.speed > 0:
                    state.wh_km_h = stab(round(state.full_power / state.speed, 1), -99.9, 99.9)

                state.builded_ts_ms = int(time.time() * 1000)
                if Config.write_logs:
                    self.log.write_state(json.dumps(state.get_json_for_log()))
            else:
                time.sleep(0.1)

            self.callback(state)

            time.sleep(float(Config.delay_update_ms) / 1000.0)


    def play_log_setup(self):

        print("read file ...")
        content = open(self.play_log_path, "r").read()

        self.play_log_js_arr = []
        for arr_item in content.split("\n"):
            if len(arr_item) < 5: break
            self.play_log_js_arr.append(json.loads(arr_item))

        print("loaded", len(self.play_log_js_arr), "points")

        print("parsing states ...")
        self.play_log_state_arr = []
        for item in self.play_log_js_arr:
            state = GUIState()
            state.parse_from_log(item)
            self.play_log_state_arr.append(state)
        print("parced")

        #self.play_log_state_arr.reverse()
        #self.play_log_time_offset = int(time.time() * 1000) - self.play_log_state_arr[0].builded_ts_ms

    index_log = 0
    def play_log_run(self):

        self.state = self.play_log_state_arr[0 + self.index_log]
        next_state = self.play_log_state_arr[1 + self.index_log]
        wait_time_ms = next_state.builded_ts_ms - self.state.builded_ts_ms

        print(self.state.builded_ts_ms, next_state.builded_ts_ms, wait_time_ms)

        self.callback(self.state)

        wait_time_ms = stab(wait_time_ms, 0, 300)

        self.index_log += 1
        time.sleep(wait_time_ms / 1000)