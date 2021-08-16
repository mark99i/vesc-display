import json
import os
import time

import utils
from battery import Battery
from config import Config


class Session:

    distance: float = 0
    average_speed: float = 0
    maximum_speed: float = 0
    minimum_power: float = 0
    maximum_power: float = 0
    minimum_phase_current: float = 0
    maximum_phase_current: float = 0
    average_battery_current: float = 0
    maximum_battery_current: float = 0
    maximum_fet_temp: float = 0
    maximum_motor_temp: float = 0
    start_session_odometer: float = 0
    end_session_odometer: float = 0
    watt_hours: float = 0

    __av_speed_calc_sum: float = 0
    __av_speed_calc_count: int = 0
    __av_battery_current_calc_sum: float = 0
    __av_battery_current_calc_count: int = 0
    __dynamic_watts_used_start: float = -1
    __dynamic_distance_start: float = -1

    speed_session_history: list = list()
    power_session_history: list = list()
    distance_session_history: list = list()

    __speed_temp_arr: list = list()
    __power_temp_arr: list = list()
    __distn_temp_arr: list = list()
    __last_time_point_saved_s: int = 0

    ts_start: int = 0
    ts_end: int = 0
    ts_last_speed_more_4: int = 0

    battery_tracking_enabled: bool = False
    battery_display_start_voltage: float = 0.0

    def update(self, state, dynamic_session: bool = False):
        # from gui_state import GUIState
        # state: GUIState = state

        from gui_state import GUIState
        state: GUIState

        if state.speed > 4:
            self.__av_speed_calc_sum += state.speed
            self.__av_speed_calc_count += 1
            self.average_speed = round(self.__av_speed_calc_sum / self.__av_speed_calc_count, 2)
            self.maximum_speed = round(max(self.maximum_speed, state.speed), 2)

            battery_current = state.esc_a_state.battery_current + state.esc_b_state.battery_current
            self.__av_battery_current_calc_sum += battery_current
            self.__av_battery_current_calc_count += 1
            self.average_battery_current = round(self.__av_battery_current_calc_sum / self.__av_battery_current_calc_count, 2)
            self.maximum_battery_current = round(max(self.maximum_battery_current, battery_current), 2)

            now_time_s = int(state.builded_ts_ms / 1000)
            self.ts_last_speed_more_4 = now_time_s

            if self.ts_start == 0:
                self.ts_start = now_time_s

            if Config.write_session_track and not dynamic_session:
                self.__speed_temp_arr.append(state.speed)
                self.__power_temp_arr.append(state.full_power)
                self.__distn_temp_arr.append(state.session_distance)

                if now_time_s - self.__last_time_point_saved_s > Config.session_track_average_sec:
                    speed_point = sum(self.__speed_temp_arr) / len(self.__speed_temp_arr)
                    power_point = sum(self.__power_temp_arr) / len(self.__power_temp_arr)
                    distn_point = sum(self.__distn_temp_arr) / len(self.__distn_temp_arr)
                    self.speed_session_history.append(speed_point)
                    self.power_session_history.append(power_point)
                    self.distance_session_history.append(distn_point)
                    self.__speed_temp_arr.clear()
                    self.__power_temp_arr.clear()
                    self.__distn_temp_arr.clear()
                    self.__last_time_point_saved_s = now_time_s


        if dynamic_session:
            if self.__dynamic_watts_used_start == -1:
                self.__dynamic_watts_used_start = state.f_get_wu()
            if self.__dynamic_distance_start == -1:
                self.__dynamic_distance_start = state.session_distance

        self.maximum_fet_temp = max(self.maximum_fet_temp,
                                    max(state.esc_a_state.temperature, state.esc_b_state.temperature))
        self.maximum_motor_temp = max(self.maximum_motor_temp,
                                    max(state.esc_a_state.motor_temperature, state.esc_b_state.motor_temperature))
        self.minimum_power = min(self.minimum_power, state.full_power)
        self.maximum_power = max(self.maximum_power, state.full_power)

        phase_current = state.esc_a_state.phase_current + state.esc_b_state.phase_current
        self.minimum_phase_current = min(self.minimum_phase_current, phase_current)
        self.maximum_phase_current = max(self.maximum_phase_current, phase_current)

        self.battery_tracking_enabled = not Battery.full_tracking_disabled

        if dynamic_session:
            self.distance = state.session_distance - self.__dynamic_distance_start
            if self.distance != 0:
                self.watt_hours = (state.f_get_wu() - self.__dynamic_watts_used_start) / self.distance
            else:
                self.watt_hours = 0
        else:
            self.watt_hours = state.wh_km
            self.distance = state.session_distance


    def f_get_private_params(self):
        return self.ts_last_speed_more_4

    def f_get_json(self) -> dict:
        result = {}

        asdict = dict((name, getattr(self, name)) for name in dir(self))
        for i in asdict.keys():
            i = str(i)
            if "__" in i or i.startswith("f_") or i.startswith("update"):
                continue
            result[i] = asdict[i]

        return result

    def f_parse_from_log(self, js: dict):
        for i in js.keys():
            setattr(self, i, js[i])
        return self