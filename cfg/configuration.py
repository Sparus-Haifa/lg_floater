from enum import Enum

class State(Enum):
    INIT = 0
    WAIT_FOR_SAFETY = 1
    WAIT_FOR_WATER = 2
    EXEC_TASK = 3
    END_TASK = 4
    WAIT_FOR_PICKUP = 5
    EMERGENCY = 6
    STOP = 7


app = {
    "simulation" : True,
    "simulation_udp_port" : 12000,
    # "host_ip" : "127.0.0.1",
    "host_ip" : "192.168.1.75",

    "disable_safety" : True,
    "test_mode" : True,
    "test_mode_udp_port" : 5000
}

# Current_state = State.INIT

serial = {
    # /dev/ttyUSB0
    # "port": "/dev/ttyACM0",
    "port": "COM4",
    "timeout" : 3,
    "baud_rate": 115200
}

serial_safety = {
    # /dev/ttyUSB0
    # "port": "/dev/ttyACM0",
    # "port": "COM4",
    "port": "COM4",
    "timeout" : 3,
    "baud_rate": 115200
}

pressure = {
    "epsilon": 0.05,
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
    "seafloor_depth" : 80  # meters
}