import datetime
import os
from pathlib import Path

class Logger:
    def __init__(self):
        self.__init_log()

    def write(self, text):
        self.__log.write("[ ")
        self.__log.write(str(datetime.datetime.now()))
        self.__log.write(" ] ")
        self.__log.write(text)

    def __init_log(self):
        #e.g. 2021-03-10 10:34:12.678331
        current_datetime = str(datetime.datetime.now())

        #e.g. 20210310
        caurrent_date =  current_datetime.split(" ")[0].replace("-", "")

        #e.g. 103412
        current_time = current_datetime.split(" ")[1].split(".")[0].replace(":", "")

        #e.g. 20210310_103412.log
        log_name = caurrent_date + "_" + current_time + ".log"

        #e.g. C:\Users\Ilan\projects\lg_floater\rpi\dev\lib
        current_dir = os.path.dirname(os.path.realpath(__file__))

        #e.g. C:\Users\Ilan\projects\lg_floater\rpi\dev\log
        log_dir = str(Path(current_dir).parent) + os.sep + "log"

        #e.g. C:\Users\Ilan\projects\lg_floater\rpi\dev\log\20210310_103412.log
        log_abs_path = log_dir + os.sep + log_name

        self.__log = open(log_abs_path, "w")
        self.write("Log was initialized successfully\n")










