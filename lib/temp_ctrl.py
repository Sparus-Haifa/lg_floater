from collections import deque


class Temp:
    def __init__(self, avg_samples, log):
        self.avg_samples = avg_samples
        self.log = log

        self.t1 = deque(maxlen=self.avg_samples)
        self.t2 = deque(maxlen=self.avg_samples)
        self.t3 = deque(maxlen=self.avg_samples)
        self.t4 = deque(maxlen=self.avg_samples)

        self.t1_avg = 0
        self.t2_avg = 0
        self.t3_avg = 0
        self.t4_avg = 0

        self.t12_avg = 0
        self.t34_avg = 0

        self._queues_are_full = False
        self.log.write("Temperature controller was initialized successfully\n")

    def add_sample(self, sample):
        # sample_arr = sample.split(":")
        if len(sample) != 2:
            return

        sample_id = sample[0].lower()
        sample_val = float(sample[1])

        if sample_id == "t1":
            # self.p1.popleft()
            self.t1.append(sample_val)
            self.t1_avg = sum(self.t1) / self.avg_samples
            self.t12_avg = (self.t1_avg + self.t2_avg) / 2

        elif sample_id == "t2":
            # self.p2.popleft()
            self.t2.append(sample_val)
            self.t2_avg = sum(self.t2) / self.avg_samples
            self.t12_avg = (self.t1_avg + self.t2_avg) / 2

        elif sample_id == "t3":
            # self.p3.popleft()
            self.t3.append(sample_val)
            self.t3_avg = sum(self.t3) / self.avg_samples
            self.t34_avg = (self.t3_avg + self.t4_avg) / 2

        elif sample_id == "t4":
            # self.p4.popleft()
            self.t4.append(sample_val)
            self.t4_avg = sum(self.t4) / self.avg_samples
            self.t34_avg = (self.t3_avg + self.t4_avg) / 2

        else:
            return

        # We can start using the samples once:
        #       We received data from all temperature sensors
        #       We received enough samples from all sensors
        if not self._queues_are_full:
            if len(self.t1) == self.avg_samples and \
                    len(self.t2) == self.avg_samples and \
                    len(self.t3) == self.avg_samples and \
                    len(self.t4) == self.avg_samples:
                self._queues_are_full = True
