from collections import deque
from lib.sensor import Sensor


class Temp(Sensor):
    def __init__(self, name, avg_samples, precision, log):
        super().__init__(name, avg_samples, precision, log)
        # self.avg_samples = avg_samples
        # self.log = log

        self.t = deque(maxlen=self.avg_samples)

        self._queues_are_full = False
        self.log.info(f"{self.name} temperature sensor was initialized successfully")

    def add_sample(self, sample_arr):
        # if len(sample_arr) != 2:
            # return

        # sample_id = sample_arr[0].lower()
        # sample_val = float(sample_arr[1])
        
        # TODO:: try catch parse

        # self.t.append(float(sample_arr))
        # super().add_sample(float(sample_arr))
        super().add_sample(sample_arr)

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

    # def getLast(self):
    #     if len(self.t)<1:
    #         print(f"{self.getName()} buffer empty")
    #         return None
    #     return self.t[0]

    # def getName(self):
    #     return self.name