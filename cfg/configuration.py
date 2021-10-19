from enum import Enum, auto

class State(Enum):
    INIT = auto()
    WAIT_FOR_SENSOR_BUFFER = auto()  # TODO: add timeout/minimun sensors
    WAIT_FOR_SAFETY = auto()
    INFLATE_BLADDER = auto()
    # ACQUIRE_CLOCK = auto()
    CALIBRATE_DEPTH_SENSORS = auto()
    WAIT_FOR_WATER = auto()
    EXEC_TASK = auto()
    END_TASK = auto()
    SLEEP_SAFETY = auto()
    WAIT_FOR_PICKUP = auto()
    EMERGENCY = auto()
    STOP = auto()

class MissionState(Enum):
    EN_ROUTE = auto()
    HOLD_ON_TARGET = auto()
    SURFACE = auto()
    MISSION_ABORT = auto()
    ASCENDING = auto()
    DESCENDING = auto()

app = {
    "simulation" : True,  # app sends debug data to sim, udp - not serial
    "simulation_udp_port" : 12000,
    # "host_ip" : "127.0.0.1",
    "host_ip" : "192.168.1.75",

    "disable_safety" : True,
    "test_mode" : False,
    "test_mode_udp_port" : 5000,
    "disable_altimeter" : True,
    "skip_arduino_compile" : True
}

# Current_state = State.INIT

serial = {
    # /dev/ttyUSB0
    "port": "/dev/ttyACM0",
    # "port": "COM4",
    "timeout" : 3,
    "baud_rate": 115200
}

serial_safety = {
    # /dev/ttyUSB0
    # "port": "/dev/ttyACM0",
    # "port": "COM4",
    "port": "/dev/ttyUSB0",
    # "port": "COM4",
    "timeout" : 3,
    "baud_rate": 115200
}

pressure = {
    "epsilon": 0.5,
    "avg_samples": 5,
    "precision" : 2
}

temperature = {
    "avg_samples": 5,
    "precision" : 2
}

imu = {
    "avg_samples": 5,
    "precision" : 2
}

bladder = {
    "avg_samples": 1,
    "precision" : 2
}

altimeter = {
    "avg_samples": 1,
    "precision" : 2
}

rpm = {
    "avg_samples": 1,
    "precision" : 2
}

task_single = {

}

task_double = {
    
}

task_emergency = {
    
}

task = {
    # "type": 1, # 1- pressure, 2-density, 3-profiling
    # "duration": 300, # seconds
    # "setpoint": 300, # will be used for types 1 & 2
    # "setpoint_tollerance": 5, #asumming we won't hit the exact setpoint - +/1 setpoint_tollerance is good enough
    # "fullduty_exec_time": 5, #num of seconds to operate the pump while in full-duty cycle mode
    # "fullduty_min_distance": 100,
    # "max_interval_between_movements": 100,
    # "min_interval_between_movements": 5



    # "setpoint_start": 25, # will be used for type 3
    # "setpoint_end": 50 # will be used for type 3cd
    
    "target_depth_in_meters" : 50,
    
    "min_time_off_duration_limit" : 0.5,
    "target_depth" : 30.0  # millibar
    # "max_time_off_duration" : 100.0

}

pickup = {
    "wait_for_water_duration" : 10
}

safety = {
    # "min_alt": 5,
    # "max_interval_between_pings" : 5
    "timeout" : 30  # In seconds
}

simulation = {
    "seafloor_depth" : 80  # meters. should be set to 250 decibar
}