from collections import deque
from lib.sensor import Sensor

class Altimeter(Sensor):
    def __init__(self, name, avg_samples, precision, log):
        super().__init__(name, avg_samples, precision, log)
        # self.avg_samples = avg_samples
        # self.log = log

        self.distance = deque(maxlen=self.avg_samples)
        self.confidance = deque(maxlen=self.avg_samples)

        self._queues_are_full = False
        self.log.info("Altimeter controller was initialized successfully")
        self.skipNext = False

    def reset(self):
        self.log.debug(f"clearing sensor {self.name} data")
        self.distance.clear()
        self.confidance.clear()

    async def add_sample(self, sample_arr):
        if self.skipNext:
            self.skipNext = False
            print("skipping adding alt sample")
            return
        try:
            value = float(sample_arr)
        except ValueError as e:
            self.log.error(f"SENSOR ERROR: [{self.name}] Overflow value [{sample_arr}]") # TODO: add to log
            self.skipNext=True
            return
        # self.t.append(sample)
        # self.t.append(value)

        self.distance.append(value)

    async def add_confidance(self, sample):
        if self.skipNext:
            self.skipNext = False
            print("skipping adding confidance sample")
            return
        try:
            value = float(sample)
        except ValueError as e:
            self.log.error(f"SENSOR ERROR: [{self.name}] Overflow value [{sample}]") # TODO: handale, duplicates
            self.skipNext=True
            return
        self.confidance.append(value)


    def getLast(self):
        if len(self.distance)<self.avg_samples:
            print(f"{self.getName()} buffer empty")
            return 0
        return self.distance[0]


    def getConfidance(self):
        if len(self.confidance)<self.avg_samples:
            print(f"{self.getName()} buffer empty")
            return 0
        return self.confidance[0]


    def isBufferFull(self):
        return self.avg_samples == len(self.distance) and self.avg_samples == len(self.confidance)