import inspect
import os
import sys
import subprocess
import time
from enum import Enum
from screeninfo import get_monitors

from PyQt5.QtChart import QChart, QLineSeries, QValueAxis
from PyQt5.QtCore import pyqtSignal, QThread, QObject, pyqtSlot
from PyQt5.QtGui import QPen, QColor


class ButtonPos(Enum):
    RIGHT_PARAM = "right_param"
    LEFT_PARAM = "left_param"
    CENTER_PARAM = "center_param"

class ParamIndicators(Enum):
    BatteryPercent = 0
    SessionDistance = 1
    Odometer = 2
    UpdatesPerSecond = 3
    WhKm = 4
    WhKmInNSec = 5
    BatteryEstDistance = 6
    WhKmH = 7
    AverageSpeed = 8
    FullPower = 9

class UtilsHolder:
    chart_power_pen = None
    chart_speed_pen = None
    chart_power_axis_y = None
    chart_speed_axis_y = None

    resolved_resolution = None

    need_restart_app = False

def get_script_dir(follow_symlinks=True):
    if getattr(sys, 'frozen', False): # py2exe, PyInstaller, cx_Freeze
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)

def setup_empty_chart(chart:QChart):
    series = QLineSeries()
    series.append(0, 0)

    UtilsHolder.chart_power_pen = QPen()
    UtilsHolder.chart_power_pen.setColor(QColor(255, 255, 255, 255))
    UtilsHolder.chart_power_pen.setWidth(4)
    series.setPen(UtilsHolder.chart_power_pen)

    UtilsHolder.chart_speed_pen = QPen()
    UtilsHolder.chart_speed_pen.setColor(QColor(0, 200, 0, 255))
    UtilsHolder.chart_speed_pen.setWidth(4)
    series.setPen(UtilsHolder.chart_speed_pen)

    UtilsHolder.chart_power_axis_y = QValueAxis()
    UtilsHolder.chart_power_axis_y.setVisible(False)

    UtilsHolder.chart_speed_axis_y = QValueAxis()
    UtilsHolder.chart_speed_axis_y.setVisible(False)

    chart.removeAllSeries()
    chart.addSeries(series)
    chart.legend().hide()
    chart.setBackgroundVisible(False)

def set_chart_series(chart: QChart, state):
    # определение типа структуры чтоб ide понимала что это
    # from gui_state import GUIState
    # state: GUIState = state

    arr_power = state.chart_power
    arr_speed = state.chart_speed

    chart_speed_max = max(max(arr_speed), with_percent(state.maximum_speed, -10)) # верх скорости
    chart_power_min = min(min(arr_power), with_percent(state.minimum_power, -60)) # низ мощности
    chart_power_max = max(max(arr_power), with_percent(state.maximum_power, -10)) # верх мощности

    UtilsHolder.chart_speed_axis_y.setRange(0, chart_speed_max)
    UtilsHolder.chart_power_axis_y.setRange(chart_power_min, chart_power_max)

    chart.removeAllSeries()
    if  len(arr_power) > 0:
        series_power = QLineSeries()
        for i in range(1, len(arr_power)):
            series_power.append(i, arr_power[i - 1])
        series_power.setPen(UtilsHolder.chart_power_pen)
        chart.addSeries(series_power)
        chart.setAxisY(UtilsHolder.chart_power_axis_y, series_power)

    if len(arr_speed) > 0:
        series_speed = QLineSeries()
        for i in range(1, len(arr_speed)):
            series_speed.append(i, arr_speed[i-1])
        series_speed.setPen(UtilsHolder.chart_speed_pen)
        chart.addSeries(series_speed)
        chart.setAxisY(UtilsHolder.chart_speed_axis_y, series_speed)

def with_percent(num, percent: int):
    return (num + (num / 100 * percent)) if percent > 0 else (num - (num / 100 * abs(percent)))

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
                if " positional argument" in str(e):
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

def distance_km_from_tachometer(tachometer: int) -> float:
    # tacho_scale = (conf->si_wheel_diameter * M_PI) / (3.0 * conf->si_motor_poles * conf->si_gear_ratio)
    # distance_meters = tachometer * tacho_scale;
    from config import Config
    wheel_diameter = Config.wheel_diameter / 1000

    if Config.motor_magnets < 1: return 0
    scale = (wheel_diameter * 3.1415926535) / (3.0 * Config.motor_magnets)
    distance_m = tachometer * scale
    return round(distance_m / 1000, 6)

def get_skin_size_for_display() -> str:
    if UtilsHolder.resolved_resolution is not None:
        return UtilsHolder.resolved_resolution

    all_skins = os.listdir(path=get_script_dir(False) + "/ui.layouts")
    all_sizes = []
    for skin_fn in all_skins:
        size = skin_fn[skin_fn.rfind("_") + 1:-3]
        if size not in all_sizes:
            all_sizes.append(size)

    monitor = get_monitors()
    if len(monitor) < 1:
        raise Exception("no monitors found")

    monitor = monitor[0]
    now_screen_size = f"{monitor.width}x{monitor.height}"

    if now_screen_size in all_sizes:
        UtilsHolder.resolved_resolution = now_screen_size
    else:
        UtilsHolder.resolved_resolution = "640x480" # defalut
        print("WARNING: UNSUPPORTED SCREEN SIZE")

    return UtilsHolder.resolved_resolution

def map_ard(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def stab(x, in_min, in_max):
    return max(min(in_max, x), in_min)

# noinspection PyUnresolvedReferences
class GUIAppComm(QObject):
    closeApp = pyqtSignal(object)

    callback = None

    def push_data(self, state):
        try: self.closeApp.emit(state)
        except: pass

    def setCallback(self, callback):
        self.callback = callback
        self.closeApp.connect(self.on_update)

    @pyqtSlot(object)
    def on_update(self, state):
        if self.callback is not None:
            self.callback(state)