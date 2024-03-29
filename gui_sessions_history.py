
import time

# noinspection PyUnresolvedReferences
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont
from PyQt5.QtWidgets import QPushButton, QMainWindow, QLineEdit, QTextEdit, QListView, QDialog, QScroller, QApplication

import network
from battery import Battery
from config import Config, Odometer
from gui_session import GUISession
from sessions_manager import SessionManager
from utils import get_script_dir, get_skin_size_for_display, QTCommunication, UtilsHolder



class GUISessionHistory:
    parent = None
    ui: QDialog = None

    list_view: QListView = None
    list_model: QStandardItemModel = None

    scroller: QScroller = None

    sessions_manager: SessionManager = None
    openned_session_gui: GUISession = None

    opened_change_val = False

    def __init__(self, parent):
        self.parent = parent
        self.ui = uic.loadUi(f"{get_script_dir(False)}/ui.layouts/generic_list_window_{get_skin_size_for_display()}.ui")
        self.ui.setWindowFlag(Qt.FramelessWindowHint)

        close_button: QPushButton = self.ui.b_exit
        close_button.clicked.connect(self.close)

        le_title: QLineEdit = self.ui.le_title
        le_title.setText("Sessions")

        self.list_view: QListView = self.ui.lv_body
        self.list_model = QStandardItemModel()
        self.list_view.setModel(self.list_model)

        self.list_view.clicked[QModelIndex].connect(self.clicked_item)
        pass

    def get_list_item(self, text: str, data = None):
        item = QStandardItem(text)
        item.setData(data)
        item.setEditable(False)
        return item

    def reload_list(self):
        self.opened_change_val = False
        self.list_model.removeRows(0, self.list_model.rowCount())

        for session in self.sessions_manager.session_history:
            lt = time.localtime(session.ts_start)
            t = time.strftime("%d.%m %H:%M:%S", lt)
            lt = time.localtime(session.ts_end)
            t += " - " + time.strftime("%H:%M:%S", lt)
            dist = round(session.end_session_odometer - session.start_session_odometer, 1)

            # 🚀
            full_str = f"{t}\n ∿ {dist}km, {session.average_speed}km/h, {round(session.watt_hours, 1)}wh/km\n⁣"

            self.list_model.appendRow(self.get_list_item(full_str, session))

    def clicked_item(self, s):
        item = self.list_model.itemFromIndex(s)
        session = item.data()
        if self.openned_session_gui is None:
            self.openned_session_gui = GUISession(self.ui, session)
        else:
            self.openned_session_gui.history_session = session
        self.openned_session_gui.show()

    def show(self):
        if self.ui.isVisible():
            self.ui.window().activateWindow()
            return

        self.sessions_manager = self.parent.data_updater_thread.sessions_manager
        self.list_model.removeRows(0, self.list_model.rowCount())
        QTCommunication.run_func_in_background(self.ui, self.sessions_manager.reload_session_list_async, self.reload_list)
        self.ui.show()

    def close(self):
        self.ui.close()

    pass