import time

# noinspection PyUnresolvedReferences
from PyQt5 import uic
from PyQt5.QtChart import QChart, QChartView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QMouseEvent
from PyQt5.QtWidgets import QLCDNumber, QPushButton, QMainWindow, QPlainTextEdit, QLineEdit, \
    QTextEdit

import data_updater
from gui_main_menu import GUIMainMenu
from gui_session import GUISession
from gui_sessions_history import GUISessionHistory
from gui_speed_logic import GUISpeedLogic
from utils import get_script_dir, get_skin_size_for_display, setup_empty_chart, \
    set_chart_series, is_win
from indicators_changer import ButtonPos, ParamIndicators, ParamIndicatorsChanger
from config import Config
from gui_settings import GUISettings
from gui_state import GUIState
from service_status import GUIServiceState

class GUIApp:
    starter = None
    ui: QMainWindow = None

    main_menu: GUIMainMenu = None
    settings: GUISettings = None
    service_status: GUIServiceState = None
    session_info: GUISession = None
    speed_logic: GUISpeedLogic = None
    session_history: GUISessionHistory = None

    indicators_changer = None

    main_speed_lcd: QLCDNumber = None
    chart: QChart = None
    chartView: QChartView = None

    left_param: QLineEdit = None
    main_power: QLineEdit = None
    right_param: QLineEdit = None

    esc_a_element: QTextEdit = None
    esc_b_element: QPlainTextEdit = None

    date: QLineEdit = None
    time: QLineEdit = None

    uart_button: QPushButton = None

    data_updater_thread: data_updater.WorkerThread = None

    right_param_active_ind = ParamIndicators.SessionDistance
    left_param_active_ind = ParamIndicators.BatteryPercent

    last_time_check_updates_in_sec = 0
    calculation_updates_in_sec = 0
    updates_in_sec = 0

    last_time_chart_update = 0

    last_uart_status = ""

    def __init__(self, starter):
        from main import Starter
        self.starter: Starter = starter
        self.ui = uic.loadUi(f"{get_script_dir(False)}/ui.layouts/main_window_{get_skin_size_for_display()}.ui")
        if not is_win():
            self.ui.setWindowFlag(Qt.FramelessWindowHint)

        self.settings = GUISettings(self)
        self.service_status = GUIServiceState(self)
        self.session_info = GUISession(self)
        self.speed_logic = GUISpeedLogic(self)
        self.main_menu = GUIMainMenu(self)
        self.session_history = GUISessionHistory(self)

        self.indicators_changer = ParamIndicatorsChanger(self)

        self.chartView = self.ui.chart
        self.chart = self.chartView.chart()
        setup_empty_chart(self.chart)
        self.chartView.setRenderHint(QPainter.Antialiasing, False)

        self.esc_a_element = self.ui.esc_a_desc
        self.esc_b_element = self.ui.esc_b_desc
        self.main_speed_lcd = self.ui.main_speed
        self.left_param = self.ui.left_param
        self.main_power = self.ui.main_power
        self.right_param = self.ui.right_param
        self.date = self.ui.date
        self.time = self.ui.time
        self.main_speed_lcd.mousePressEvent = self.on_click_lcd

        self.left_param.setAlignment(Qt.AlignCenter)
        self.main_power.setAlignment(Qt.AlignCenter)
        self.right_param.setAlignment(Qt.AlignCenter)
        self.date.setAlignment(Qt.AlignCenter)
        self.time.setAlignment(Qt.AlignCenter)

        self.right_param.mousePressEvent = self.on_click_right_param
        self.left_param.mousePressEvent = self.on_click_left_param
        self.main_power.mousePressEvent = self.on_click_center_param

        self.right_param_active_ind = ParamIndicators[Config.right_param_active_ind]
        self.left_param_active_ind = ParamIndicators[Config.left_param_active_ind]

        self.esc_b_element.lower()
        self.esc_a_element.lower()

        self.uart_button = self.ui.uart_button
        self.uart_button.setStyleSheet("color: rgb(255, 255, 255);\nbackground-color: rgb(255, 0, 255);") # pink
        self.uart_button.clicked.connect(self.on_click_uart_settings)

    def show(self):
        self.ui.show()

    def on_click_uart_settings(self):
        self.service_status.show()

    def on_click_right_param(self, event: QMouseEvent):
        self.indicators_changer.show_menu_param_change(event, ButtonPos.RIGHT_PARAM)
        pass

    def on_click_left_param(self, event: QMouseEvent):
        self.indicators_changer.show_menu_param_change(event, ButtonPos.LEFT_PARAM)
        pass

    def on_click_lcd(self, ev):
        self.main_menu.show()

    # noinspection PyUnusedLocal
    def on_click_center_param(self, event: QMouseEvent):
        self.session_info.show()

    def callback_update_gui(self, state: GUIState):
        if self.speed_logic.ui.isVisible():
            self.speed_logic.update_speed(state)
            return

        if not self.ui.isActiveWindow():
            return

        self.esc_a_element.setPlainText(state.esc_a_state.build_gui_str(Config.mtemp_insteadof_load))
        self.esc_b_element.setPlainText(state.esc_b_state.build_gui_str(Config.mtemp_insteadof_load))

        power_str = f'{state.esc_a_state.phase_current + state.esc_b_state.phase_current}A / ' \
                    f'{state.full_power}W / ' \
                    f'{state.esc_a_state.battery_current + state.esc_b_state.battery_current}A'
        self.main_power.setText(power_str)

        self.main_speed_lcd.display(str(round(state.speed, 1)))

        all_params_values = self.indicators_changer.get_indicators_by_state(self, state)

        self.left_param.setText(all_params_values[self.left_param_active_ind.value])
        self.right_param.setText(all_params_values[self.right_param_active_ind.value])

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

        if now_time_ms - self.last_time_chart_update > Config.delay_chart_update_ms:
            if Config.chart_points > 0:
                set_chart_series(self.chart, state)
            self.last_time_chart_update = now_time_ms

        self.calculation_updates_in_sec += 1
        if now_time_ms - self.last_time_check_updates_in_sec > 1000:
            self.updates_in_sec = self.calculation_updates_in_sec
            self.calculation_updates_in_sec = 0
            self.last_time_check_updates_in_sec = now_time_ms