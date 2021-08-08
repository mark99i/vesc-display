from enum import Enum

from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QMenu, QAction

from config import Config


class ButtonPos(Enum):
    RIGHT_PARAM = "right_param"
    LEFT_PARAM = "left_param"
    CENTER_PARAM = "center_param"

class ParamIndicators(Enum):
    BatteryPercent = 0
    SessionDistance = 1
    Odometer = 2
    UpdatesPerSecond = 3
    WhKm = 4
    BatteryEstDistance = 6
    WhKmH = 7
    FullPower = 9
    NSec = 10           # not saved in config, only for open menu choose nsec

    nsec_min_voltage = 100
    nsec_max_voltage = 101
    nsec_min_b_current = 102
    nsec_max_b_current = 103
    nsec_min_p_current = 104
    nsec_max_p_current = 105
    nsec_min_speed = 106
    nsec_max_speed = 107
    nsec_distance = 108
    nsec_watts_used = 109
    nsec_watts_on_km = 110
    nsec_max_diff_voltage = 111

class ParamIndicatorsChanger:
    gui = None
    ui = None

    last_menu_event = None

    def __init__(self, gui):
        self.gui = gui
        self.ui = gui.ui

    def have_enabled_nsec(self) -> bool:
        from gui import GUIApp as NormalApp

        if type(self.gui) == NormalApp:
            if ParamIndicators[Config.right_param_active_ind].value < 100 and \
                ParamIndicators[Config.left_param_active_ind].value < 100:
                return False
        else:
            if ParamIndicators[Config.right_param_active_ind].value < 100 and \
                ParamIndicators[Config.center_param_active_ind].value < 100 and \
                ParamIndicators[Config.left_param_active_ind].value < 100:
                return False

        return False

    def is_menu_item_now_using(self, param_position: ButtonPos, indicator: ParamIndicators):
        if param_position == ButtonPos.LEFT_PARAM:
            if self.gui.left_param_active_ind == indicator:
                return True

            if indicator == ParamIndicators.NSec and self.gui.left_param_active_ind.value > 99:
                return True

        if param_position == ButtonPos.CENTER_PARAM:
            if self.gui.center_param_active_ind == indicator:
                return True

            if indicator == ParamIndicators.NSec and self.gui.center_param_active_ind.value > 99:
                return True

        if param_position == ButtonPos.RIGHT_PARAM:
            if self.gui.right_param_active_ind == indicator:
                return True

            if indicator == ParamIndicators.NSec and self.gui.right_param_active_ind.value > 99:
                return True

    def show_menu_param_change(self, event: QMouseEvent, param_position: ButtonPos):
        menu = QMenu(self.ui)
        menu.setStyleSheet('color: rgb(255, 255, 255);font: 22pt "Consolas"; font-weight: bold; border-style: outset; border-width: 2px; border-color: beige;')

        actions = []
        if param_position == ButtonPos.LEFT_PARAM or param_position == ButtonPos.RIGHT_PARAM or param_position == ButtonPos.CENTER_PARAM:
            for indicator in [i for i in ParamIndicators]:
                if indicator.value > 99: continue # NSec
                name: str = indicator.name
                if self.is_menu_item_now_using(param_position, indicator):
                    name = "✔ " + name
                action = QAction()
                action.setData(param_position)
                action.setText(name)
                actions.append(action)

        self.last_menu_event = event
        menu.triggered.connect(self.menu_param_choosen)
        menu.addActions(actions)
        menu.exec(event.globalPos())

    def menu_param_choosen(self, action: QAction):
        choosen_item = action.text()
        param_position = action.data()
        if "NSec" in choosen_item:
            choosen_item = "NSec"
        if " " in choosen_item: return

        print("set", choosen_item, "to", param_position)

        if choosen_item == ParamIndicators.NSec.name:
            menu = QMenu(self.ui)
            menu.setStyleSheet('color: rgb(255, 255, 255);font: 22pt "Consolas"; font-weight: bold; border-style: outset; border-width: 2px; border-color: beige;')

            actions = []

            for indicator in [i for i in ParamIndicators]:
                if indicator.value < 100: continue # non-NSec
                name: str = indicator.name

                if self.is_menu_item_now_using(param_position, indicator):
                    name = "✔ " + name

                action = QAction()
                action.setData(param_position)
                action.setText(name)
                actions.append(action)

            menu.addActions(actions)
            menu.triggered.connect(self.menu_param_nsec_choosen)
            menu.exec(self.last_menu_event.globalPos())
            return

        if param_position == ButtonPos.RIGHT_PARAM:
            self.gui.right_param_active_ind = ParamIndicators[choosen_item]
            Config.right_param_active_ind = ParamIndicators[choosen_item].name
        if param_position == ButtonPos.LEFT_PARAM:
            self.gui.left_param_active_ind = ParamIndicators[choosen_item]
            Config.left_param_active_ind = ParamIndicators[choosen_item].name
        if param_position == ButtonPos.CENTER_PARAM:
            self.gui.center_param_active_ind = ParamIndicators[choosen_item]
            Config.center_param_active_ind = ParamIndicators[choosen_item].name
        Config.save()

    def menu_param_nsec_choosen(self, action: QAction):
        choosen_item = action.text()
        param_position = action.data()
        if " " in choosen_item: return

        print("set", choosen_item, "to", param_position)

        if param_position == ButtonPos.RIGHT_PARAM:
            self.gui.right_param_active_ind = ParamIndicators[choosen_item]
            Config.right_param_active_ind = ParamIndicators[choosen_item].name
        if param_position == ButtonPos.LEFT_PARAM:
            self.gui.left_param_active_ind = ParamIndicators[choosen_item]
            Config.left_param_active_ind = ParamIndicators[choosen_item].name
        if param_position == ButtonPos.CENTER_PARAM:
            self.gui.center_param_active_ind = ParamIndicators[choosen_item]
            Config.center_param_active_ind = ParamIndicators[choosen_item].name
        Config.save()