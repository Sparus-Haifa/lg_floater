from collections import deque
from lib.press_sens import Press
from lib.sensor import Sensor
from lib.press_ctrl import *


class Press_ctrl():
    def __init__(self, avg_samples, precision, epsilon, log):
        self.avg_samples = avg_samples
        self.precision = precision
        self.epsilon = epsilon
        self.log = log
        self.sensors = {}


    def addSensor(self, header):
        sensor = Press(header,self.avg_samples,self.precision,self.log)
        self.sensors[header]=sensor

    def getSensors(self):
        return self.sensors

    def senseWater(self):
        return False