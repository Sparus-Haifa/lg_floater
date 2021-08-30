from collections import deque
import sys
import datetime


class Safety:
    def __init__(self, min_alt, max_interval_between_pings, log):
        self.log = log
        self.altitude = sys.maxsize
        self.hull_leak = False
        self.hydraulic_leak = False
        self.min_alt = min_alt
        self.max_interval_between_pings = max_interval_between_pings
        self.last_ping = datetime.datetime.now()

        self.log.info("Safety controller was initialized successfully")


    def add_sample(self, sample_arr):
        if len(sample_arr) != 2:
            return

        sample_id = sample_arr[0].lower()
        sample_val = float(sample_arr[1])

        if sample_id == "d": #altitude
            self.altitude = float(sample_val)

        elif sample_id == "h1": #Hull leak detector
            self.hull_leak = bool(sample_val)

        elif sample_id == "h2": #Hydraulic leak
            self.hydraulic_leak = bool(sample_val)

        elif sample_id == "n":  # "alive" ping from secondary arduino
            if sample_val == 11:
                self.last_ping = datetime.datetime.now()

        else:
            return

        self.log.info("Updating safety info {}\n".format(sample_arr))

    def is_emergency_state(self):
        if self.hull_leak:
            return True

        elif self.hydraulic_leak:
            return True

        elif self.altitude < self.min_alt:
            return True

        elif  (datetime.datetime.now() - self.last_ping) > self.max_interval_between_pings:
            return True

        else:
            return False





