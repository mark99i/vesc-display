# noinspection PyUnresolvedReferences
import threading

# noinspection PyUnresolvedReferences
import time

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QPushButton, QLineEdit, QDialog, QPlainTextEdit, QTextEdit

from battery import Battery
from config import Odometer, Config
from network import Network
from utils import *


class GUISession:
    AUTOUPDATE_INTERVAL_SEC: int = 5

    ui: QDialog = None
    parent = None

    reset_session = None

    le_battery_tracking: QLineEdit = None
    le_stats: QPlainTextEdit = None

    b_close: QPushButton = None
    b_reset: QPushButton = None
    b_bt_switch: QPushButton = None

    class GUIResetSession(QDialog):
        parent = None

        def __init__(self, parent_ui, parent_struct):
            super().__init__(parent_ui)
            self.parent = parent_struct
            self.setWindowFlag(Qt.FramelessWindowHint)
            self.setStyleSheet("background-color: rgb(0, 0, 0); color: rgb(255, 255, 255);")

            self.textv = QTextEdit(self)
            self.textv.setStyleSheet("color: rgb(255, 255, 255);")
            self.textv.setGeometry(10, 10, 381, 131)
            self.textv.setReadOnly(True)
            self.textv.setUndoRedoEnabled(False)
            self.textv.setDisabled(False)
            self.textv.setFont(QFont("Consolas", 24))
            self.textv.setText("restarting vesc... please wait (5-10sec)")
            self.textv.setAlignment(Qt.AlignCenter)

            self.close = QPushButton(self)
            self.close.setStyleSheet("color: rgb(255, 255, 255); background-color: rgb(0, 0, 100); border: none;")
            self.close.setGeometry(130, 150, 131, 41)
            self.close.setFont(QFont("Consolas", 18))
            self.close.setText("Close")
            self.close.clicked.connect(self.click_cancel)
            self.close.setDisabled(True)

        def show(self):
            QTCommunication.run_func_in_background(self, self.bg_restart_vescs, self.on_restart_ended)
            super().show()

        def bg_restart_vescs(self, args):
            res1 = Network.COMM_REBOOT([-1])
            time.sleep(5)

            res2 = True
            if Config.esc_b_id != -1:
                res2 = Network.COMM_REBOOT([Config.esc_b_id])
                time.sleep(5)

            return res1 and res2

        def on_restart_ended(self, data: bool):
            self.close.setDisabled(False)
            if data:
                self.textv.setText("reset completed!")

                self.parent: GUISession = self.parent
                self.parent.parent.data_updater_thread.state.reset_session()
                self.parent.update_text_stats()
                Battery.display_start_voltage = 0
            else:
                self.textv.setText("command error!")



        def click_cancel(self):
            self.hide()
            pass

    def __init__(self, parent):
        self.ui = uic.loadUi(f"{get_script_dir(False)}/ui.layouts/session_info_{get_skin_size_for_display()}.ui")
        from gui import GUIApp
        self.parent: GUIApp = parent
        self.ui.setWindowFlag(Qt.FramelessWindowHint)

        self.le_battery_tracking = self.ui.battery_tracking
        self.le_stats = self.ui.stats
        self.b_close = self.ui.close_button
        self.b_bt_switch = self.ui.bt_switch
        self.b_reset = self.ui.reset_button

        self.b_close.clicked.connect(self.click_close)
        self.b_bt_switch.clicked.connect(self.click_bt_switch)

        self.reset_session = GUISession.GUIResetSession(self.ui, self)
        self.b_reset.clicked.connect(self.click_reset)


    def show(self):
        self.ui.show()
        self.update_text_stats()

    def update_text_stats(self):
        data_updater_thread = self.parent.data_updater_thread
        # from gui_state import GUIState
        # state: GUIState = worker_thread.state
        state = data_updater_thread.state
        watt_h_used = int(state.esc_a_state.watt_hours_used + state.esc_b_state.watt_hours_used)

        text = f"""
distance: {round(Odometer.session_mileage, 2)} km
average speed: {round(state.session.average_speed, 2)} km/h
maximum speed: {round(state.session.maximum_speed, 2)} km/h
maximum power: {round(state.session.maximum_power, 2)} Wh
average battery current: {round(state.session.average_battery_current, 2)} A
maximum battery current: {round(state.session.maximum_battery_current, 2)} A

watt hours used {watt_h_used} from {Battery.full_battery_wh}, est ~{Battery.full_battery_wh - watt_h_used} 
watt hours/km: {round(state.wh_km, 2)} wh/km

maximum fet temp: {state.session.maximum_fet_temp} °С
maximum motor temp: {state.session.maximum_motor_temp} °С

---
odometer: {round(Odometer.full_odometer, 2)} km
"""

        self.le_stats.setPlainText(text[1:-1])
        self.update_battery_tracking_state()

        if self.ui.isActiveWindow() or self.ui.isVisible():
            # threading.Timer not working because him execute function not in UI thread
            QTCommunication.run_func_in_background(self.ui,
                                                   need_run=lambda: time.sleep(self.AUTOUPDATE_INTERVAL_SEC),
                                                   callback=self.update_text_stats)
        pass

    def update_battery_tracking_state(self):
        self.le_battery_tracking.setText(f"battery full tracking: {not Battery.full_tracking_disabled}")

    def click_reset(self):
        if not self.reset_session.isVisible():
            self.reset_session.show()

    def click_close(self):
        self.ui.close()
        self.reset_session.hide()
        pass

    def click_bt_switch(self):
        Battery.full_tracking_disabled = not Battery.full_tracking_disabled
        self.update_battery_tracking_state()
        pass