import json
import os
import time

import utils
from battery import Battery
from config import Config


class Session:
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
    __ts_last_speed_more_2: int = 0

    speed_session_history: list = list()
    power_session_history: list = list()
    battery_session_history: list = list()
    ts_session_history: list = list()

    ts_start: int = 0
    ts_end: int = 0

    battery_tracking_enabled: bool = False
    battery_display_start_voltage: float = 0.0

    def update(self, state):
        # from gui_state import GUIState
        # state: GUIState = state
        if state.speed > 2:
            self.__av_speed_calc_sum += state.speed
            self.__av_speed_calc_count += 1
            self.average_speed = round(self.__av_speed_calc_sum / self.__av_speed_calc_count, 2)
            self.maximum_speed = round(max(self.maximum_speed, state.speed), 2)

            battery_current = state.esc_a_state.battery_current + state.esc_b_state.battery_current
            self.__av_battery_current_calc_sum += battery_current
            self.__av_battery_current_calc_count += 1
            self.average_battery_current = round(self.__av_battery_current_calc_sum / self.__av_battery_current_calc_count, 2)
            self.maximum_battery_current = round(max(self.maximum_battery_current, battery_current), 2)

            self.__ts_last_speed_more_2 = int(state.builded_ts_ms / 1000)
            if self.ts_start == 0:
                self.ts_start = int(state.builded_ts_ms / 1000)

            if Config.write_session_track:
                self.speed_session_history.append(state.speed)
                self.power_session_history.append(state.full_power)
                self.battery_session_history.append(state.battery_percent)
                self.ts_session_history.append(state.builded_ts_ms)

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
        self.watt_hours = state.wh_km

    def f_get_private_params(self):
        return self.__ts_last_speed_more_2

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