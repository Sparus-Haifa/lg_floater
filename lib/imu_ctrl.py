from collections import deque
from os import name
from lib.sensor import Sensor

class IMU(Sensor):
    def __init__(self, name, avg_samples, log):
        super().__init__(name)
        self.log = log
        self.avg_samples = avg_samples

        # self.imu_samples = deque(maxlen=self.avg_samples) #queue of lists - [ [x,y,z,a], [x,y,z,a] ]
        self.t = deque(maxlen=self.avg_samples)

        self.log.write("IMU controller was initialized successfully\n")

    #IMU sample looks like XYZ:x,y,z,a
    def add_sample(self, sample):
        # sample_arr = sample.split(":")[1].split(",")
        # if len(sample_arr) != 4:
        #     self.log.write("-W- IMU add_sample - invalid sample {}\n".format(sample))
        #     return

        # self.imu_samples.append(sample_arr)
        # self.log.write("Added IMU sample: {}\n".format(str(sample_arr)))
        # TODO: try except parse
        self.t.append(float(sample))

    def getLast(self):
        if len(self.t)<1:
            print(f"{self.getName()} buffer is empty")
            return None
        return self.t[0]
