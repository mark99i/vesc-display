import time
import os
import threading
from queue import Queue, Empty

import utils
from config import Config


class SessionLog:
    LOGS_WRITE_DISK_EVENTS = 50

    have_init = False
    log_file_path = None

    log_states_queue = Queue()

    def init(self):
        if self.have_init: return

        lt = time.localtime()
        dt = time.strftime("%d.%m.%Y", lt) + "_" + time.strftime("%H.%M.%S", lt)

        self.log_file_path = f"{utils.get_script_dir()}/logs/session_{dt}.log"

        if os.path.isfile(self.log_file_path):
            os.replace(self.log_file_path, self.log_file_path + ".old")

        with open(self.log_file_path, "w") as fp:
            os.fsync(fp)

        threading.Thread(target=self.logging_thread_func, name="logging_thread").start()
        self.have_init = True

    def logging_thread_func(self):
        while True:
            while self.log_states_queue.qsize() < SessionLog.LOGS_WRITE_DISK_EVENTS and Config.write_logs:
                time.sleep(1)
                continue

            file = open(self.log_file_path, "a")

            while True:
                try: state: str = self.log_states_queue.get(block=False)
                except Empty: break

                file.write(state)
                file.write("\n")

            os.fsync(file)
            file.close()

            if not Config.write_logs:
                break

        self.have_init = False

    def write_state(self, state_d: str):
        if not self.have_init:
            self.init()

        self.log_states_queue.put(state_d)