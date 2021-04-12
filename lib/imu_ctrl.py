from collections import deque


class IMU:
    def __init__(self, avg_samples, log):
        self.avg_samples = avg_samples
        self.log = log

        self.X = deque(maxlen=self.avg_samples)
        self.Y = deque(maxlen=self.avg_samples)
        self.Z = deque(maxlen=self.avg_samples)

        self.x_avg = 0
        self.y_avg = 0
        self.z_avg = 0

        self._queues_are_full = False
        self.log.write("IMU controller was initialized successfully\n")

    def add_sample(self, sample):
        # sample_arr = sample.split(":")
        if len(sample) != 2:
            return

        sample_id = sample[0].lower()
        sample_val = float(sample[1])

        if sample_id == "x":
            # self.p1.popleft()
            self.t1.append(sample_val)
            self.t1_avg = sum(self.t1) / self.avg_samples
            self.t12_avg = (self.t1_avg + self.t2_avg) / 2

        elif sample_id == "y":
            # self.p2.popleft()
            self.t2.append(sample_val)
            self.t2_avg = sum(self.t2) / self.avg_samples
            self.t12_avg = (self.t1_avg + self.t2_avg) / 2

        elif sample_id == "z":
            # self.p3.popleft()
            self.t3.append(sample_val)
            self.t3_avg = sum(self.t3) / self.avg_samples
            self.t34_avg = (self.t3_avg + self.t4_avg) / 2

        else:
            return

        # We can start using the samples once:
        #       We received data from all temperature sensors
        #       We received enough samples from all sensors
        if not self._queues_are_full:
            if len(self.x) == self.avg_samples and \
                    len(self.y) == self.avg_samples and \
                    len(self.z) == self.avg_samples:
                self._queues_are_full = True
