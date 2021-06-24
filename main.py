from PyQt5.QtWidgets import QApplication
import data_updater
import gui
from config import Config

print("loading config ... ", end='')
try:
    Config.load()
    print("ok, launching ui")
except:
    print("fault!")
    input()

app = QApplication([])
ui = gui.GUIApp()

comm = gui.Communicate()
comm.setCallback(ui.callback_update_gui)

thread = data_updater.WorkerThread(comm.push_data)
thread.start()
ui.show()
thread.stopped_flag = True

app.exit(0)
exit(0)

