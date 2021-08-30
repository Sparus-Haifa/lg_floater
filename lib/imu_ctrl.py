from collections import deque
from os import name
from lib.imu_sens import *
class IMU_ctrl:
    def __init__(self, avg_samples, precision, log):
        self.log = log
        self.avg_samples = avg_samples
        self.precision = precision
        self.sensors = {}

        # self.imu_samples = deque(maxlen=self.avg_samples) #queue of lists - [ [x,y,z,a], [x,y,z,a] ]
        # self.t = deque(maxlen=self.avg_samples)

        self.log.info("IMU controller was initialized successfully")

    def addSensor(self, header):
        sensor = IMU(header,self.avg_samples,self.precision,self.log)
        self.sensors[header]=sensor

    def getSensors(self):
        return self.sensors