from threading import Thread

# noinspection PyUnresolvedReferences
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt, pyqtSignal, QObject, pyqtSlot, QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont
from PyQt5.QtWidgets import QPushButton, QMainWindow, QLineEdit, QTextEdit, QListView, QDialog, QScroller

import network
import utils
from config import Config
from gui_state import GUIState


class GUISettingsIntMod(QDialog):
    change_step: int = 0
    parameter_val: int = 0
    parameter_name: str = None

    val_min = 0
    val_max = 0

    on_close_change_val = None

    def __init__(self, parent, parameter: str, step: int, on_close_change_val, val_min: int, val_max: int):
        super().__init__(parent)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: rgb(0, 0, 0); color: rgb(255, 255, 255);")

        self.on_close_change_val = on_close_change_val
        self.parameter_name = parameter
        self.change_step = step
        self.parameter_val = getattr(Config, parameter)
        self.val_min = val_min
        self.val_max = val_max

        self.textv = QLineEdit(self)
        self.textv.setStyleSheet("color: rgb(255, 255, 255);")
        self.textv.setGeometry(10, 20, 380, 30)
        self.textv.setReadOnly(True)
        self.textv.setDisabled(False)
        self.textv.setFont(QFont("Consolas", 16))
        self.textv.setText(parameter)

        self.val = QLineEdit(self)
        self.val.setStyleSheet("color: rgb(255, 255, 255); ")
        self.val.setGeometry(100, 70, 191, 61)
        self.val.setReadOnly(True)
        self.val.setDisabled(False)
        self.val.setFont(QFont("Consolas", 26))
        self.val.setAlignment(Qt.AlignCenter)
        self.val.setText(str(self.parameter_val))

        self.minus = QPushButton(self)
        self.minus.setStyleSheet("color: rgb(255, 255, 255); background-color: rgb(0, 0, 100); border: none;")
        self.minus.setGeometry(10, 70, 75, 61)
        self.minus.setFont(QFont("Consolas", 22))
        self.minus.setText("-")
        self.minus.clicked.connect(self.click_minus)

        self.plus = QPushButton(self)
        self.plus.setStyleSheet("color: rgb(255, 255, 255); background-color: rgb(0, 0, 100); border: none;")
        self.plus.setGeometry(310, 70, 75, 61)
        self.plus.setFont(QFont("Consolas", 22))
        self.plus.setText("+")
        self.plus.clicked.connect(self.click_plus)

        self.ok = QPushButton(self)
        self.ok.setStyleSheet("color: rgb(255, 255, 255); background-color: rgb(0, 150, 0); border: none;")
        self.ok.setGeometry(240, 150, 131, 41)
        self.ok.setFont(QFont("Consolas", 18))
        self.ok.setText("OK")
        self.ok.clicked.connect(self.click_ok)

        self.cancel = QPushButton(self)
        self.cancel.setStyleSheet("color: rgb(255, 255, 255); background-color: rgb(150, 0, 0); border: none;")
        self.cancel.setGeometry(30, 150, 131, 41)
        self.cancel.setFont(QFont("Consolas", 18))
        self.cancel.setText("Cancel")
        self.cancel.clicked.connect(self.click_cancel)

        self.check_min_max_val_disable_enable_buttons()
        self.show()

    def check_min_max_val_disable_enable_buttons(self):
        if self.parameter_val <= self.val_min:
            self.minus.setEnabled(False)
        else:
            self.minus.setEnabled(True)

        if self.parameter_val >= self.val_max:
            self.plus.setEnabled(False)
        else:
            self.plus.setEnabled(True)

    def click_plus(self):
        self.parameter_val += self.change_step
        self.val.setText(str(self.parameter_val))

        self.check_min_max_val_disable_enable_buttons()
        pass

    def click_minus(self):
        self.parameter_val -= self.change_step
        self.val.setText(str(self.parameter_val))

        self.check_min_max_val_disable_enable_buttons()
        pass

    def click_ok(self):
        setattr(Config, self.parameter_name, self.parameter_val)
        Config.save()
        self.on_close_change_val()
        self.destroy()
        pass

    def click_cancel(self):
        self.on_close_change_val()
        self.destroy()
        pass

