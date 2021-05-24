import serial


class SerialComm:
    def __init__(self, port, baud_rate, _timeout, log):
        self.log = log
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = _timeout
        log.write("attempting to init serial comm\n")
        log.write(" port:" + port + "\n")
        log.write(" baud_rate:" + str(baud_rate) + "\n")
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            self.ser.flush()
            log.write("SerialComm was initialized successfully\n")
        except Exception as ex:
            log.write("-E- Failed to init serial port\n")
            log.write(" " + str(ex))
            self.ser = None


    def read(self):
        return self.ser.readline()

    def write(self, text):
        line = bytes(text, encoding='utf-8')

        self.ser.write(line)
