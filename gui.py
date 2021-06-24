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

    main_speed_lcd: QLCDNumber = None
    chart: QChart = None
    chartView: QChartView = None

    battery_percent: QLineEdit = None
    main_power: QLineEdit = None
    watt_kmh: QLineEdit = None

    esc_a_element: QTextEdit = None
    esc_b_element: QTextEdit = None

    date: QLineEdit = None
    time: QLineEdit = None

    settings_button: QPushButton = None
    close_button: QPushButton = None

    last_time = 0
    reqs = 0

    def __init__(self):
        self.app = QApplication([])
        self.ui = uic.loadUi(utils.get_script_dir(False) + "/main_window.ui")
        self.ui.setWindowFlag(Qt.FramelessWindowHint)

        self.settings = GUISettings()

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
        self.esc_a_element.setWordWrapMode(QTextOption.ManualWrap)
        self.esc_b_element.setWordWrapMode(QTextOption.ManualWrap)
        self.esc_a_element.setAcceptRichText(False)
        self.esc_a_element.setContextMenuPolicy(Qt.NoContextMenu)
        self.esc_a_element.setReadOnly(True)
        self.esc_a_element.setUndoRedoEnabled(False)
        self.esc_b_element.setAcceptRichText(False)
        self.esc_b_element.setContextMenuPolicy(Qt.NoContextMenu)
        self.esc_b_element.setReadOnly(True)
        self.esc_b_element.setUndoRedoEnabled(False)

    def show(self):
        self.ui.show()
        self.app.exec()
        self.ui.setFocus(True)
        self.ui.activateWindow()
        self.ui.raise_()

    def on_click_close_app(self):
        self.ui.destroy()
        self.app.exit(0)
        pass

    def on_click_open_settings(self):
        self.settings.show()

    def callback_update_gui(self, state: GUIState):
        if self.settings.ui.isVisible():
            return

        self.esc_a_element.setPlainText(state.esc_a_state.build_gui_str())
        self.esc_b_element.setPlainText(state.esc_b_state.build_gui_str())

        power_str = f'{state.esc_a_state.phase_current + state.esc_b_state.phase_current}A / ' \
                    f'{state.esc_a_state.power + state.esc_b_state.power}W / ' \
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

        self.reqs += 1
        if self.last_time < int(time.time()):
            utils.set_chart_series(self.chart, state.chart_current)
            # print(self.reqs)
            self.battery_percent.setText(str(self.reqs))
            self.reqs = 0
            self.last_time = int(time.time())
        pass