class GUISettingsScanCan(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: rgb(0, 0, 0); color: rgb(255, 255, 255);")

        self.textv = QTextEdit(self)
        self.textv.setStyleSheet("color: rgb(255, 255, 255);")
        self.textv.setGeometry(10, 10, 381, 131)
        self.textv.setReadOnly(True)
        self.textv.setUndoRedoEnabled(False)
        self.textv.setDisabled(False)
        self.textv.setFont(QFont("Consolas", 24))
        self.textv.setText("scanning can bus... please wait")
        self.textv.setAlignment(Qt.AlignCenter)

        self.close = QPushButton(self)
        self.close.setStyleSheet("color: rgb(255, 255, 255); background-color: rgb(0, 0, 100); border: none;" )
        self.close.setGeometry(130, 150, 131, 41)
        self.close.setFont(QFont("Consolas", 18))
        self.close.setText("Close")
        self.close.clicked.connect(self.click_cancel)
        self.close.setDisabled(True)

    def show(self):
        utils.QTCommunication.run_func_in_background(self, network.Network.scan_can, self.on_scan_ended)
        super().show()

    def on_scan_ended(self, vescs: list):
        self.close.setDisabled(False)
        self.textv.setText("Scan complete! Result: " + str(vescs))
        pass

    def click_cancel(self):
        self.hide()
        pass

class GUISettings:
    ui: QMainWindow = None

    list_view: QListView = None
    list_model: QStandardItemModel = None

    scroller: QScroller = None

    opened_change_val = False

    def __init__(self):
        self.ui = uic.loadUi(utils.get_script_dir(False) + "/settings.ui")
        self.ui.setWindowFlag(Qt.FramelessWindowHint)

        close_button: QPushButton = self.ui.exit_settings
        close_button.clicked.connect(self.close_settings)

        self.list_view: QListView = self.ui.list_view
        self.list_model = QStandardItemModel()
        self.list_view.setModel(self.list_model)

        self.list_view.clicked[QModelIndex].connect(self.clicked_item)

        #self.list_view.verticalScrollBar().setFixedWidth(30)
        pass

    def get_list_item(self, text: str, s: bool = True):
        item = QStandardItem(text)
        item.setEditable(False)
        if s: item.setCheckState(False)
        return item

    def reload_list(self):
        self.opened_change_val = False
        self.list_model.removeRows(0, self.list_model.rowCount())
        #self.list_model.appendRow(self.get_list_item("scan vesc can bus"))
        #self.list_model.appendRow(self.get_list_item("-----------------", False))
        conf = Config.get_as_dict()
        for name in conf.keys():
            self.list_model.appendRow(self.get_list_item(f"{name}:\n\t{conf.get(name)}"))

    def open_int_mod(self, parameter, step, val_min, val_max):
        self.opened_change_val = True
        change_ui = GUISettingsIntMod(self.ui, parameter, step, self.reload_list, val_min, val_max)
        change_ui.show()

    def open_scan_can_bus(self):
        scan_can = GUISettingsScanCan(self.ui)
        scan_can.show()
        pass

    def clicked_item(self, s):
        if self.opened_change_val:
            return
        item = self.list_model.itemFromIndex(s)
        parameter_name = item.text()

        if ":" in parameter_name:
            parameter_name = parameter_name[0:parameter_name.find(":")]

        if   parameter_name == "delay_update_ms":
            self.open_int_mod(parameter_name, 1, 1, 1000)
        elif parameter_name == "esc_b_id":
            self.open_int_mod(parameter_name, 1, -1, 254)
        elif parameter_name == "chart_speed_points":
            self.open_int_mod(parameter_name, 5, 0, 1000)
        elif parameter_name == "chart_current_points":
            self.open_int_mod(parameter_name, 5, 0, 1000)
        elif parameter_name == "switch_a_b_esc":
            self.open_int_mod(parameter_name, 1, 0, 1)
        elif parameter_name == "hw_controller_current_limit":
            self.open_int_mod(parameter_name, 5, 0, 1000)
        elif parameter_name == "serial_speed":
            self.open_int_mod(parameter_name, 100, 600, 500000)
        elif parameter_name == "enable_uart_debug":
            self.open_int_mod(parameter_name, 1, 0, 1)
        elif parameter_name == "motor_magnets":
            self.open_int_mod(parameter_name, 1, 1, 100)
        elif parameter_name == "wheel_diameter":
            self.open_int_mod(parameter_name, 1, 30, 1000)
        elif parameter_name == "scan vesc can bus":
            self.open_scan_can_bus()

    def show(self):
        self.reload_list()
        self.ui.show()

    def close_settings(self):
        self.ui.close()
        pass

    pass
