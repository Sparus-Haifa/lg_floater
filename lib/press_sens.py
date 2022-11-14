from collections import deque
from lib.sensor import Sensor

class Press(Sensor):
    _delta_up_down = ...  # type: float

    def __init__(self, name, avg_samples, precision, log, offset=0):
        super().__init__(name, avg_samples, precision, log, offset)
        # self.name = name
        # self.avg_samples = avg_samples
        # self.epsilon = epsilon
        # self.log = log


        self._queues_are_full = False

        self.log.info(f"{self.name} pressure sensor was initialized successfully")


    async def add_sample(self, sample):
        # TODO: try catch parse
        # super().add_sample(float(sample))
        await super().add_sample(sample)

    # def getLast(self):
    #     if len(self.t)<self.avg_samples:
    #         # print(f"{self.getName()} buffer is empty")
    #         return "Buffering"
    #     return self.t[0]
            

    # def getName(self):
    #     return self.name