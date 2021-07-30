# noinspection PyUnresolvedReferences
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QLabel

from utils import *

class GUIMainMenu:
    ui: QDialog = None
    parent = None

    i_settings: QLabel = None
    i_speedlogic: QLabel = None
    i_session: QLabel = None
    i_session_history: QLabel = None
    i_return: QLabel = None
    i_close: QLabel = None

    def __init__(self, parent):
        self.ui = uic.loadUi(f"{get_script_dir(False)}/ui.layouts/main_menu_{get_skin_size_for_display()}.ui")
        from gui import GUIApp
        self.parent: GUIApp = parent
        self.ui.setWindowFlag(Qt.FramelessWindowHint)

        self.i_settings = self.setIcon(self.ui.i_settings, f"{get_script_dir(False)}/ui.images/settings.svg")
        self.i_speedlogic = self.setIcon(self.ui.i_speedlogic, f"{get_script_dir(False)}/ui.images/speedlogic.svg")
        self.i_session = self.setIcon(self.ui.i_session, f"{get_script_dir(False)}/ui.images/session_info.svg")
        self.i_session_history = self.setIcon(self.ui.i_session_history, f"{get_script_dir(False)}/ui.images/session_history.svg")
        self.i_close = self.setIcon(self.ui.i_close, f"{get_script_dir(False)}/ui.images/close.svg")
        self.i_return = self.setIcon(self.ui.i_return, f"{get_script_dir(False)}/ui.images/return.svg")

        self.i_settings.mousePressEvent = self.click_setting
        self.i_speedlogic.mousePressEvent = self.click_speedlogic
        self.i_session.mousePressEvent = self.click_session
        self.i_session_history.mousePressEvent = self.click_session_history
        self.i_close.mousePressEvent = self.click_close
        self.i_return.mousePressEvent = self.click_return

    @staticmethod
    def setIcon(widget: QLabel, path: str, sizex: int = 125, sizey: int = 125) -> QLabel:
        pic = QPixmap(path)
        pic = pic.scaled(QSize(sizey, sizex), Qt.KeepAspectRatio)
        widget.setPixmap(pic)
        return widget

    def show(self):
        self.ui.show()

    def click_setting(self, ev):
        self.parent.settings.show()
        self.ui.close()

    def click_close(self, ev):
        raise Exception("exit")
        # TODO: correctly exit

    def click_return(self, ev):
        self.ui.close()
        pass

    def click_speedlogic(self, ev):
        self.parent.speed_logic.show()
        self.ui.close()
        pass

    def click_session_history(self, ev):
        #self.ui.close()
        pass

    def click_session(self, ev):
        self.parent.session_info.show()
        self.ui.close()
        pass
