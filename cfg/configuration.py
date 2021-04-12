from enum import Enum

class State(Enum):
    INIT = 1
    WAIT_FOR_WATER = 2
    EXEC_TASK = 3
    END_TASK = 4
    EMERGENCY = 5

Current_state = State.INIT

serial = {
    "port": "COM3",
    "baud_rate": 9600
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
    "setpoint_start": 25, # will be used for type 3
    "setpoint_end": 50 # will be used for type 3
}

safety = {}
