import time

from PyQt5 import uic
from PyQt5.QtChart import QChart, QChartView
from PyQt5.QtCore import Qt, pyqtSignal, QObject, pyqtSlot
from PyQt5.QtGui import QPainter, QIcon, QPixmap, QCursor
from PyQt5.QtWidgets import QLCDNumber, QPushButton, QMainWindow, QApplication, QPlainTextEdit, QLineEdit, \
    QTextEdit

import data_updater
import utils
from config import Config, Odometer
from gui_settings import GUISettings
from gui_state import GUIState
# noinspection PyUnresolvedReferences
from service_status import GUIServiceState


class Communicate(QObject):
    closeApp = pyqtSignal(GUIState)

    callback = None

    def push_data(self, state):
        self.closeApp.emit(state)

    def setCallback(self, callback):
        self.callback = callback
        self.closeApp.connect(self.on_update)

    @pyqtSlot(GUIState)
    def on_update(self, state):
        if self.callback is not None:
            self.callback(state)

class GUIApp:
    app: QApplication = None
    ui: QMainWindow = None

    settings: GUISettings = None
    service_status: GUIServiceState = None

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

    settings_button: QPushButton = None
    close_button: QPushButton = None
    uart_button: QPushButton = None

    data_updater_thread: data_updater.WorkerThread = None

    alt = False

    last_time = 0
    reqs = 0

    def __init__(self):
        self.app = QApplication([])
        self.ui = uic.loadUi(utils.get_script_dir(False) + "/main_window.ui")
        self.ui.setWindowFlag(Qt.FramelessWindowHint)

        self.settings = GUISettings()
        self.service_status = GUIServiceState(self)

        self.close_button = self.ui.close_button
        close_icon = QIcon()
        close_icon.addPixmap(QPixmap(utils.get_script_dir(False) + "/close.png"), QIcon.Selected, QIcon.On)
        self.close_button.setIcon(close_icon)
        self.close_button.clicked.connect(self.on_click_close_app)

        self.settings_button = self.ui.settings_button
        settings_icon = QIcon()
        settings_icon.addPixmap(QPixmap(utils.get_script_dir(False) + "/settings.png"), QIcon.Selected, QIcon.On)
        self.settings_button.setIcon(settings_icon)
        self.settings_button.clicked.connect(self.on_click_open_settings)

        self.chartView = self.ui.chart
        self.chart = self.chartView.chart()
        utils.setup_empty_chart(self.chart)
        self.chartView.setRenderHint(QPainter.Antialiasing, False)

        self.esc_a_element = self.ui.esc_a_desc
        self.esc_b_element = self.ui.esc_b_desc
        self.main_speed_lcd = self.ui.main_speed
        self.left_param = self.ui.left_param
        self.main_power = self.ui.main_power
        self.right_param = self.ui.right_param
        self.date = self.ui.date
        self.time = self.ui.time

        self.left_param.setAlignment(Qt.AlignCenter)
        self.main_power.setAlignment(Qt.AlignCenter)
        self.right_param.setAlignment(Qt.AlignCenter)
        self.date.setAlignment(Qt.AlignCenter)
        self.time.setAlignment(Qt.AlignCenter)

        self.right_param.mousePressEvent = self.on_click_right_param
        self.right_param.setReadOnly(True)

        self.esc_b_element.lower()
        self.esc_a_element.lower()

        self.uart_button = self.ui.uart_button
        self.uart_button.setStyleSheet("color: rgb(255, 255, 255);\nbackground-color: rgb(255, 0, 255);") # pink
        self.uart_button.clicked.connect(self.on_click_uart_settings)

    def show(self):
        self.ui.show()
        self.app.exec()

    def on_click_close_app(self):
        self.ui.hide()
        self.ui.destroy()
        raise Exception("exit")
        # TODO: need exit func

    def on_click_open_settings(self):
        self.settings.show()

    def on_click_uart_settings(self):
        self.service_status.show()

    def on_click_right_param(self, event):
        self.alt = not self.alt
        # TODO: alt func menu
        pass

    def callback_update_gui(self, state: GUIState):
        if self.settings.ui.isVisible():
            return
        if self.service_status.ui.isVisible():
            return

        self.esc_a_element.setPlainText(state.esc_a_state.build_gui_str())
        self.esc_b_element.setPlainText(state.esc_b_state.build_gui_str())

        power_str = f'{state.esc_a_state.phase_current + state.esc_b_state.phase_current}A / ' \
                    f'{state.full_power}W / ' \
                    f'{state.esc_a_state.battery_current + state.esc_b_state.battery_current}A'
        self.main_power.setText(power_str)

        #if state.speed > 0:
        #    wt_kmh = int((state.esc_a_state.power + state.esc_b_state.power) / state.speed)
        #    self.left_param.setText(f"{wt_kmh}W")
        #else:
        #    self.left_param.setText("0W")
        #self.left_param.setText()

        self.main_speed_lcd.display(str(round(state.speed, 1)))

        self.left_param.setText(state.battery_percent_str)
        if not self.alt:
            self.right_param.setText(str(Odometer.session_mileage)[:4])

        lt = time.localtime()
        self.date.setText(time.strftime("%d.%m.%y", lt))
        self.time.setText(time.strftime("%H:%M:%S", lt))

        if   state.uart_status == GUIState.UART_STATUS_ERROR:
            self.uart_button.setStyleSheet("color: rgb(255, 255, 255);\nbackground-color: rgb(255, 0, 0);border: none;") # red
        elif state.uart_status == GUIState.UART_STATUS_WORKING_SUCCESS:
            self.uart_button.setStyleSheet("color: rgb(255, 255, 255);\nbackground-color: rgb(0, 110, 0);border: none;") # green
        elif state.uart_status == GUIState.UART_STATUS_WORKING_ERROR:
            self.uart_button.setStyleSheet("color: rgb(255, 255, 255);\nbackground-color: rgb(85, 0, 255);border: none;")  # blue
        elif state.uart_status == GUIState.UART_STATUS_UNKNOWN:
            self.uart_button.setStyleSheet("color: rgb(255, 255, 255);\nbackground-color: rgb(255, 0, 255);border: none;") # pink

        self.reqs += 1
        if self.last_time < int(time.time()):
            if Config.chart_current_points > 0 or Config.chart_current_points > 0:
                utils.set_chart_series(self.chart, state.chart_current, state.chart_speed)
            print(self.reqs)
            if self.alt:
                self.right_param.setText(str(self.reqs))
            #print(utils.Battery.full_tracking_disabled)
            self.reqs = 0
            self.last_time = int(time.time())
        pass