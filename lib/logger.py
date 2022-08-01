import logging
import sys
import os
import datetime
class Logger:
    def __init__(self, test_mode: bool) -> None:
        self.log = logging.getLogger("normal")
        self.csv_log = logging.getLogger("csv")
        

        self.log.setLevel(logging.DEBUG)
        self.csv_log.setLevel(logging.NOTSET)

        console_handler = logging.StreamHandler(sys.stdout)
        
        # s = 'log.log'
        #e.g. 2021-03-10 10:34:12.678331
        current_datetime = str(datetime.datetime.now())

        #e.g. 20210310
        caurrent_date =  current_datetime.split(" ")[0].replace("-", "")

        #e.g. 103412
        current_time = current_datetime.split(" ")[1].split(".")[0].replace(":", "")

        #e.g. 20210310_103412.log
        # s = log_name = caurrent_date + "_" + current_time + ".log"
        log_notset = caurrent_date + "_" + current_time + "_debug.log"
        log_info = caurrent_date + "_" + current_time + "_info.log"
        log_csv = caurrent_date + "_" + current_time + ".csv"

        folder_path = os.path.join('log', caurrent_date)
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        full_path_notset = os.path.join(folder_path, log_notset)
        full_path_info = os.path.join(folder_path, log_info)
        full_path_csv = os.path.join(folder_path, log_csv)


        file_handler_notset = logging.FileHandler(full_path_notset)
        file_handler_info = logging.FileHandler(full_path_info)
        file_handler_csv = logging.FileHandler(full_path_csv)


        console_handler.setLevel(logging.WARNING)
        file_handler_notset.setLevel(logging.NOTSET)
        file_handler_info.setLevel(logging.INFO)
        file_handler_csv.setLevel(logging.NOTSET)


        

        if test_mode:
            formatter    = logging.Formatter('%(asctime)s:TEST-MODE:%(levelname)s: %(message)s')
        else:
            formatter    = logging.Formatter('%(asctime)s:%(levelname)s: %(message)s')

        csv_formatter    = logging.Formatter('%(asctime)s,%(message)s')
        
        console_handler.setFormatter(formatter)
        file_handler_notset.setFormatter(formatter)
        file_handler_info.setFormatter(formatter)
        file_handler_csv.setFormatter(csv_formatter)




        self.log.addHandler(console_handler)
        self.log.addHandler(file_handler_notset)
        self.log.addHandler(file_handler_info)
        self.csv_log.addHandler(file_handler_csv)



    def get_log(self):
        return self.log

    def get_csv_log(self):
        return self.csv_log

    