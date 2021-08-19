from collections import deque
class Sensor:
    def __init__(self, name, avg_samples):
        self.name = name
        self.avg_samples = avg_samples
        self.t = deque(maxlen=self.avg_samples)



    def getName(self):
        return self.name

    def getLast(self):
        if len(self.t)<self.avg_samples:
            # print(f"{self.getName()} buffer is empty")
            # return "Buffering"
            return f"Buffering ({len(self.t)}/{self.avg_samples})"
        return self.t[0]

    def add_sample(self, sample):
        # TODO: try catch parse
        self.t.append(sample)