from collections import deque

class RPM:
    _delta_up_down = ...  # type: float

    def __init__(self, avg_samples, log):
        self.avg_samples = avg_samples
        self.log = log

        self.t = deque(maxlen=self.avg_samples)


        self._queues_are_full = False

        self.log.write("Press controller was initialized successfully\n")


    def add_sample(self, sample):
        self.t.append(sample)

    def getLast(self):
        if len(self.t)<1:
            print("buffer is empty")
            return 0
        return self.t[0]
            


