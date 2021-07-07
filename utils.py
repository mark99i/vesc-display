import inspect
import math
import os
import sys
import subprocess
import time
from threading import Thread

from PyQt5.QtChart import QChart, QLineSeries
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from PyQt5.QtGui import QPen, QColor




def get_script_dir(follow_symlinks=True):
    if getattr(sys, 'frozen', False): # py2exe, PyInstaller, cx_Freeze
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)


chart_current_pen = None
chart_speed_pen = None

def setup_empty_chart(chart:QChart):
    series = QLineSeries()
    series.append(0, 0)

    global chart_current_pen
    chart_current_pen = QPen()
    chart_current_pen.setColor(QColor(255, 255, 255, 255))
    chart_current_pen.setWidth(4)
    series.setPen(chart_current_pen)

    global chart_speed_pen
    chart_speed_pen = QPen()
    chart_speed_pen.setColor(QColor(0, 200, 0, 255))
    chart_speed_pen.setWidth(4)
    series.setPen(chart_speed_pen)

    chart.removeAllSeries()
    chart.addSeries(series)
    # chart.createDefaultAxes()
    chart.legend().hide()
    chart.setBackgroundVisible(False)

def set_chart_series(chart: QChart, arr_current: list, arr_speed: list):
    chart.removeAllSeries()

    global chart_current_pen, chart_speed_pen

    if  len(arr_current) > 0:
        series_current = QLineSeries()
        for i in range(1, len(arr_current)):
            series_current.append(i, arr_current[i - 1])
        series_current.setPen(chart_current_pen)
        chart.addSeries(series_current)

    if len(arr_speed) > 0:
        series_speed = QLineSeries()
        for i in range(1, len(arr_speed)):
            series_speed.append(i, arr_speed[i-1])
        series_speed.setPen(chart_speed_pen)
        chart.addSeries(series_speed)

class Battery:

    MIN_CELL_VOLTAGE: float = 2.9
    NOM_CELL_VOLTAGE: float = 3.7
    MAX_CELL_VOLTAGE: float = 4.2

    full_battery_wh: int = 0
    display_start_voltage: float = 0
    non_full_start_voltage: bool = False

    last_percent: int = -100

    @staticmethod
    def init(now_voltage):
        from config import Config
        if Config.battery_cells < 1 or Config.battery_mah < 500:
            return
        Battery.full_battery_wh = int((Config.battery_cells * Battery.NOM_CELL_VOLTAGE * Config.battery_mah) / 1000)

        max_battery_voltage = Config.battery_cells * Battery.MAX_CELL_VOLTAGE
        min_voltage_for_full_charge = max_battery_voltage - (max_battery_voltage / 100 / 2) # mex_voltage - 0.5%

        Battery.display_start_voltage = now_voltage
        if now_voltage < min_voltage_for_full_charge:
            Battery.non_full_start_voltage = True

    @staticmethod
    def recalc_full_battery_wh():
        from config import Config
        Battery.full_battery_wh = int((Config.battery_cells * Battery.NOM_CELL_VOLTAGE * Config.battery_mah) / 1000)

    @staticmethod
    def calculate_battery_percent(voltage: float, watt_hours: int) -> str:
        if Battery.full_battery_wh == 0:
            return "-"

        estimated_wh = Battery.full_battery_wh - watt_hours
        battery_percent = int(100 / (Battery.full_battery_wh / estimated_wh))

        if Battery.last_percent == -100:
            Battery.last_percent = battery_percent
        else:
            if abs(Battery.last_percent - battery_percent) > 3:
                if Battery.last_percent < battery_percent:
                    battery_percent = Battery.last_percent + 1
                else:
                    battery_percent = Battery.last_percent - 1
            Battery.last_percent = battery_percent

        battery_percent = max(min(100, battery_percent), 0)
        return f"{battery_percent}%{'?' if Battery.non_full_start_voltage else ''}"



class QTCommunication:
    # noinspection PyUnresolvedReferences
    class QTBG(QThread):
        finish_signal = pyqtSignal(object)

        worker = None
        arg = None

        def __init__(self, parent=None):
            QThread.__init__(self, parent)

        def setData(self, worker, callback, arg):
            self.worker = worker
            self.finish_signal.connect(callback)
            self.arg = arg

        def run(self):
            try:
                result = self.worker(self.arg)
            except Exception as e:
                if "takes 0 positional arguments but 1 was given" in str(e):
                    result = self.worker()
                else:
                    print("bg exc:",e)
                    raise e
            self.finish_signal.emit(result)
            return

    @staticmethod
    def run_func_in_background(parent, need_run, callback, push_args: object = None):
        thread = QTCommunication.QTBG(parent)
        thread.setData(need_run, callback, push_args)
        thread.start()

def get_list_serial_ports() -> list:
    import serial.tools.list_ports
    ports = serial.tools.list_ports.comports()

    result = []
    for port, desc, hwid in sorted(ports):
        result.append(str(port))
    return result

def get_systemd_status(service: str) -> str:
    if sys.platform == "win32":
        return "unkn (win32, running)"

    cmd = f"systemctl status {service} | grep active | xargs | cut -d' ' -f 2-3"
    result = subprocess.check_output(["bash", "-c", cmd])
    return result[:-1].decode()

def restart_systemd_status(service: str) -> None:
    if sys.platform == "win32":
        return None

    cmd = f"sudo systemctl restart {service}"
    subprocess.check_output(["bash", "-c", cmd])

    # time for starting service
    time.sleep(5)
    return None
