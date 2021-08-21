# noinspection PyUnresolvedReferences
import threading

# noinspection PyUnresolvedReferences
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton, QLineEdit, QDialog, QLCDNumber

from gui_state import GUIState
from utils import *


class GUISpeedLogic:
    ui: QDialog = None
    parent = None

    lcd_speed: QLCDNumber = None
    le_on40: QLineEdit = None
    le_on50: QLineEdit = None
    le_on60: QLineEdit = None
    le_on70: QLineEdit = None
    le_status: QLineEdit = None
    le_updates: QLineEdit = None

    b_close: QPushButton = None
    b_clear: QPushButton = None

    need_show_updates = False

    mstatus = 0
    go_ts_ms = 0

    on40_fill = False
    on50_fill = False
    on60_fill = False
    on70_fill = False

    on50_enabled = True
    on60_enabled = True
    on70_enabled = True

    last_time_check_updates_in_sec = 0
    calculation_updates_in_sec = 0
    updates_in_sec = 0

    ST_CAN_GO = 1
    ST_GO = 2
    ST_NEED_STOP = 3
    ST_SUCCESS = 4
    ST_NEED_CLEAN = 5

    def __init__(self, parent):
        self.ui = uic.loadUi(f"{get_script_dir(False)}/ui.layouts/speed_logic_{get_skin_size_for_display()}.ui")
        from gui import GUIApp
        self.parent: GUIApp = parent
        self.ui.setWindowFlag(Qt.FramelessWindowHint)

        self.lcd_speed = self.ui.lcd_speed
        self.le_on40 = self.ui.on40
        self.le_on50 = self.ui.on50
        self.le_on60 = self.ui.on60
        self.le_on70 = self.ui.on70
        self.le_status = self.ui.status
        self.le_updates = self.ui.updates_count
        self.b_close = self.ui.close_button
        self.b_clear = self.ui.clear_info

        self.b_close.clicked.connect(self.click_close)
        self.b_clear.clicked.connect(self.click_clear)
        self.le_updates.mousePressEvent = self.click_updates
        self.le_on50.mousePressEvent = self.click_le_on50
        self.le_on60.mousePressEvent = self.click_le_on60
        self.le_on70.mousePressEvent = self.click_le_on70

    def show(self):
        if self.ui.isVisible():
            self.ui.window().activateWindow()

        self.ui.show()
        self.parent.data_updater_thread.speed_logic_mode_enabled = True
        self.lcd_speed.display("0.0")
        self.click_clear()
        self.le_updates.setText("-")

    def update_speed(self, state: GUIState):
        speed = state.speed
        self.lcd_speed.display(str(round(state.speed, 1)))
        if self.need_show_updates:
            self.calc_updates(state)

        if self.mstatus == self.ST_NEED_STOP:
            if speed < 1:
                if self.all_cleared():
                    self.set_status(self.ST_CAN_GO)
                else:
                    self.set_status(self.ST_NEED_CLEAN)
            return

        if self.mstatus == self.ST_CAN_GO:
            if speed > 1.1:
                self.set_status(self.ST_GO)
                self.go_ts_ms = state.builded_ts_ms
            return

        if self.mstatus == self.ST_GO:
            if speed < 0.8:
                self.set_status(self.ST_NEED_CLEAN)
                return

            if not self.on40_fill and speed > 40:
                self.on40_fill = True
                t_40 = round((state.builded_ts_ms - self.go_ts_ms) / 1000, 2)
                self.le_on40.setText(f"0-40: {t_40}s")
                if not self.on50_enabled and not self.on60_enabled and not self.on70_enabled:
                    self.set_status(self.ST_SUCCESS)

            if not self.on50_fill and speed > 50:
                self.on50_fill = True
                t_50 = round((state.builded_ts_ms - self.go_ts_ms) / 1000, 2)
                self.le_on50.setText(f"0-50: {t_50}s")

                if not self.on60_enabled and not self.on70_enabled:
                    self.set_status(self.ST_SUCCESS)

            if not self.on60_fill and speed > 60:
                self.on60_fill = True
                t_60 = round((state.builded_ts_ms - self.go_ts_ms) / 1000, 2)
                self.le_on60.setText(f"0-60: {t_60}s")

                if not self.on70_enabled:
                    self.set_status(self.ST_SUCCESS)

            if not self.on70_fill and speed > 70:
                self.on70_fill = True
                t_70 = round((state.builded_ts_ms - self.go_ts_ms) / 1000, 2)
                self.le_on70.setText(f"0-70: {t_70}s")

                self.set_status(self.ST_SUCCESS)

        pass

    def click_le_on50(self, ev):
        self.on50_enabled = not self.on50_enabled
        self.click_clear()
        pass
    def click_le_on60(self, ev):
        self.on60_enabled = not self.on60_enabled
        self.click_clear()
        pass
    def click_le_on70(self, ev):
        self.on70_enabled = not self.on70_enabled
        self.click_clear()
        pass

    def click_close(self):
        self.ui.close()
        self.parent.data_updater_thread.speed_logic_mode_enabled = False
        pass

    def click_updates(self, ev):
        self.need_show_updates = not self.need_show_updates
        if not self.need_show_updates:
            self.le_updates.setText("-")
            self.calculation_updates_in_sec = 0
            self.last_time_check_updates_in_sec = 0
        else:
            self.le_updates.setText("...")
            self.last_time_check_updates_in_sec = int(time.time() * 1000)


    def calc_updates(self, state):
        self.calculation_updates_in_sec += 1
        if state.builded_ts_ms - self.last_time_check_updates_in_sec > 1000:
            self.le_updates.setText(str(self.calculation_updates_in_sec))
            self.calculation_updates_in_sec = 0
            self.last_time_check_updates_in_sec = state.builded_ts_ms

    def click_clear(self):
        self.le_on40.setText("0-40: ...")
        self.le_on50.setText("0-50: ..." if self.on50_enabled else "0-50: -")
        self.le_on60.setText("0-60: ..." if self.on60_enabled else "0-60: -")
        self.le_on70.setText("0-70: ..." if self.on70_enabled else "0-70: -")
        self.on40_fill = False
        self.on50_fill = False
        self.on60_fill = False
        self.on70_fill = False
        self.set_status(self.ST_NEED_STOP)
        pass

    def all_cleared(self):
        return not self.on40_fill and not self.on50_fill and not self.on60_fill and not self.on70_fill

    def set_status(self, st: int):
        self.mstatus = st
        if   st == self.ST_CAN_GO:
            self.le_status.setText("Start!")
        elif st == self.ST_GO:
            self.le_status.setText("GO!")
        elif st == self.ST_NEED_STOP:
            self.le_status.setText("need stop!")
        elif st == self.ST_SUCCESS:
            self.le_status.setText("Success!")
        elif st == self.ST_NEED_CLEAN:
            self.le_status.setText("need clear!")



