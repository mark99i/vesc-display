import inspect
import os
import sys
from threading import Thread

from PyQt5.QtChart import QChart, QLineSeries
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
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


class QTComm(QObject):
    closeApp = None
    callback = None

    def __init__(self):
        super().__init__()
        self.closeApp = pyqtSignal(object)

    def push_data(self, state):
        self.closeApp.emit(state)

    def setCallback(self, callback):
        self.callback = callback
        self.closeApp.connect(self.on_update)

    @pyqtSlot(object)
    def on_update(self, state):
        if self.callback is not None:
            self.callback(state)

class QTBG(Thread):
    callback = None
    need_run = None

    def __init__(self, need_run, callback):
        Thread.__init__(self)
        self.callback = callback
        self.need_run = need_run

    def run(self):
        self.callback(self.need_run())

def run_func_in_background(need_run, callback):
    comm = QTComm()
    comm.setCallback(callback)
    QTBG(need_run, comm.push_data).start()

def get_list_serial_ports() -> list:
    import serial.tools.list_ports
    ports = serial.tools.list_ports.comports()

    result = []
    for port, desc, hwid in sorted(ports):
        result.append(str(port))
    return result


