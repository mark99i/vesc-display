# noinspection PyUnresolvedReferences
import threading

# noinspection PyUnresolvedReferences
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton, QLineEdit, QDialog, QPlainTextEdit

from battery import Battery
from config import Odometer
from utils import *


class GUISession:
    AUTOUPDATE_INTERVAL_SEC = 5

    ui: QDialog = None
    parent = None

    le_battery_tracking: QLineEdit = None
    le_stats: QPlainTextEdit = None

    b_close: QPushButton = None
    b_bt_switch: QPushButton = None

    def __init__(self, parent):
        self.ui = uic.loadUi(f"{get_script_dir(False)}/ui.layouts/session_info_{get_skin_size_for_display()}.ui")
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
        self.ui.show()
        self.update_text_stats()

    def update_text_stats(self):
        data_updater_thread = self.parent.data_updater_thread
        state = data_updater_thread.state
        watt_h_used = int(state.esc_a_state.watt_hours_used + state.esc_b_state.watt_hours_used)

        text = f"""
session distance: {Odometer.session_mileage} km
session average speed: {state.average_speed} km/h
session maximum speed: {state.maximum_speed} km/h

watt hours used {watt_h_used} from {Battery.full_battery_wh}, est ~{Battery.full_battery_wh - watt_h_used} wh 
watt hours/km: {round(state.wh_km, 2)} wh/km

session maximum fet temp: {data_updater_thread.session_holder.ft_max} °С

---
odometer: {round(Odometer.full_odometer, 2)} km
"""

        self.le_stats.setPlainText(text[1:-1])
        self.update_battery_tracking_state()

        if self.ui.isActiveWindow():
            # threading.Timer not working because him execute function not in UI thread
            QTCommunication.run_func_in_background(self.ui,
                                                   need_run=lambda: time.sleep(GUISession.AUTOUPDATE_INTERVAL_SEC),
                                                   callback=self.update_text_stats)
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