import time

# noinspection PyUnresolvedReferences
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QLCDNumber, QPushButton, QMainWindow, QLineEdit, QProgressBar, QTextEdit, QLabel

import data_updater
from gui_main_menu import GUIMainMenu
from gui_session import GUISession
from gui_sessions_history import GUISessionHistory
from gui_speed_logic import GUISpeedLogic
from utils import get_script_dir, get_skin_size_for_display, map_ard, stab, is_win
from indicators_changer import ButtonPos, ParamIndicators, ParamIndicatorsChanger
from config import Config
from gui_settings import GUISettings
from gui_state import GUIState
from service_status import GUIServiceState

class GUIApp:
    starter = None
    ui: QMainWindow = None

    settings: GUISettings = None
    service_status: GUIServiceState = None
    session_info: GUISession = None
    main_menu: GUIMainMenu = None
    speed_logic: GUISpeedLogic = None
    session_history: GUISessionHistory = None

    indicators_changer = None

    main_speed_lcd: QLCDNumber = None
    session_description: QLabel = None
    settings_button: QLabel = None

    left_param: QLineEdit = None
    center_param: QLineEdit = None
    right_param: QLineEdit = None

    battery_progress_bar: QProgressBar = None

    date: QLineEdit = None
    time: QLineEdit = None

    uart_button: QPushButton = None

    data_updater_thread: data_updater.WorkerThread = None

    right_param_active_ind = ParamIndicators.SessionDistance
    center_param_active_ind = ParamIndicators.BatteryPercent
    left_param_active_ind = ParamIndicators.BatteryPercent

    last_time_check_updates_in_sec = 0
    calculation_updates_in_sec = 0
    updates_in_sec = 0

    last_menu_event: QMouseEvent = None
    last_uart_status = ""

    def __init__(self, starter):
        from main import Starter
        self.starter: Starter = starter
        self.ui = uic.loadUi(f"{get_script_dir(False)}/ui.layouts/main_window_lite_{get_skin_size_for_display()}.ui")
        if not is_win():
            self.ui.setWindowFlag(Qt.FramelessWindowHint)

        self.settings = GUISettings(self)
        self.service_status = GUIServiceState(self)
        self.session_info = GUISession(self)
        self.main_menu = GUIMainMenu(self)
        self.speed_logic = GUISpeedLogic(self)
        self.indicators_changer = ParamIndicatorsChanger(self)
        self.session_history = GUISessionHistory(self)

        self.main_speed_lcd = self.ui.main_speed
        self.session_description = self.ui.session_description
        self.left_param = self.ui.left_param
        self.center_param = self.ui.center_param
        self.right_param = self.ui.right_param
        self.date = self.ui.date
        self.time = self.ui.time
        self.battery_progress_bar = self.ui.battery_progress_bar

        self.right_param.mousePressEvent = self.on_click_right_param
        self.left_param.mousePressEvent = self.on_click_left_param
        self.center_param.mousePressEvent = self.on_click_center_param

        self.right_param_active_ind = ParamIndicators[Config.right_param_active_ind]
        self.left_param_active_ind = ParamIndicators[Config.left_param_active_ind]
        self.center_param_active_ind = ParamIndicators[Config.center_param_active_ind]

        self.settings_button = GUIMainMenu.setIcon(self.ui.settings_button, f"{get_script_dir(False)}/ui.images/settings.svg", 13)
        self.settings_button.mousePressEvent = self.on_click_lcd

        self.uart_button = self.ui.uart_button
        self.uart_button.setStyleSheet("color: rgb(255, 255, 255);\nbackground-color: rgb(255, 0, 255);") # pink
        self.uart_button.clicked.connect(self.on_click_uart_settings)

        self.battery_progress_bar.mousePressEvent = self.on_click_battery
        self.main_speed_lcd.mousePressEvent = self.on_click_lcd

        self.session_description.setWindowIconText("full")
        self.session_description.mousePressEvent = self.on_click_session_desc

    def show(self): self.ui.show()

    def on_click_lcd(self, event: QMouseEvent): self.main_menu.show()
    def on_click_uart_settings(self): self.service_status.show()

    def on_click_right_param(self, event: QMouseEvent): self.indicators_changer.show_menu_param_change(event, ButtonPos.RIGHT_PARAM)
    def on_click_left_param(self, event: QMouseEvent): self.indicators_changer.show_menu_param_change(event, ButtonPos.LEFT_PARAM)
    def on_click_center_param(self, event: QMouseEvent): self.indicators_changer.show_menu_param_change(event, ButtonPos.CENTER_PARAM)

    def on_click_battery(self, event: QMouseEvent): self.session_info.show()

    def on_click_session_desc(self, event: QMouseEvent):
        if self.session_description.windowIconText() == "full":
            # switch to last
            self.session_description.setWindowIconText("last")
            #self.data_updater_thread.calc_dynamic_session_enabled = True
        else:
            # switch to full
            self.session_description.setWindowIconText("full")
            #self.data_updater_thread.calc_dynamic_session_enabled = False

    def upd_session_desc(self, state: GUIState):
        if self.session_description.windowIconText() == "full":
            content = f"""
session statistics:

distance: {round(state.session.distance, 2)} km
max speed: {state.session.maximum_speed} km/h
avg speed: {state.session.average_speed} km/h

efficiency: {round(state.session.watt_hours, 2)} wh/km
max power: {state.session.maximum_phase_current}A/{state.session.maximum_power}W/{state.session.maximum_battery_current}A
            """
            self.session_description.setText(content[1:-1])

        if self.session_description.windowIconText() == "last":
            content = f"""
statistics from last start:

distance: {round(state.dynamic_session.distance, 2)} km
max speed: {state.dynamic_session.maximum_speed} km/h
avg speed: {state.dynamic_session.average_speed} km/h

efficiency: {round(state.dynamic_session.watt_hours, 2)} wh/km
max power: {state.dynamic_session.maximum_phase_current}A/{state.dynamic_session.maximum_power}W/{state.dynamic_session.maximum_battery_current}A
            """
            self.session_description.setText(content[1:-1])

    def callback_update_gui(self, state: GUIState):
        if self.speed_logic.ui.isVisible():
            self.speed_logic.update_speed(state)
            return

        if not self.ui.isActiveWindow() and not is_win():
            return

        self.main_speed_lcd.display(str(round(state.speed, 1)))
        self.battery_progress_bar.setValue(state.battery_percent)

        all_params_values = self.indicators_changer.get_indicators_by_state(self, state)

        self.left_param.setText(all_params_values[self.left_param_active_ind.value])
        self.right_param.setText(all_params_values[self.right_param_active_ind.value])
        self.center_param.setText(all_params_values[self.center_param_active_ind.value])

        now_time_ms = int(time.time() * 1000)
        lt = time.localtime((state.builded_ts_ms / 1000) if state.builded_ts_ms > 0 else (now_time_ms / 1000))
        self.date.setText(time.strftime("%d.%m.%y", lt))
        self.time.setText(time.strftime("%H:%M:%S", lt))

        if state.uart_status != self.last_uart_status:
            if   state.uart_status == GUIState.UART_STATUS_ERROR:
                self.uart_button.setStyleSheet("color: rgb(255, 255, 255);\nbackground-color: rgb(255, 0, 0);border: none;") # red
            elif state.uart_status == GUIState.UART_STATUS_WORKING_SUCCESS:
                self.uart_button.setStyleSheet("color: rgb(255, 255, 255);\nbackground-color: rgb(0, 110, 0);border: none;") # green
            elif state.uart_status == GUIState.UART_STATUS_WORKING_ERROR:
                self.uart_button.setStyleSheet("color: rgb(255, 255, 255);\nbackground-color: rgb(85, 0, 255);border: none;")  # blue
            elif state.uart_status == GUIState.UART_STATUS_UNKNOWN:
                self.uart_button.setStyleSheet("color: rgb(255, 255, 255);\nbackground-color: rgb(255, 0, 255);border: none;") # pink
            self.last_uart_status = state.uart_status

        if state.speed < 5:
            self.session_description.setHidden(False)
            session_desc_alpha = stab(int(map_ard(state.speed, 5, 0.5, 0, 255)), 0, 255)
            self.session_description.setStyleSheet(f"color: rgba(255, 255, 255, {session_desc_alpha}); background: rgba(0,0,0, {stab(session_desc_alpha + 20, 0, 255)});")
            self.upd_session_desc(state)

            if state.speed < 1:
                self.settings_button.setHidden(False)
            else:
                self.settings_button.setHidden(True)
        else:
            self.session_description.setHidden(True)
            self.settings_button.setHidden(True)

        self.calculation_updates_in_sec += 1
        if now_time_ms - self.last_time_check_updates_in_sec > 1000:
            self.updates_in_sec = self.calculation_updates_in_sec
            self.calculation_updates_in_sec = 0
            self.last_time_check_updates_in_sec = now_time_ms