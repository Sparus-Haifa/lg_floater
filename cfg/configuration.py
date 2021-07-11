from enum import Enum

class State(Enum):
    INIT = 1
    WAIT_FOR_WATER = 2
    EXEC_TASK = 3
    END_TASK = 4
    EMERGENCY = 5

Current_state = State.INIT

serial = {
    # /dev/ttyUSB0
    # "port": "/dev/ttyACM0",
    "port": "COM3",
    "timeout" : 3,
    "baud_rate": 115200
}

serial_safety = {
    # /dev/ttyUSB0
    # "port": "/dev/ttyACM0",
    "port": "COM4",
    "timeout" : 3,
    "baud_rate": 115200
}

pressure = {
    "epsilon": 0.05,
    "avg_samples": 5
}

temperature = {
    "avg_samples": 5
}

imu = {
    "avg_samples": 5
}

task = {
    "type": 1, # 1- pressure, 2-density, 3-profiling
    "duration": 300, # seconds
    "setpoint": 300, # will be used for types 1 & 2
    "setpoint_tollerance": 5, #asumming we won't hit the exact setpoint - +/1 setpoint_tollerance is good enough
    "fullduty_exec_time": 5, #num of seconds to operate the pump while in full-duty cycle mode
    "fullduty_min_distance": 100,
    "max_interval_between_movements": 100,
    "min_interval_between_movements": 5



    # "setpoint_start": 25, # will be used for type 3
    # "setpoint_end": 50 # will be used for type 3cd
}

safety = {
    "min_alt": 5,
    "max_interval_between_pings" : 5
}
