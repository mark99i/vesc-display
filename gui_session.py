# noinspection PyUnresolvedReferences
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QPushButton, QLineEdit, QDialog, QPlainTextEdit

from config import Odometer
from gui_state import GUIState
from utils import *


class GUISession:
    ui: QDialog = None
    parent = None

    le_battery_tracking: QLineEdit = None
    le_stats: QPlainTextEdit = None

    b_close: QPushButton = None
    b_bt_switch: QPushButton = None

    def __init__(self, parent):
        self.ui = uic.loadUi(get_script_dir(False) + "/session_info.ui")
        from gui import GUIApp
        self.parent: GUIApp = parent
        self.ui.setWindowFlag(Qt.FramelessWindowHint)

        self.le_battery_tracking = self.ui.battery_tracking
        self.le_stats = self.ui.stats
        self.b_close = self.ui.close_button
        self.b_bt_switch = self.ui.bt_switch

        self.b_close.clicked.connect(self.click_close)
        self.b_bt_switch.clicked.connect(self.click_bt_switch)

    def show(self):
        self.show_text_stats(self.parent.data_updater_thread.state)
        self.update_battery_tracking_state()
        self.ui.show()

    def show_text_stats(self, state: GUIState):
        watt_h_used = int(state.esc_a_state.watt_hours_used + state.esc_b_state.watt_hours_used)

        text = f"""
session distance: {Odometer.session_mileage} km
average speed: {state.average_speed} km/h
maximum speed: {state.maximum_speed} km/h

watt_hours: used {watt_h_used} from {Battery.full_battery_wh} wh 
watt_hours_on_km: {round(state.wh_km, 2)} wh/km

odometer: {round(Odometer.full_odometer, 2)} km
"""

        self.le_stats.setPlainText(text[1:-1])
        pass

    def update_battery_tracking_state(self):
        self.le_battery_tracking.setText(f"battery full tracking: {not Battery.full_tracking_disabled}")

    def click_close(self):
        self.ui.close()
        pass

    def click_bt_switch(self):
        Battery.full_tracking_disabled = not Battery.full_tracking_disabled
        self.update_battery_tracking_state()
        pass