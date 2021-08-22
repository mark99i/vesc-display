# noinspection PyUnresolvedReferences
from PyQt5 import QtWidgets, uic
from PyQt5.QtChart import QChartView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPainter
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

    le_stats: QPlainTextEdit = None

    b_close: QPushButton = None
    b_reset: QPushButton = None
    b_bt_switch: QPushButton = None

    b_stats: QPushButton = None
    b_speed: QPushButton = None
    b_power: QPushButton = None

    chart: QChart = None
    chartView: QChartView = None
    chart_axis_y = QValueAxis()
    chart_axis_x = QValueAxis()

    now_state = "stats"
    history: bool = False
    history_session = None

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
            if self.ui.isVisible():
                self.ui.window().activateWindow()
                return

            QTCommunication.run_func_in_background(self, self.bg_restart_vescs, self.on_restart_ended)
            self.textv.setText("restarting vesc... please wait (5-10sec)")
            self.textv.setDisabled(False)
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
                self.parent.parent.data_updater_thread.sessions_manager.start_new_session()
                self.parent.update_text_stats()
                Battery.display_start_voltage = 0
            else:
                self.textv.setText("command error!")



        def click_cancel(self):
            self.hide()
            pass

    def __init__(self, parent, history_session_view = None):
        self.ui = uic.loadUi(f"{get_script_dir(False)}/ui.layouts/session_info_{get_skin_size_for_display()}.ui")
        from gui import GUIApp
        self.parent: GUIApp = parent
        self.history_session = history_session_view
        self.history = self.history_session is not None
        self.ui.setWindowFlag(Qt.FramelessWindowHint)

        self.le_stats = self.ui.stats
        self.b_close = self.ui.close_button
        self.b_bt_switch = self.ui.bt_switch
        self.b_reset = self.ui.reset_button
        self.b_stats = self.ui.b_stats
        self.b_speed = self.ui.b_speed
        self.b_power = self.ui.b_power

        self.b_close.clicked.connect(self.click_close)

        if not self.history:
            self.b_bt_switch.clicked.connect(self.click_bt_switch)

            self.reset_session = GUISession.GUIResetSession(self.ui, self)
            self.b_reset.clicked.connect(self.click_reset)
        else:
            self.b_bt_switch.setVisible(False)
            self.b_reset.setVisible(False)

        self.chartView = self.ui.chart
        self.chart = self.chartView.chart()
        self.chart.legend().hide()
        self.chart.setBackgroundVisible(False)
        self.chartView.setRenderHint(QPainter.Antialiasing, False)

        self.b_stats.clicked.connect(self.on_click_stats)
        self.b_speed.clicked.connect(self.on_click_speed)
        self.b_power.clicked.connect(self.on_click_power)

    def show(self):
        self.ui.show()
        self.update_session()

    def on_click_stats(self, ev): self.now_state = "stats"; self.update_session()
    def on_click_speed(self, ev): self.now_state = "speed"; self.update_session()
    def on_click_power(self, ev): self.now_state = "power"; self.update_session()

    def update_session(self):
        if self.now_state == "stats":
            self.chart.setVisible(False)
            self.le_stats.setVisible(True)
            self.b_stats.setStyleSheet("color: rgb(255, 255, 255); background-color: rgb(255, 0, 200); border: none;")
            self.b_speed.setStyleSheet("color: rgb(255, 255, 255); background-color: rgb(85, 0, 0); border: none;")
            self.b_power.setStyleSheet("color: rgb(255, 255, 255); background-color: rgb(85, 0, 0); border: none;")
        else:
            self.chart.setVisible(True)
            self.le_stats.setVisible(False)

        if self.now_state == "stats":
            self.update_text_stats()

        if not self.history:
            sess = self.parent.data_updater_thread.sessions_manager.now_session
        else:
            sess = self.history_session

        if self.now_state == "speed":
            self.fill_chart(sess.speed_session_history, sess.distance_session_history)
            self.b_stats.setStyleSheet("color: rgb(255, 255, 255); background-color: rgb(85, 0, 0); border: none;")
            self.b_speed.setStyleSheet("color: rgb(255, 255, 255); background-color: rgb(255, 0, 200); border: none;")
            self.b_power.setStyleSheet("color: rgb(255, 255, 255); background-color: rgb(85, 0, 0); border: none;")
            pass

        if self.now_state == "power":
            self.fill_chart(sess.power_session_history, sess.distance_session_history)
            self.b_stats.setStyleSheet("color: rgb(255, 255, 255); background-color: rgb(85, 0, 0); border: none;")
            self.b_speed.setStyleSheet("color: rgb(255, 255, 255); background-color: rgb(85, 0, 0); border: none;")
            self.b_power.setStyleSheet("color: rgb(255, 255, 255); background-color: rgb(255, 0, 200); border: none;")
            pass

        if (self.ui.isActiveWindow() or self.ui.isVisible()) and not self.history:
            # threading.Timer not working because him execute function not in UI thread
            QTCommunication.run_func_in_background(self.ui,
                                                   need_run=lambda: time.sleep(self.AUTOUPDATE_INTERVAL_SEC),
                                                   callback=self.update_session)

    def fill_chart(self, y: list, x: list):
        self.chart_axis_y.setLabelsColor(QColor(255, 255, 255, 255))
        self.chart_axis_x.setLabelsColor(QColor(255, 255, 255, 255))

        chart_pen = QPen()
        chart_pen.setColor(QColor(255, 255, 255, 255))
        chart_pen.setWidth(3)

        series = QLineSeries()
        for i in range(0, len(x)):
            series.append(x[i], y[i])

        series.setPen(chart_pen)

        if len(x) == 0 or len(y) == 0:
            self.chart_axis_y.setMax(0)
            self.chart_axis_y.setMin(0)
            self.chart_axis_x.setMax(0)
            self.chart_axis_x.setMin(0)
        else:
            self.chart_axis_y.setMax(max(y))
            self.chart_axis_y.setMin(min(y))
            self.chart_axis_x.setMax(max(x))
            self.chart_axis_x.setMin(min(x))

        self.chart.removeAxis(self.chart_axis_x)
        self.chart.removeAxis(self.chart_axis_y)
        self.chart.removeAllSeries()
        self.chart.addSeries(series)
        self.chart.setAxisY(self.chart_axis_y, series)
        self.chart.setAxisX(self.chart_axis_x, series)


    def update_text_stats(self):
        # from gui_state import GUIState
        # state: GUIState = worker_thread.state

        if not self.history:
            state = self.parent.data_updater_thread.state
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
        else:
            from session import Session
            session: Session = self.history_session
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

watt used: {int(session.watt_hours * dist)} wh, efficiency {round(session.watt_hours, 2)} wh/km

max fet/motor temp: {session.maximum_fet_temp}/{session.maximum_motor_temp} °С

---
odometer: {round(session.start_session_odometer, 2)} -> {round(session.end_session_odometer, 2)} km
            """

        self.le_stats.setPlainText(text[1:-1])
        self.update_battery_tracking_state()

    def update_battery_tracking_state(self):
        self.b_bt_switch.setText(f"BT: {not Battery.full_tracking_disabled}")

    def click_reset(self):
        if not self.reset_session.isVisible():
            self.reset_session.show()

    def click_close(self):
        self.ui.close()
        if not self.history:
            self.reset_session.hide()
        pass

    def click_bt_switch(self):
        Battery.full_tracking_disabled = not Battery.full_tracking_disabled
        self.update_battery_tracking_state()
        pass