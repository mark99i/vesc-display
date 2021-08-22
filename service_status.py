import json

# noinspection PyUnresolvedReferences
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton, QLineEdit, QDialog, QPlainTextEdit

import network
from gui_state import GUIState
from utils import get_script_dir, get_skin_size_for_display, QTCommunication, get_systemd_status, restart_systemd_status


class GUIServiceState:
    ui: QDialog = None
    parent = None

    le_systemd: QLineEdit = None
    le_con_state: QLineEdit = None
    le_esc_id: QLineEdit = None
    le_stats: QPlainTextEdit = None

    b_upd: QPushButton = None
    b_connect: QPushButton = None
    b_restart: QPushButton = None
    b_close: QPushButton = None

    def __init__(self, parent):
        self.ui = uic.loadUi(f"{get_script_dir(False)}/ui.layouts/vesc_uart_status_{get_skin_size_for_display()}.ui")
        self.parent = parent
        self.ui.setWindowFlag(Qt.FramelessWindowHint)
        self.ui.setStyleSheet("background-color: rgb(0, 0, 0); color: rgb(255, 255, 255);")

        self.le_systemd = self.ui.systemd_state
        self.le_con_state = self.ui.connection_state
        self.le_esc_id = self.ui.local_esc_id
        self.le_stats = self.ui.connection_stats
        self.b_upd = self.ui.update_info
        self.b_restart = self.ui.control_systemd_service
        self.b_connect = self.ui.connect_reconnect
        self.b_close = self.ui.close_button

        self.b_upd.clicked.connect(self.click_update_status)
        self.b_restart.clicked.connect(self.click_restart)
        self.b_connect.clicked.connect(self.click_reconnect)
        self.b_close.clicked.connect(self.click_close)

    def show(self):
        if self.ui.isVisible():
            self.ui.window().activateWindow()

        self.click_update_status()
        self.ui.show()

    def on_get_systemd_status(self, status: str):
        self.le_systemd.setText(f"systemd state: {status}")
        if "running" in status:
            QTCommunication.run_func_in_background(self.ui, network.Network.get_uart_status, self.on_get_uart_status)
            self.le_con_state.setText("serial state: loading...")
            self.le_esc_id.setText("local controller id: loading...")
        else:
            self.le_con_state.setText("serial state: unkn")
            self.le_esc_id.setText("local controller id: unkn")
            self.b_upd.setText("update\ninfo")
            self.b_upd.setEnabled(True)
        self.le_stats.setPlainText("")

    def on_get_uart_status(self, js: dict):
        if js is None: js = dict()
        self.le_con_state.setText("serial state: " + js.get("status", "unkn"))
        self.le_esc_id.setText("local controller id: " + str(js.get("local_id", -1)))
        self.le_stats.setPlainText(json.dumps(js.get("stats")).replace("{", "").replace("}", ""))
        self.b_upd.setText("update\ninfo")
        self.b_upd.setEnabled(True)

        if js.get("local_id", -1) != -1:
            self.parent.data_updater_thread.state.uart_status = GUIState.UART_STATUS_WORKING_ERROR

    def click_update_status(self):
        self.le_systemd.setText("systemd state: ...")
        self.le_con_state.setText("serial state: ...")
        self.le_esc_id.setText("local controller id: ...")
        self.le_stats.setPlainText("...")
        self.b_upd.setText("please\nwait")
        self.b_upd.setEnabled(False)
        QTCommunication.run_func_in_background(self.ui, get_systemd_status,
                                                     self.on_get_systemd_status, push_args="vesc-uart")
        pass

    # noinspection PyUnusedLocal
    def on_service_restarted(self, arg):
        self.b_restart.setText("restart\nservice")
        self.b_restart.setEnabled(True)
        self.click_update_status()

    def click_restart(self):
        self.b_restart.setText("please\nwait")
        self.b_restart.setEnabled(False)
        QTCommunication.run_func_in_background(self.ui, restart_systemd_status,
                                                     self.on_service_restarted, push_args="vesc-uart")

    # noinspection PyUnusedLocal
    def on_serial_reconnected(self, arg):
        self.b_connect.setText("reconnect\nserial")
        self.b_connect.setEnabled(True)
        self.click_update_status()

    def click_reconnect(self):
        self.b_connect.setText("please\nwait")
        self.b_connect.setEnabled(False)
        QTCommunication.run_func_in_background(self.ui, network.Network.connect, self.on_serial_reconnected)
        pass

    def click_close(self):
        self.ui.close()
        pass
