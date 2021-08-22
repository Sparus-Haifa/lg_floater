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
        return round(avg,self.precision)

    def add_sample(self, sample):
        # TODO: try catch parse
        try:
            value = float(sample)
        # except Exception as e:
        except ValueError as e:
            # print(e)
            # print(sample)
            # exit()
            print(f"SENSOR ERROR: [{self.name}]Overflow value") # TODO: add to log
            return
        # self.t.append(sample)
        self.t.append(value)

    def isBufferFull(self):
        return self.avg_samples == len(self.t)