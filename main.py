import cfg.configuration as cfg
import lib.logger as logger
import lib.comm_serial as ser

from lib.press_ctrl import *
from lib.temp_ctrl import *
from lib.imu_ctrl import *
from lib.safety_ctrl import *

#read line from serial port; decode it, store the data and execute an appropriate callback
def get_next_serial_line():
    serial_line = comm.read() # e.g. data=['P1', '1.23']
    print("raw: {}".format(serial_line))
    serial_line = serial_line.strip().decode('utf-8', 'ignore').split(":")

    #Pressure
    if serial_line[0].upper().startswith("P"):
        print("adding {}".format(serial_line))
        sensPress.add_sample(serial_line)
        p_callback()

    #Temperature
    elif serial_line[0].upper().startswith("T"):
        print("adding {}".format(serial_line))
        sensTemp.add_sample(serial_line)
        t_callback()

    #IMU
    elif serial_line[0].upper() in ["X", "Y", "Z"]:
        print("adding {}".format(serial_line))
        sensTemp.add_sample(serial_line)
        imu_callback()

    # Depth
    elif serial_line[0].upper().startswith("D"):
        print("adding {}".format(serial_line))
        sensTemp.add_sample(serial_line)


#---------- Callbacks--------------#

#when a new temperature sample arrives
def t_callback():
    pass

#when a new pressure sample arrives
def p_callback():
    if cfg.pressure.Current_state == cfg.State.INIT:
        if sensPress.queues_are_full:
            cfg.pressure.Current_state = cfg.State.WAIT_FOR_WATER

        elif cfg.pressure.Current_state == cfg.State.WAIT_FOR_WATER:
            if sensPress.get_delta_up_down >= cfg.pressure["epsilon"]:
                cfg.pressure.Current_state = cfg.State.EXEC_TASK

#when a new IMU sample arrives
def imu_callback():
    pass

#when a new IMU sample arrives
def safety_callback():
    pass


#-----------------------MAIN BODY--------------------------#

if __name__ == "__main__":
    log = logger.Logger()

    safety = Safety(log)
    sensPress = Press(cfg.pressure["avg_samples"], cfg.pressure["epsilon"], log)
    sensTemp = Temp(cfg.temperature["avg_samples"], log)
    sensIMU = IMU(cfg.imu["avg_samples"], log)

    comm = ser.SerialComm(cfg.serial["port"], cfg.serial["baud_rate"], log)
    if not comm.ser:
        print("-E- Failed to init serial port")
        exit()

    while True:
        get_next_serial_line()
