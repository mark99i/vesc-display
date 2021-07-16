import os
import sys

from PyQt5.QtWidgets import QApplication
import data_updater
from gui import GUIApp as GUIApp
from gui_lite import GUIApp as GUIAppLite
from utils import GUIAppComm, get_script_dir, UtilsHolder
from config import Config

log = None
if len(sys.argv) > 1:
    if not os.path.isfile(sys.argv[1]):
        print("argv[1] not file, launching in normal mode")
        input()
        exit(1)
    else:
        log = sys.argv[1]

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
    input()
    exit(1)

w_thread = None
while True:
    UtilsHolder.need_restart_app = False

    app = QApplication([])

    if Config.use_gui_lite:
        ui = GUIAppLite()
    else:
        ui = GUIApp()

    comm = GUIAppComm()
    comm.setCallback(ui.callback_update_gui)
    if w_thread is None:
        w_thread = data_updater.WorkerThread()
        w_thread.callback = comm.push_data
        w_thread.name = "data_updater"
        w_thread.play_log_path = log
        w_thread.start()
    w_thread.callback = comm.push_data
    ui.data_updater_thread = w_thread
    ui.show()
    w_thread.callback = None

    if not UtilsHolder.need_restart_app:
        break

w_thread.stopped_flag = True

app.exit(0)
exit(0)

