import time
import cfg.configuration as cfg
import lib.logger as logger
import lib.comm_serial as ser

from lib.press_ctrl import *
from lib.temp_ctrl import *
from lib.imu_ctrl import *
from lib.safety_ctrl import *
from lib.fyi_ctrl import *
from lib.profile import *
from lib.task_ctrl import *

#get line from main arduino; decode it, store the data and execute an appropriate callback
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
    elif serial_line[0].upper().startswith("XYZ"):
        print("adding {}".format(serial_line))
        sensIMU.add_sample(serial_line)
        imu_callback()

    # Depth
    elif serial_line[0].upper().startswith("D"):
        print("adding {}".format(serial_line))
        safety.add_sample(serial_line)

#get line from secondary arduino;
def get_next_serial_line_safety():
    # send "I'm alive message"
    comm_safety.write("N:11")

    serial_line = comm.read()  # e.g. data=['P1', '1.23']
    print("raw: {}".format(serial_line))
    serial_line = serial_line.strip().decode('utf-8', 'ignore').split(":")

    if serial_line[0].upper().startswith("N"):
        print("adding {}".format(serial_line))
        safety.add_sample(serial_line)
        safety_callback()

def end_mission(why):
    log.write("mission was ended: {}".format(why))



#---------- Callbacks--------------#

#when a new temperature sample arrives
def t_callback():
    pass

#when a new pressure sample arrives
def p_callback():
    if cfg.Current_state == cfg.State.INIT:
        if sensPress._queues_are_full:
            cfg.Current_state = cfg.State.WAIT_FOR_WATER

    elif cfg.Current_state == cfg.State.WAIT_FOR_WATER:
        if sensPress.get_delta_up_down() >= cfg.pressure["epsilon"]:
            cfg.Current_state = cfg.State.EXEC_TASK

    elif cfg.Current_state == cfg.State.EXEC_TASK:
        cmd_to_send = task_ctrl.exec()
        if cmd_to_send: #not None
            comm.write(cmd_to_send)



#when a new IMU sample arrives
def imu_callback():
    pass

#when a new IMU sample arrives
def safety_callback():
    if safety.is_emergency_state():
        comm_safety.write("N:13") #report emergency to secondary arduino
        comm.write("U:193")


#-----------------------MAIN BODY--------------------------#

if __name__ == "__main__":
    log = logger.Logger()

    safety = Safety(cfg.safety["min_alt"], cfg.safety["max_interval_between_pings"], log)
    fyi = FYI(log)
    sensPress = Press(cfg.pressure["avg_samples"], cfg.pressure["epsilon"], log)
    sensTemp = Temp(cfg.temperature["avg_samples"], log)
    sensIMU = IMU(cfg.imu["avg_samples"], log)
    profile = Profile("cfg/profile.txt", log)
    task_ctrl = Task(sensPress, log)

    # Main arduino
    comm = ser.SerialComm(cfg.serial["port"], cfg.serial["baud_rate"], cfg.serial["timeout"], log)
    if not comm.ser:
        print("-E- Failed to init serial port")
        exit()

    # Secondary arduino (safety)
    comm_safety = ser.SerialComm(cfg.serial_safety["port"], cfg.serial_safety["baud_rate"], cfg.serial_safety["timeout"], log)
    if not comm.ser:
        print("-E- Failed to init safety serial port")
        exit()

    while True:
        get_next_serial_line()
        # get_next_serial_line_safety()


        #comm.write("U:55.55")
        #time.sleep(4)
        #comm.write("U:0")
        #time.sleep(4)
        # comm.write(bytes('D:55.55'))
        # time.sleep(1)
        # comm.write(bytes('U:0'))
        # time.sleep(1)
        # comm.write(bytes('D:0'))
        # time.sleep(1)
