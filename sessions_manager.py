import json
import os
import sys
import threading
import time

from config import Odometer, Config
from session import Session
from utils import get_script_dir


class SessionManager:
    session_history = []
    now_session = Session()

    def start_new_session(self):
        Odometer.full_odometer += Odometer.session_mileage
        Odometer.session_mileage = 0
        Config.odometer_distance_km_backup = Odometer.full_odometer
        Config.save()
        Odometer.save()
        self.now_session.ts_end = int(time.time())
        self.now_session.end_session_odometer = Odometer.full_odometer

        with open(get_script_dir() + f"/sessions/session_{self.now_session.ts_start}.json", "w") as fp:
            content = json.dumps(self.now_session.f_get_json(), indent=4)
            fp.write(content)
            os.fsync(fp)

        self.now_session = Session()
        self.now_session.ts_start = int(time.time())
        self.now_session.start_session_odometer = Odometer.full_odometer
        pass

    def resume_old_session(self):
        if not os.path.exists(get_script_dir() + "/configs/session_last.json"):
            return

        content = open(get_script_dir() + "/configs/session_last.json", "r").read()

        try:
            content = json.loads(content)
            self.now_session.f_parse_from_log(content)
        except:
            print("cannot parse last session for resume")
            return

        threading.Thread(target=self.session_autosaving, name="autosaving-session").start()
        pass

    def reload_session_list_async(self):


        pass

    def session_autosaving(self):
        while True:
            try:
                with open(get_script_dir() + "/configs/session_last.json", "w") as fp:
                    content = json.dumps(self.now_session.f_get_json(), indent=4)
                    fp.write(content)
                    os.fsync(fp)
                time.sleep(30)
            except: pass

