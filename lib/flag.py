from collections import deque
from os import name
from lib.sensor import Sensor

class Flag:
    def __init__(self, name, log):
        # super().__init__(name, 1)
        # self.avg_samples = avg_samples
        self.log = log

        self.status = None

        # self._queues_are_full = False
        self.log.write("Temperature controller was initialized successfully\n")

    def add_sample(self, sample_arr):
        # if len(sample_arr) != 2:
            # return

        # sample_id = sample_arr[0].lower()
        # sample_val = float(sample_arr[1])

        self.status=int(float(sample_arr))

        # self.log.write("Added temperature sample: {}\n".format(str(sample_arr)))

        # We can start using the samples once:
        #       We received data from all temperature sensors
        #       We received enough samples from all sensors
        # if not self._queues_are_full:
        #     if len(self.t1) == self.avg_samples and \
        #             len(self.t2) == self.avg_samples and \
        #             len(self.t3) == self.avg_samples and \
        #             len(self.t4) == self.avg_samples:
        #         self._queues_are_full = True

    def getLast(self):
        return self.status