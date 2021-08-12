import json
import os
import sys
import threading
import time

from battery import Battery
from config import Odometer, Config
from session import Session
from utils import get_script_dir


class SessionManager:
    session_history = []
    now_session = Session()

    def start_new_session(self):
        Odometer.full_odometer = round(Odometer.full_odometer + Odometer.session_mileage, 2)
        Odometer.session_mileage = 0
        Config.odometer_distance_km_backup = Odometer.full_odometer
        Config.save()
        Odometer.save()
        self.now_session.ts_end = int(time.time())
        self.now_session.end_session_odometer = Odometer.full_odometer

        # записывать сессию в файл если она не пустая
        if self.now_session.average_speed != 0:
            self.write_session_with_ts(self.now_session)

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
            Battery.full_tracking_disabled = not self.now_session.battery_tracking_enabled
            Battery.display_start_voltage = self.now_session.battery_display_start_voltage
            Battery.recalc_full_battery_wh()
        except:
            print("cannot parse last session for resume")
            return

    def start_autosaving(self):
        threading.Thread(target=self.session_autosaving, name="autosaving-session").start()

    def write_session_with_ts(self, sess: Session):
        if not Config.write_session:
            return

        with open(get_script_dir() + f"/sessions/session_{sess.ts_start}.json", "w") as fp:
            if Config.write_session_track:
                content = json.dumps(sess.f_get_json())
            else:
                content = json.dumps(sess.f_get_json(), indent=4)
            fp.write(content)
            os.fsync(fp)

    def reload_session_list_async(self):
        self.session_history.clear()
        sessions_files = os.listdir(get_script_dir() + "/sessions")
        sessions_files.sort(reverse=True)

        for session_file in sessions_files:
            content = open(get_script_dir() + f"/sessions/{session_file}").read()
            sess = Session().f_parse_from_log(json.loads(content))
            self.session_history.append(sess)

    def session_autosaving(self):
        while True:
            try:
                with open(get_script_dir() + "/configs/session_last.json", "w") as fp:
                    if Config.write_session_track:
                        content = json.dumps(self.now_session.f_get_json())
                    else:
                        content = json.dumps(self.now_session.f_get_json(), indent=4)
                    fp.write(content)
                    os.fsync(fp)
                time.sleep(30)
            except: pass