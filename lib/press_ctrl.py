from collections import deque

class Press:
    _delta_up_down = ...  # type: float

    def __init__(self, avg_samples, epsilon, log):
        self.avg_samples = avg_samples
        self.epsilon = epsilon
        self.log = log

        self.p1 = deque(maxlen=self.avg_samples)
        self.p2 = deque(maxlen=self.avg_samples)
        self.p3 = deque(maxlen=self.avg_samples)
        self.p4 = deque(maxlen=self.avg_samples)
        self.p5 = deque(maxlen=self.avg_samples)
        self.p6 = deque(maxlen=self.avg_samples)

        self.p1_avg = 0
        self.p2_avg = 0
        self.p3_avg = 0
        self.p4_avg = 0

        self.p12_avg = 0
        self.p34_avg = 0

        self._delta_up_down = 0
        self._queues_are_full = False

        self.log.write("Press controller was initialized successfully\n")


    def add_sample(self, sample):
        # sample_arr = sample.split(":")
        if len(sample) != 2:
            return

        sample_id = sample[0].lower()
        sample_val = float(sample[1])

        if sample_id == "p1":
            # self.p1.popleft()
            self.p1.append(sample_val)
            self.p1_avg = sum(self.p1) / self.avg_samples
            self.p12_avg = (self.p1_avg + self.p2_avg)/2

        elif sample_id == "p2":
            # self.p2.popleft()
            self.p2.append(sample_val)
            self.p2_avg = sum(self.p2) / self.avg_samples
            self.p12_avg = (self.p1_avg + self.p2_avg) / 2

        elif sample_id == "p3":
            # self.p3.popleft()
            self.p3.append(sample_val)
            self.p3_avg = sum(self.p3) / self.avg_samples
            self.p34_avg = (self.p3_avg + self.p4_avg) / 2

        elif sample_id == "p4":
            # self.p4.popleft()
            self.p4.append(sample_val)
            self.p4_avg = sum(self.p4) / self.avg_samples
            self.p34_avg = (self.p3_avg + self.p4_avg) / 2

        elif sample_id == "p5":
            # self.p4.popleft()
            self.p5.append(sample_val)

        elif sample_id == "p6":
            # self.p4.popleft()
            self.p6.append(sample_val)

        else:
            return

        self._delta_up_down = abs(self.p34_avg - self.p12_avg)
        self.log.write("Added pessure sample: {}\n".format(str(sample)))
        self.log.write("New delta_up_down: {}\n".format(str(self._delta_up_down)))

        # We can start using the samples once:
        #       We received data from all pressure sensors
        #       We received enough samples from all sensors
        if not self._queues_are_full:
            if len(self.p1) == self.avg_samples and \
                    len(self.p2) == self.avg_samples and \
                    len(self.p3) == self.avg_samples and \
                    len(self.p4) == self.avg_samples:
                self._queues_are_full = True


    def get_delta_up_down(self):
        return self._delta_up_down




