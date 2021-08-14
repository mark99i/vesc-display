# noinspection PyUnresolvedReferences
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QPushButton, QLineEdit, QDialog, QPlainTextEdit, QTextEdit

from battery import Battery
from config import Odometer, Config
from network import Network
from utils import *


class GUISessionFromHistory:
    ui: QDialog = None

    tv_stats: QPlainTextEdit = None
    b_close: QPushButton = None

    def __init__(self):
        self.ui = uic.loadUi(f"{get_script_dir(False)}/ui.layouts/generic_text_window_{get_skin_size_for_display()}.ui")
        self.ui.setWindowFlag(Qt.FramelessWindowHint)

        title: QLineEdit = self.ui.le_title
        title.setText("Session Rec")

        self.tv_stats = self.ui.tv_text
        self.b_close = self.ui.b_exit

        self.b_close.clicked.connect(self.click_close)

    def show(self, session):
        from session import Session
        session: Session = session
        time_start = time.strftime("%d.%m %H:%M:%S", time.localtime(session.ts_start))
        time_end = time.strftime("%d.%m %H:%M:%S", time.localtime(session.ts_end))
        dist = round(session.end_session_odometer - session.start_session_odometer, 2)

        text = f"""
session from {time_start} to {time_end}
distance: {dist} km
average speed: {session.average_speed} km/h
maximum speed: {session.maximum_speed} km/h
min/max power: {session.minimum_power}/{session.maximum_power} W
average battery current: {session.average_battery_current} A
maximum battery current: {session.maximum_battery_current} A
min/max phase current: {session.minimum_phase_current}/{session.maximum_battery_current} A

watt used: {int(session.watt_hours * dist)} wh 
watt hours/km: {session.watt_hours} wh/km

maximum fet temp: {session.maximum_fet_temp} °С
maximum motor temp: {session.maximum_motor_temp} °С

---
odometer: {round(session.start_session_odometer, 2)} -> {round(session.end_session_odometer, 2)} km
"""

        self.tv_stats.setPlainText(text[1:-1])
        self.ui.show()

    def click_close(self):
        self.ui.close()
        pass