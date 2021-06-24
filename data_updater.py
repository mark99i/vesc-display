import time
from threading import Thread

from config import Config
from gui_state import GUIState


class WorkerThread(Thread):
    callback = None
    stopped_flag = False

    def __init__(self, callback):
        Thread.__init__(self)
        self.callback = callback

    def run(self):
        time.sleep(1)

        state = GUIState()
        while True:
            if self.stopped_flag: return

            self.callback(state)

            state.speed += 0.1

            if state.speed > 100:
                state.speed = 0

            time.sleep(1000.0 / float(Config.refresh_rate) / 1000.0)