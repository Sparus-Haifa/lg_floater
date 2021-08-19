from collections import deque
class Sensor:
    def __init__(self, name, avg_samples, precision):
        self.name = name
        self.avg_samples = avg_samples
        self.t = deque(maxlen=self.avg_samples)
        self.precision = precision



    def getName(self):
        return self.name

    def getLast(self):
        if len(self.t)<self.avg_samples:
            # print(f"{self.getName()} buffer is empty")
            # return "Buffering"
            return f"Buffering ({len(self.t)}/{self.avg_samples})"

        avg = sum(self.t)/len(self.t)
        # return self.t[0]
        return round(avg,2)

    def add_sample(self, sample):
        # TODO: try catch parse
        self.t.append(sample)

    def isBufferFull(self):
        return self.avg_samples == len(self.t)