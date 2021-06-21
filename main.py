import time
from threading import Thread

from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QLCDNumber
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, qRgb
from PyQt5.QtChart import QChart, QLineSeries, QChartView, QCategoryAxis

import data_updater

app = QtWidgets.QApplication([])
ui:QtWidgets.QMainWindow = uic.loadUi("untitled.ui")

# ui.setWindowFlag(Qt.FramelessWindowHint)

lcd:QLCDNumber = ui.mainSpeed
lcd.display(str(float(33.3)))

chartV:QChartView = ui.currentChart
chart:QChart = ui.currentChart.chart()

ser = [0, 0, 10, 60, 200, 700, 2000, 4000, 4000, 4000, 4000, 3500, 3700, 3600, 3000, 3200, 3400, 3700, 2000, 2400, 2300,
       2350, 2100, 1800, 1900, 500, 600, 1000, 1200, 1300, 2000, 1900, 1940, 1930, 1800, 500, 200, 200, 100, 50, 0, 0,
       0, 0, 10, 60, 100, 500, 1000, 3500, 3900, 3960, 4000, 3900, 3930, 3500, 3200, 3000, 2900, 2500, 2000, 2000, 2000,
       1800, 1500, 1500, 1500, 1900, 3000, 3700, 3700]


seriesX = QLineSeries()
for i in range(1, len(ser)):
    seriesX.append(i, ser[i-1])



pen = QPen()
pen.setColor(QColor(255, 255, 255, 255))
pen.setWidth(4)
seriesX.setPen(pen)

axisX = QCategoryAxis()
axisY = QCategoryAxis()

axisX.setLineVisible(False)
axisY.setLineVisible(False)

axisPen = QPen()
axisPen.setColor(QColor(255, 0, 0, 255))
axisY.setShadesPen(axisPen)

seriesX.attachAxis(axisX)
#chart.addAxis(axisX, Qt.AlignBottom)
#chart.addAxis(axisY, Qt.AlignLeft)

chart.addSeries(seriesX)

chart.setAxisX(axisX)
chart.setAxisY(axisY)

chart.legend().hide()

chart.createDefaultAxes()
chart.setBackgroundVisible(False)



chartV.setRenderHint(QPainter.Antialiasing)

chartV.setAutoFillBackground(True)


#chart.addSeries(series)
#chart.createDefaultAxes()

def set_lcd(text):
    lcd.display(text)

w = data_updater.WorkerThread(set_lcd)
w.start()

ui.show()
app.exec()

