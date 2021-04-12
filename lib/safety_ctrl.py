from collections import deque


class Safety:
    def __init__(self, log):
        self.log = log
        self.log.write("Safety controller was initialized successfully\n")


