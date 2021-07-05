import inspect
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
