import os
import queue
import sys
from threading import Lock

from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QLCDNumber, QPushButton, QWidget, QMainWindow, QApplication, QPlainTextEdit, QLineEdit, \
    QTextEdit
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QObject, pyqtSlot
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, qRgb, QIcon, QPixmap, QTextOption
from PyQt5.QtChart import QChart, QLineSeries, QChartView, QCategoryAxis

import time
import data_updater
import utils
from gui_settings import GUISettings
from gui_state import GUIState, ESCState

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

    battery_percent: QLineEdit = None
    main_power: QLineEdit = None
    watt_kmh: QLineEdit = None

    esc_a_element: QTextEdit = None
    esc_b_element: QPlainTextEdit = None

    date: QLineEdit = None
    time: QLineEdit = None

    settings_button: QPushButton = None
    close_button: QPushButton = None
    uart_button: QPushButton = None

    data_updater_thread: data_updater.WorkerThread = None

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
        self.watt_kmh = self.ui.watt_kmh
        self.main_power = self.ui.main_power
        self.battery_percent = self.ui.battery_percent
        self.date = self.ui.date
        self.time = self.ui.time

        self.watt_kmh.setAlignment(Qt.AlignCenter)
        self.main_power.setAlignment(Qt.AlignCenter)
        self.battery_percent.setAlignment(Qt.AlignCenter)
        self.date.setAlignment(Qt.AlignCenter)
        self.time.setAlignment(Qt.AlignCenter)

        self.esc_b_element.lower()
        self.esc_a_element.lower()

        self.uart_button = self.ui.uart_button
        self.uart_button.setStyleSheet("color: rgb(255, 255, 255);\nbackground-color: rgb(255, 0, 255);") # pink
        self.uart_button.clicked.connect(self.on_click_uart_settings)

    def show(self):
        self.ui.show()
        self.app.exec()

    def on_click_close_app(self):
        self.ui.destroy()
        self.app.exit(0)
        pass

    def on_click_open_settings(self):
        self.settings.show()

    def on_click_uart_settings(self):
        self.service_status.show()

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

        if state.speed > 0:
            wt_kmh = int((state.esc_a_state.power + state.esc_b_state.power) / state.speed)
            self.watt_kmh.setText(f"{wt_kmh}W")
        else:
            self.watt_kmh.setText("0W")
        self.main_speed_lcd.display(str(round(state.speed, 1)))

        lt = time.localtime()
        self.date.setText(time.strftime("%d.%m.%y", lt))
        self.time.setText(time.strftime("%H:%M:%S", lt))

        if   state.uart_status == GUIState.UART_STATUS_ERROR:
            self.uart_button.setStyleSheet("color: rgb(255, 255, 255);\nbackground-color: rgb(255, 0, 0);") # red
        elif state.uart_status == GUIState.UART_STATUS_WORKING_SUCCESS:
            self.uart_button.setStyleSheet("color: rgb(255, 255, 255);\nbackground-color: rgb(0, 110, 0);") # green
        elif state.uart_status == GUIState.UART_STATUS_WORKING_ERROR:
            self.uart_button.setStyleSheet("color: rgb(255, 255, 255);\nbackground-color: rgb(85, 0, 255);")  # blue
        elif state.uart_status == GUIState.UART_STATUS_UNKNOWN:
            self.uart_button.setStyleSheet("color: rgb(255, 255, 255);\nbackground-color: rgb(255, 0, 255);") # pink

        self.reqs += 1
        if self.last_time < int(time.time()):
            utils.set_chart_series(self.chart, state.chart_current)
            # print(self.reqs)
            self.battery_percent.setText(str(self.reqs))
            self.reqs = 0
            self.last_time = int(time.time())
        pass