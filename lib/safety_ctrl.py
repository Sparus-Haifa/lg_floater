from collections import deque
import sys


class Safety:
    def __init__(self, min_alt, log):
        self.log = log
        self.altidude = sys.maxsize
        self.hull_leak = False
        self.heydraulic_leak = False
        self.min_alt = min_alt

        self.log.write("Safety controller was initialized successfully\n")


    def add_sample(self, sample):
        sample_arr = sample.split(":")
        if len(sample_arr) != 2:
            return

        sample_id = sample_arr[0].lower()
        sample_val = float(sample_arr[1])

        if sample_id == "d": #altitude
            self.altidude = float(sample_val)

        elif sample_id == "h1": #Hull leak detector
            self.hull_leak = bool(sample_val)

        elif sample_id == "h2": #Hydraulic leak
            self.heydraulic_leak = bool(sample_val)

        else:
            return

        self.log.write("Updating safety info {}\n".format(sample))


    def is_emergency_state(self):
        if self.hull_leak:
            return True

        elif self.heydraulic_leak:
            return True

        elif self.altidude < self.min_alt:
            return True

        else:
            return False




