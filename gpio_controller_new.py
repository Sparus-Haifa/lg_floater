from gpiozero import LED
from time import sleep


class GPIOController:
    def __init__(self, pin_bcm_num) -> None:
        from gpiozero import LED
        self.pin_number = pin_bcm_num
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setup(self.pin_number, GPIO.OUT)
        self.pin = LED(pin_bcm_num)

    def high(self):
        # GPIO.output(self.pin_number, GPIO.HIGH)
        self.pin.on()

    def low(self):
        # GPIO.output(self.pin_number, GPIO.LOW)
        self.pin.off()

    # def clean(self):
    #     GPIO.cleanup()




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
        # controller.clean()
        pass

    

if __name__=='__main__':
    main()
    