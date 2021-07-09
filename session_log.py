import time

import ujson as json
import os
import threading
from queue import Queue

import utils
from config import Config
from gui_state import GUIState

class SessionLog:
    have_init = False
    log_file_path = utils.get_script_dir() + "/session_log.json"
    old_log_file_path = utils.get_script_dir() + "/session_log_old.json"

    log_states_queue = Queue()

    def init(self):
        if self.have_init: return

        if os.path.isfile(self.log_file_path):
            os.replace(self.log_file_path, self.old_log_file_path)

        with open(self.log_file_path, "w") as fp:
            os.fsync(fp)

        threading.Thread(target=self.logging_thread_func, name="logging_thread").start()
        self.have_init = True

    def logging_thread_func(self):
        while True:
            while self.log_states_queue.qsize() < 100:
                time.sleep(1)
                continue

            file = open(self.log_file_path, "a")

            while True:
                try: state: GUIState = self.log_states_queue.get(block=False)
                except: break

                text_state = json.dumps(state.get_json_for_log())

                file.write(text_state)
                file.write("\n")

            os.fsync(file)
            file.close()

            print("written log")

    def write_state(self, state: GUIState):
        if not self.have_init:
            self.init()

        if Config.write_logs:
            self.log_states_queue.put(state)