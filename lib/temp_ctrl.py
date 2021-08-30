from collections import deque
from lib.temp_sens import *


class Temp_ctrl():
    def __init__(self, avg_samples, precision, log):
        self.avg_samples = avg_samples
        self.precision = precision
        self.log = log
        self.sensors = {}
        self.log.info("Temperature controller was initialized successfully")


    def addSensor(self, header):
        sensor = Temp(header,self.avg_samples,self.precision,self.log)
        self.sensors[header]=sensor


    def getSensors(self):
        return self.sensors