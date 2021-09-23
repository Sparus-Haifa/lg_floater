import serial


class SerialComm:
    def __init__(self, name, port, baud_rate, _timeout, log):
        self.name = name
        self.log = log
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = _timeout
        log.debug("attempting to init serial comm")
        log.debug(" port:" + port)
        log.debug(" baud_rate:" + str(baud_rate))
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=self.timeout)
            self.ser.flush()
            log.info("SerialComm was initialized successfully")
        except Exception as ex:
            log.critical("-E- Failed to init serial port")
            log.critical(" " + str(ex))
            self.ser = None


    def read(self):
        if (self.ser.inWaiting()>0):
            return self.ser.readline()
        return b''

    def write(self, text):
        line = bytes(text, encoding='utf-8')
        self.log.debug(f"rpi>{self.name}: {text}")
        self.ser.write(line)
