import logging
import sys
import os
import datetime
class Logger:
    def __init__(self, test_mode: bool) -> None:
        self.log = logging.getLogger()
        self.log.setLevel(logging.NOTSET)
        console_handler = logging.StreamHandler(sys.stdout)
        # s = 'log.log'
        #e.g. 2021-03-10 10:34:12.678331
        current_datetime = str(datetime.datetime.now())

        #e.g. 20210310
        caurrent_date =  current_datetime.split(" ")[0].replace("-", "")

        #e.g. 103412
        current_time = current_datetime.split(" ")[1].split(".")[0].replace(":", "")

        #e.g. 20210310_103412.log
        s = log_name = caurrent_date + "_" + current_time + ".log"
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