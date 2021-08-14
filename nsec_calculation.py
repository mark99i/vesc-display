import json
import copy
from enum import Enum, auto

from config import Config
from gui_state import GUIState


class NSec:
    class NSecResult:
        min_voltage: float = 0
        max_voltage: float = 0
        min_b_current: float = 0
        max_b_current: float = 0
        min_p_current: float = 0
        max_p_current: float = 0
        min_speed: float = 0
        max_speed: float = 0
        distance: float = 0
        watts_used: float = 0
        watts_on_km: float = 0
        max_diff_voltage: float = 0

    states_arr = []
    last_result = NSecResult()

    # Подсчет значений NSecResult методом скользящего окна на основе последних (Config.nsec_calc_count) состояний
    def get_value(self, nstate: GUIState) -> NSecResult:
        if nstate.speed < 2 or Config.nsec_calc_count < 1:
            return self.last_result

        self.states_arr.append(copy.deepcopy(nstate))

        # берем самый старый state
        removed_state: GUIState = self.states_arr[0]

        # удаляем все что больше nsec_calc_count
        while len(self.states_arr) > Config.nsec_calc_count:
            self.states_arr.pop(0)

        result = NSec.NSecResult()

        full_wattes_used_now = nstate.esc_a_state.watt_hours_used + nstate.esc_b_state.watt_hours_used
        full_wattes_used_removed = removed_state.esc_a_state.watt_hours_used + removed_state.esc_b_state.watt_hours_used

        result.distance = nstate.session_distance - removed_state.session_distance
        result.watts_used = full_wattes_used_now - full_wattes_used_removed

        min_battery_current_state = nstate
        max_battery_current_state = nstate
        min_phase_current_state = nstate
        max_phase_current_state = nstate

        for state in self.states_arr:
            state: GUIState
            result.min_voltage = min(result.min_voltage, state.esc_a_state.voltage)
            result.max_voltage = max(result.max_voltage, state.esc_a_state.voltage)
            result.max_speed = max(result.max_speed, state.speed)
            result.min_speed = min(result.min_speed, state.speed)

            if min_battery_current_state.f_get_bc() > state.f_get_bc():
                min_battery_current_state = state

            if max_battery_current_state.f_get_bc() < state.f_get_bc():
                max_battery_current_state = state

            if min_phase_current_state.f_get_pc() > state.f_get_pc():
                min_phase_current_state = state

            if max_phase_current_state.f_get_pc() < state.f_get_pc():
                max_phase_current_state = state

        result.max_voltage.__round__(1)
        result.min_voltage.__round__(1)
        result.max_speed.__round__(1)
        result.min_speed.__round__(1)

        # если esc_b есть, то берем наименьший, если нет, то просто с A
        if Config.esc_b_id != -1:
            result.min_b_current = min(min_battery_current_state.esc_a_state.battery_current,
                                       min_battery_current_state.esc_b_state.battery_current)
            result.max_b_current = max(max_battery_current_state.esc_a_state.battery_current,
                                       max_battery_current_state.esc_b_state.battery_current)
            result.min_p_current = min(min_phase_current_state.esc_a_state.phase_current,
                                       min_phase_current_state.esc_b_state.phase_current)
            result.max_p_current = max(max_phase_current_state.esc_a_state.phase_current,
                                       max_phase_current_state.esc_b_state.phase_current)
        else:
            result.min_b_current = min_battery_current_state.esc_a_state.battery_current
            result.max_b_current = max_battery_current_state.esc_a_state.battery_current
            result.min_p_current = min_phase_current_state.esc_a_state.phase_current
            result.max_p_current = max_phase_current_state.esc_a_state.phase_current

        if result.distance > 0:
            result.watts_on_km = result.watts_used / result.distance
        result.max_diff_voltage = round(result.max_voltage - result.min_voltage, 1)

        self.last_result = result
        return result