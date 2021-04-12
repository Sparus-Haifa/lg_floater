import serial


class SerialComm:
    def __init__(self, port, baud_rate, log):
        self.log = log
        self.port = port
        self.baud_rate = baud_rate
        log.write("attempting to init serial comm\n")
        log.write(" port:" + port + "\n")
        log.write(" baud_rate:" + str(baud_rate) + "\n")
        try:
            self.ser = serial.Serial(port, baud_rate)
            self.ser.flush()
            log.write("SerialComm was initialized successfully\n")
        except Exception as ex:
            log.write("-E- Failed to init serial port\n")
            log.write(" " + str(ex))
            self.ser = None


    def read(self):
        return self.ser.readline()
