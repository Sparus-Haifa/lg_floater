import logging
import sys
import os
class Logger:
    def __init__(self, test_mode: bool) -> None:
        self.log = logging.getLogger()
        self.log.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler(sys.stdout)
        s = 'log.log'
        full_path = os.path.join('log',s)
        file_handler = logging.FileHandler(full_path)
        console_handler.setLevel(logging.WARNING)
        file_handler.setLevel(logging.INFO)
        

        if test_mode:
            formatter    = logging.Formatter('%(asctime)s:TEST-MODE:%(levelname)s: %(message)s')
        else:
            formatter    = logging.Formatter('%(asctime)s:%(levelname)s: %(message)s')

        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)


        self.log.addHandler(console_handler)
        self.log.addHandler(file_handler)

    def get_log(self):
        return self.log