from collections import deque
# from os import name
from lib.sensor import Sensor

class RPM(Sensor):
    _delta_up_down = ...  # type: float

    def __init__(self, name, avg_samples, log):
        super().__init__(name, avg_samples)
        # self.avg_samples = avg_samples
        self.log = log

        self.t = deque(maxlen=self.avg_samples)


        self._queues_are_full = False

        self.log.write("Press controller was initialized successfully\n")


    def add_sample(self, sample):
        self.t.append(sample)

    def getLast(self):
        if len(self.t)<1:
            print(f"{self.getName()} buffer is empty")
            return None
        return self.t[0]
            


