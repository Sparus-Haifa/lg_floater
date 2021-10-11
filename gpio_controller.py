import RPi.GPIO as GPIO




class GPIOController:
    def __init__(self, pin_bcm_num) -> None:
        self.pin_number = pin_bcm_num
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin_number, GPIO.OUT)

    def high(self):
        GPIO.output(self.pin_number, GPIO.HIGH)

    def low(self):
        GPIO.output(self.pin_number, GPIO.LOW)

    def clean(self):
        GPIO.cleanup()




def main():
    import time
    controller = GPIOController(14)

    try:
        while True:
            controller.high()
            print('high')
            time.sleep(1)
            controller.low()
            print('low')
            time.sleep(1)
    except KeyboardInterrupt:
        controller.clean()

    

if __name__=='__main__':
    main()
    