from collections import deque

class Press:
    _delta_up_down = ...  # type: float

    def __init__(self, avg_samples, epsilon, log):
        self.avg_samples = avg_samples
        self.epsilon = epsilon
        self.log = log

        self.t = deque(maxlen=self.avg_samples)


        self._queues_are_full = False

        self.log.write("Press controller was initialized successfully\n")


    def add_sample(self, sample):
        # TODO: try catch parse
        self.t.append(float(sample))

    def getLast(self):
        if len(self.t)<1:
            print("buffer is empty")
            return 0
        return self.t[0]
            


