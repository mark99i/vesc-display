import inspect
import os
import sys
import subprocess
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

def setup_empty_chart(chart:QChart):
    series = QLineSeries()
    series.append(0, 0)

    global chart_current_pen
    chart_current_pen = QPen()
    chart_current_pen.setColor(QColor(255, 255, 255, 255))
    chart_current_pen.setWidth(4)
    series.setPen(chart_current_pen)

    chart.removeAllSeries()
    chart.addSeries(series)
    # chart.createDefaultAxes()
    chart.legend().hide()
    chart.setBackgroundVisible(False)

def set_chart_series(chart: QChart, arr: list):
    series = QLineSeries()

    for i in range(1, len(arr)):
        series.append(i, arr[i-1])

    global chart_current_pen
    series.setPen(chart_current_pen)
    chart.removeAllSeries()
    chart.addSeries(series)


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
    return result[:-1]

def restart_systemd_status(service: str) -> None:
    if sys.platform == "win32":
        return None

    cmd = f"systemctl restart {service}"
    subprocess.check_output(["bash", "-c", cmd])
    return None
