import os
import sys

from PyQt5.QtWidgets import QApplication
from data_updater import WorkerThread
from gui import GUIApp as GUIApp
from gui_lite import GUIApp as GUIAppLite
from utils import GUIAppComm, get_script_dir, UtilsHolder
from config import Config

class Starter:
    log: str = None
    app = QApplication([])
    communication = GUIAppComm()

    active_ui = None
    worker_thread = WorkerThread()

    def parse_arg(self):
        if len(sys.argv) > 1:
            if not os.path.isfile(sys.argv[1]):
                print("argv[1] not file, exiting"); exit(1)
            else:
                self.log = sys.argv[1]

    def load_config(self):
        if not os.path.isdir(get_script_dir(False) + "/configs"):
            os.mkdir(get_script_dir(False) + "/configs")
        if not os.path.isdir(get_script_dir(False) + "/logs"):
            os.mkdir(get_script_dir(False) + "/logs")

        print("loading config ... ", end='')
        try:
            Config.load()
            print("ok, launching ui")
        except:
            print("fault!")
            input(); exit(1)

    def init_qt(self):
        self.app = QApplication([])

    def blocking_start_qt(self):
        self.app.exec() # blocking func

    def init_worker_thread(self):
        self.worker_thread.play_log_path = self.log
        self.worker_thread.start()
        pass

    def init_gui(self):
        if Config.use_gui_lite:
            self.active_ui = GUIAppLite(self)
        else:
            self.active_ui = GUIApp(self)

    def linking_gui_and_data_updater(self):
        self.communication.callback = self.active_ui.callback_update_gui
        self.worker_thread.callback = self.communication.push_data

        self.active_ui.data_updater_thread = self.worker_thread

    def restart_gui(self):
        self.communication.callback = None
        self.active_ui.ui.hide()
        self.active_ui.ui.destroy()

        self.init_gui()
        self.linking_gui_and_data_updater()
        self.active_ui.show()

    def start(self):
        self.parse_arg()
        self.load_config()

        self.init_qt()
        self.init_worker_thread()
        self.init_gui()
        self.linking_gui_and_data_updater()
        self.active_ui.show()
        self.blocking_start_qt()

if __name__ == "__main__":
    Starter().start()
    exit(0)
