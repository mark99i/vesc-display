import time

# noinspection PyUnresolvedReferences
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QMouseEvent
from PyQt5.QtWidgets import QLCDNumber, QPushButton, QMainWindow, QApplication, QLineEdit, QMenu, QAction, QProgressBar

import data_updater
from gui_main_menu import GUIMainMenu
from gui_session import GUISession
from gui_speed_logic import GUISpeedLogic
from nsec_calculation import NSec
from utils import ButtonPos, ParamIndicators, get_script_dir, get_skin_size_for_display
from config import Config, Odometer
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

    main_speed_lcd: QLCDNumber = None

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
        self.ui.setWindowFlag(Qt.FramelessWindowHint)

        self.settings = GUISettings(self)
        self.service_status = GUIServiceState(self)
        self.session_info = GUISession(self)
        self.main_menu = GUIMainMenu(self)
        self.speed_logic = GUISpeedLogic(self)

        self.main_speed_lcd = self.ui.main_speed
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
        self.center_param_active_ind = ParamIndicators[Config.left_param_active_ind]

        self.uart_button = self.ui.uart_button
        self.uart_button.setStyleSheet("color: rgb(255, 255, 255);\nbackground-color: rgb(255, 0, 255);") # pink
        self.uart_button.clicked.connect(self.on_click_uart_settings)

        self.battery_progress_bar.mousePressEvent = self.on_click_battery
        self.main_speed_lcd.mousePressEvent = self.on_click_lcd

    def show(self):
        self.ui.show()

    def on_click_lcd(self, event: QMouseEvent):
        self.main_menu.show()

    def on_click_uart_settings(self):
        self.service_status.show()

    def on_click_right_param(self, event: QMouseEvent):
        self.show_menu_param_change(event, ButtonPos.RIGHT_PARAM)
        pass

    def on_click_left_param(self, event: QMouseEvent):
        self.show_menu_param_change(event, ButtonPos.LEFT_PARAM)
        pass

    def on_click_center_param(self, event: QMouseEvent):
        self.show_menu_param_change(event, ButtonPos.CENTER_PARAM)

    def on_click_battery(self, event: QMouseEvent):
        self.session_info.show()

    def show_menu_param_change(self, event: QMouseEvent, param_position: ButtonPos):
        menu = QMenu(self.ui)
        menu.setStyleSheet('color: rgb(255, 255, 255);font: 22pt "Consolas"; font-weight: bold; border-style: outset; border-width: 2px; border-color: beige;')

        actions = []
        if param_position == ButtonPos.LEFT_PARAM or param_position == ButtonPos.RIGHT_PARAM or param_position == ButtonPos.CENTER_PARAM:
            for indicator in [i for i in ParamIndicators]:
                name: str = indicator.name
                if param_position == ButtonPos.LEFT_PARAM and self.left_param_active_ind == indicator:
                    name = "✔ " + name
                if param_position == ButtonPos.CENTER_PARAM and self.right_param_active_ind == indicator:
                    name = "✔ " + name
                if param_position == ButtonPos.RIGHT_PARAM and self.right_param_active_ind == indicator:
                    name = "✔ " + name
                action = QAction()
                action.setData(param_position)
                action.setText(name)
                actions.append(action)

        self.last_menu_event = event
        menu.triggered.connect(self.menu_param_choosen)
        menu.addActions(actions)
        menu.exec(event.globalPos())

    def menu_param_choosen(self, action: QAction):
        choosen_item = action.text()
        param_pos = action.data()
        if " " in choosen_item: return

        print("set", choosen_item, "to", param_pos)

#        if choosen_item == ParamIndicators.NSec.name:
#            print("choosen nsec!!")
#            menu = QMenu(self.ui)
#            menu.setStyleSheet('color: rgb(255, 255, 255);font: 22pt "Consolas"; font-weight: bold; border-style: outset; border-width: 2px; border-color: beige;')

#            actions = []

#            for indicator in [i for i in NSec.NSecResult.OptionsEnum]:
#                name: str = indicator.name
                #if param_position == ButtonPos.LEFT_PARAM and self.left_param_active_ind == indicator:
                #    name = "✔ " + name
                #if param_position == ButtonPos.CENTER_PARAM and self.right_param_active_ind == indicator:
                #    name = "✔ " + name
                #if param_position == ButtonPos.RIGHT_PARAM and self.right_param_active_ind == indicator:
                #    name = "✔ " + name
#                action = QAction()
                #action.setData(param_position)
#                action.setText(name)
#                actions.append(action)

#            menu.addActions(actions)
#            menu.exec(self.last_menu_event.globalPos())

#            return


        if param_pos == ButtonPos.RIGHT_PARAM:
            self.right_param_active_ind = ParamIndicators[choosen_item]
            Config.right_param_active_ind = ParamIndicators[choosen_item].name
        if param_pos == ButtonPos.LEFT_PARAM:
            self.left_param_active_ind = ParamIndicators[choosen_item]
            Config.left_param_active_ind = ParamIndicators[choosen_item].name
        if param_pos == ButtonPos.CENTER_PARAM:
            self.center_param_active_ind = ParamIndicators[choosen_item]
            Config.center_param_active_ind = ParamIndicators[choosen_item].name
        Config.save()

    def callback_update_gui(self, state: GUIState):
        if self.speed_logic.ui.isVisible():
            self.speed_logic.update_speed(state)
            return

        if not self.ui.isActiveWindow():
            return

        self.main_speed_lcd.display(str(round(state.speed, 1)))
        self.battery_progress_bar.setValue(state.battery_percent)

        all_params_values = dict()
        all_params_values[0] = f"{state.battery_percent}%"
        all_params_values[1] = str(state.session_distance)[:4]
        all_params_values[2] = str(int(Odometer.full_odometer))
        all_params_values[3] = str(self.updates_in_sec)
        all_params_values[4] = str(round(state.wh_km, 1))
        all_params_values[5] = str(round(state.wh_km_Ns, 1))
        all_params_values[6] = str(state.estimated_battery_distance)[:4]
        all_params_values[7] = str(state.wh_km_h)
        all_params_values[8] = str(round(state.session.average_speed, 1))
        all_params_values[9] = str(state.full_power)

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


        self.calculation_updates_in_sec += 1
        if now_time_ms - self.last_time_check_updates_in_sec > 1000:
            self.updates_in_sec = self.calculation_updates_in_sec
            self.calculation_updates_in_sec = 0
            self.last_time_check_updates_in_sec = now_time_ms