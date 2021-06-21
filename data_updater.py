import time
from threading import Thread


class WorkerThread(Thread):
    callback = None

    def __init__(self, callback):
        Thread.__init__(self)
        self.callback = callback

    def run(self):

        i = 0.0
        while True:

            self.callback(str(round(i, 1)))

            i += 0.1

            time.sleep(0.01)