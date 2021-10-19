from lib.pid_ctrl import PID
from lib.rpm import RPM
from lib.flag import Flag
from lib.altimeter import Altimeter
from lib.bladder_volume import Bladder
import time
import cfg.configuration as cfg
# from cfg import Mode
# import lib.logger as logger
import lib.comm_serial as ser
import lib.comm_udp as com
# import lib.comm_tcp as com

from lib.press_ctrl import *
from lib.temp_ctrl import *
from lib.imu_ctrl import *
from lib.safety_ctrl import *
from lib.fyi_ctrl import *
from lib.profile import *
from lib.task_ctrl import *

from enum import Enum

import sys # for args, and log out

# import logging
from lib.logger import Logger

import os  # for log file path

from cfg.configuration import State, MissionState

from gpio_controller import GPIOController

from burner import ArduinoBurner

# logging.basicConfig(filename='log\\example.log', level=0, format='%(asctime)s : %(levelname)s : %(message)s')
# logging.basicConfig(level=0)

# task
MIN_TIME_OFF_DURATION = cfg.task["min_time_off_duration_limit"]
# MAX_TIME_OFF_DURATION = cfg.task["max_time_off_duration"]
TARGET_DEPTH_IN_METERS = cfg.task["target_depth_in_meters"]

# safety
SAFETY_TIMEOUT = cfg.safety["timeout"]



class Controller():
    def __init__(self, log):

        self.simulation = cfg.app["simulation"]
        self.disable_safety = cfg.app["disable_safety"]
        self.test_mode = cfg.app["test_mode"]
        self.disable_altimeter = cfg.app["disable_altimeter"]
        self.skip_arduino_compile = cfg.app['skip_arduino_compile']
        
        if self.test_mode or self.disable_safety or self.disable_altimeter:
            self.test_mode = True

        self.log = log        
    

        if self.simulation:
            self.log.warning("Simulation mode")

        if self.disable_safety:
            self.log.warning("Safety is disabled")

        if self.test_mode:
            self.log.warning("Test mode")
            self.test_command = None
            self.test_value = None
            self.current_state = State.STOP
        else:
            self.current_state = State.INIT

        self.current_mission_state = None

        self.target_depth = cfg.task["target_depth"]
        self.current_depth = None

        self.lastTime = time.time()  # global timer
        self.mission_timer = None  # timer for main mission to stop and end mission

        # Iridium
        self.iridium_command_was_sent = False

        # Nano
        self.sent_sleep_to_nano = False
        self.waiting_for_nano_sleep = False
        self.wake_up_sent_to_nano = False
        self.is_safety_responding = False
        self.weightDropped = False
        self.drop_weight_command_sent = False
        self.safteyTimer = None
        self.safety_watchdog_is_enabled = False  # when we start timing safety
        self.sleep_sent_to_nano = False
        self.nano_is_sleeping = True
        # safety = Safety(cfg.safety["min_alt"], cfg.safety["max_interval_between_pings"], log)


        # PID
        self.pid_controller = PID(self.log)
        # self.lastP=0 # TODO: move to pid module
        self.pid_sent_time = None
        # self.pid_sent




        self.surface_command_sent = False
        # self.idle = True  # dutycycle is off: init state, bladder already at max or min state etc.

        # Bladder status
        self.bladder_is_at_min_volume = False
        self.bladder_is_at_max_volume = False

        self.depth_sensors_are_calibrated = None

        WAIT_FOR_WATER_DURATION = cfg.pickup["wait_for_water_duration"]
        self.waterSenseDuration =  WAIT_FOR_WATER_DURATION  #  5 # sould be 5 min = 60*5 [sec]
        self.waterTestTimer = None


        # Task execusion timers
        self.time_off_duration = None
        self.time_on_duration = None
        # self.dcTimer = None
        self.time_off_timer = None
        
        self.error = None


        # setup GPIO
        RPI_TRIGGER_PIN = 14
        self.safety_trigger = GPIOController(RPI_TRIGGER_PIN)
        self.safety_trigger.high()

        self.simFactor = 1.0

        

        self.setupSensors()
        self.addSensorsToDict()
        self.addFlagsToDict()
        self.setupComms()


        self.profile = Profile("cfg/profile.txt", self.log)
        # self.task_ctrl = Task(sensPress, log)

    def setupComms(self):
        # Main arduino
        if not self.simulation:
            self.comm = ser.SerialComm("MEGA", cfg.serial["port"], cfg.serial["baud_rate"], cfg.serial["timeout"], self.log)
            if not self.comm.ser:
                self.log.critical("-E- Failed to init serial port")
                exit()
        else:
        # Simulated via udp
            self.comm = com.UdpComm(cfg.app["simulation_udp_port"])
            if not self.comm.server_socket:
                self.log.critical("-E- Failed to init udp port")
                exit() 

        # Secondary arduino (safety)
        if self.disable_safety:
            # self.log.warning("")
            pass
        else:
            self.comm_safety = ser.SerialComm("NANO", cfg.serial_safety["port"], cfg.serial_safety["baud_rate"], cfg.serial_safety["timeout"], self.log)
            if not self.comm_safety.ser:
                self.log.critical("-E- Failed to init safety serial port")
                exit()

        # Test mode
        if self.test_mode:
            self.comm_cli = com.UdpComm(cfg.app["test_mode_udp_port"])
            if not self.comm_cli.server_socket:
                self.log.critical("-E- Failed to init cli udp port")
                exit()    

    def setupSensors(self):
        self.sensors = {}
        self.flags = {}

        # Pressure
        self.pressureController = Press_ctrl(cfg.pressure["avg_samples"], cfg.pressure["precision"], cfg.pressure["epsilon"], self.log)
        self.pressureController.addSensor("BP1")
        self.pressureController.addSensor("BP2")
        self.pressureController.addSensor("TP1")
        self.pressureController.addSensor("TP2")
        self.pressureController.addSensor("HP")
        self.pressureController.addSensor("AP")
        self.pressureSensors = self.pressureController.getSensors()

        # Temperature
        self.temperatureController = Temp_ctrl(cfg.temperature["avg_samples"], cfg.temperature["precision"], self.log)
        self.temperatureController.addSensor("BT1")
        self.temperatureController.addSensor("BT2")
        self.temperatureController.addSensor("TT1")
        self.temperatureController.addSensor("TT2")
        self.temperatureController.addSensor("AT")
        self.temperatureSensors = self.temperatureController.getSensors()

        # IMU
        self.IMUController = IMU_ctrl(cfg.imu["avg_samples"], cfg.imu["precision"], self.log)
        self.IMUController.addSensor("X")
        self.IMUController.addSensor("Y")
        self.IMUController.addSensor("Z")
        self.IMUSensors = self.IMUController.getSensors()
        
        # Other sensors
        self.bladderVolume = Bladder("Bladder Volume", cfg.bladder["avg_samples"], cfg.bladder["precision"], self.log)
        self.altimeter = Altimeter("Altimeter", cfg.altimeter["avg_samples"], cfg.altimeter["precision"], self.log)
        self.rpm = RPM("RPM", cfg.rpm["avg_samples"], cfg.rpm["precision"], self.log)


        # Flags
        self.pumpFlag = Flag("Pump",self.log)  # PF
        self.bladder_flag = Flag("Bladder", self.log)  # BF
        self.leak_h_flag = Flag("Hull leak", self.log)  # HL
        self.leak_e_flag = Flag("Engine leak", self.log)  # EL
        self.full_surface_flag = Flag("Full surface initiated", self.log)       

    def addSensorsToDict(self):
        for sensor in self.temperatureSensors:
            self.sensors[sensor]=self.temperatureSensors[sensor]
        for sensor in self.pressureSensors:
            self.sensors[sensor]=self.pressureSensors[sensor]
        for sensor in self.IMUSensors:
            self.sensors[sensor]=self.IMUSensors[sensor]

        self.sensors["PD"]=self.altimeter
        self.sensors["PC"]=self.altimeter
        self.sensors["BV"]=self.bladderVolume
        self.sensors["rpm"]=self.rpm
    

    def addFlagsToDict(self):
        self.flags["PF"]=self.pumpFlag
        self.flags["HL"]=self.leak_h_flag
        self.flags["EL"]=self.leak_e_flag
        self.flags["BF"]=self.bladder_flag
        self.flags["FS"]=self.full_surface_flag

    def clean(self):
        self.safety_trigger.clean()

    def get_cli_command(self):
        # print("getting cli")
        line = self.comm_cli.read()
        if line is None or line == '' or line == b'':
            return
        line = line.decode('utf-8','ignore').strip().split(':')

        self.log.debug(f"CLI:{line}")

        header, value = line
        # if header == "stop":
        #     print("stop")
        self.test_command = header
        self.test_value = value


    #get line from main arduino; decode it, store the data and execute an appropriate callback
    def get_next_serial_line(self):
        serial_line = self.comm.read() # e.g. data=['P1', '1.23']
        if serial_line == None:
            # print(f"Waiting for message from arduino. Received: {serial_line}")
            return
        # for c in ["V","D","T"]:
        #     if str(serial_line).startswith(c):
        #         self.log.debug("raw: {}".format(serial_line))
        if serial_line!=b"":
            self.log.debug("mega>rpi: {}".format(serial_line))
        serial_line = serial_line.decode('utf-8', 'ignore').strip().split(":")
        header = serial_line[0]
        if len(serial_line)<2:
            return #no Value, break
        value = serial_line[1]


        def handle_mega_message(header, value):
            if header=="TT1":
                self.temperatureSensors["TT1"].add_sample(value)
            elif header=="TT2":
                self.temperatureSensors["TT2"].add_sample(value)
            elif header=="BT1":
                self.temperatureSensors["BT1"].add_sample(value)
            elif header=="BT2":
                self.temperatureSensors["BT2"].add_sample(value)
            elif header=="AT":
                self.temperatureSensors["AT"].add_sample(value)
            elif header=="BP1":
                self.pressureSensors["BP1"].add_sample(value)
            elif header=="BP2":
                self.pressureSensors["BP2"].add_sample(value)
            elif header=="TP1":
                self.pressureSensors["TP1"].add_sample(value)
            elif header=="TP2":
                self.pressureSensors["TP2"].add_sample(value)
            elif header=="HP":
                self.pressureSensors["HP"].add_sample(value)
            elif header=="AP":
                self.pressureSensors["AP"].add_sample(value)
            elif header=="X":
                self.IMUSensors["X"].add_sample(value)
            elif header=="Y":
                self.IMUSensors["Y"].add_sample(value)
            elif header=="Z":
                self.IMUSensors["Z"].add_sample(value)
            elif header=="HL":
                self.leak_h_flag.add_sample(value) # trigger
                self.handle_HL()
            elif header=="EL":
                self.leak_e_flag.add_sample(value) # trigger
                self.handle_EL()
            elif header=="BF":
                self.bladder_flag.add_sample(value)
                self.handle_BF()
            elif header=="PD":
                self.altimeter.add_sample(value) # trigger
                self.handle_PD()
            elif header=="PC":
                self.altimeter.add_confidance(value) 
            elif header=="PU":
                self.pumpFlag.add_sample(value)
            elif header=="RPM":
                self.rpm.add_sample(value) 
            elif header=="PF":
                lastValue = self.pumpFlag.getLast() # trigger
                self.pumpFlag.add_sample(value)
                self.handle_PF(lastValue)
            elif header=="BV":
                self.bladderVolume.add_sample(value) # trigger
                self.handle_BV()
            elif header=="SF":
                self.full_surface_flag.add_sample(value)
                self.handle_SF()

        handle_mega_message(header, value)

        # time.sleep(0.01)

    def handle_SF(self):
        # send S:1
        pass

    def handle_BF(self):
        value = self.bladder_flag.getLast()
        if value == 0:
            self.bladder_is_at_max_volume = False
            self.bladder_is_at_min_volume = False
        elif value == 1:  # Bladder at min.
            self.bladder_is_at_min_volume = True
        elif value == 2:
            self.bladder_is_at_max_volume = True


    def handle_HL(self):
        value = self.leak_h_flag.getLast()
        if value == 1:
            self.current_state = State.EMERGENCY

    def handle_EL(self):
        value = self.leak_e_flag.getLast()
        if value==1:
            self.current_state = State.EMERGENCY

    # Start emergency ascending with bladder first
    def surface(self):
        if self.surface_command_sent:
            self.log.debug("waiting for surface command")
        else:
            self.log.info("sending surface command")
            if not self.disable_safety:
                self.comm_safety.write("S:1")

    # sending the command to drop the dropweight to saftey
    def drop_weight(self):
        if self.drop_weight_command_sent:
            self.log.debug("waiting for weight to drop")
        else:
            self.log.info("dropping weight")
            if not self.disable_safety:
                self.comm_safety.write("N:2")
            self.drop_weight_command_sent = True



    def handle_PD(self):
        # TODO: decide which comes first from arduino
        # assuming PC comes first
        if cfg.app["disable_altimeter"]:
            return
        value = self.altimeter.getLast()
        confidance = self.altimeter.getConfidance()
        if confidance > 50:
            if 10 < value and value <= 20:
                self.log.warning("Yellow line! Ending mission!")
                # Alert
                # self.surface()
                self.current_state = State.END_TASK
            elif value <= 10:
                self.log.critical("Red line! Aborting mission!")
                # self.drop_weight()
                self.current_state = State.EMERGENCY


    def handle_PF(self, lastValue):
        value = self.pumpFlag.getLast()
        if value==0:
            # pump is off:
            # 1. pump init
            # 2. pump cut on time
            # 3. pump cut before time
            if lastValue and lastValue != value:
                self.log.info("Pump turned off. Starting timeOff timer.")
                self.time_on_duration = None
                self.time_off_timer = time.time()
            # if self.time_on_duration and  self.time_on_duration>0 and (time.time() - self.dcTimer)*self.simFactor < self.time_on_duration and self.bladderVolume:
            #     print("Waiting on pump to start")
            #     exit()
            #     self.dcTimer = time.time()
            # print("pump is off")
            # self.pumpFlag.add_sample(0)
            pass
        elif value==1:
            self.log.info("pump turned on")
            # self.pumpFlag.add_sample(1)
            pass
        elif value==2:
            # print("pump not working")
            # self.pumpFlag.add_sample(2)
            # leak
            self.current_state = State.EMERGENCY
            self.log.critical("PUMP FAILIURE")
            self.time_on_duration = None

            # self.comm_safety.write("N:2")
            # self.drop_weight()
        else:
            self.log.error("PF value error",value)
            # assert()


    def handle_BV(self):
         # send pid
        if self.simulation:
            self.comm.write(f"State:{self.current_state}\n")  # debug send state

        if self.test_mode:
            self.run_test_sequence()
        else:
            self.run_mission_sequence()
        


    def run_test_sequence(self):
        print("running test")
        # self.logSensors()
        if self.test_command is not None:
            command = self.test_command
            value = self.test_value
            # self.test_command = None
            # self.test_value = None

            if command == "restart":
                self.log.warning("restarting")
                self.current_state = State.INIT
                
                def reset():
                    for sensor in self.sensors:
                        self.sensors[sensor].reset()
                    for flag in self.flags:
                        self.flags[flag].reset()
                
                reset()
                self.test_command = None

            if command == "stop":
                self.current_state = State.STOP
                self.log.warning("stopping")

            if command == "depth":
                self.log.debug(f"setting setpoint to {value}")
                self.target_depth = float(value)
                self.pid_controller.reset_d()
                self.test_command = None


            if command == "water":
                self.log.debug("water test")
                if self.current_state == State.EXEC_TASK:
                    self.current_state = State.STOP
                    self.test_command = None

                else:
                    self.current_state = State.WAIT_FOR_WATER
                    # self.test_command = "water"

            if command == "exec_task":
                self.log.debug('exec_task')
                if self.current_state == State.STOP:
                    self.log.debug('switching state to WAIT_FOR_SAFETY')
                    self.current_state = State.EXEC_TASK
                elif self.current_state == State.EXEC_TASK:
                    self.log.debug('testing: EXEC_TASK')
                elif self.current_state != State.EXEC_TASK:
                    self.log.debug('switching state back to STOP')
                    self.current_state = State.STOP
                    self.test_command = None

            if command == "pickup":
                pass
                # self.log.debug("wait for pickup")
                # self.current_state = State.WAIT_FOR_PICKUP

            if command == "sink_wait_climb":
                self.log.debug("sink_wait_climb")
                # TODO

            if command == 'wakeup_safety':
                self.log.debug('wakeup_safety')
                if self.current_state == State.STOP:
                    self.log.debug('switching state to WAIT_FOR_SAFETY')
                    self.current_state = State.WAIT_FOR_SAFETY
                elif self.current_state == State.WAIT_FOR_SAFETY:
                    self.log.debug('test command wait for safety')
                elif self.current_state != State.WAIT_FOR_SAFETY:
                    self.log.debug('switching state back to STOP')
                    self.current_state = State.STOP
                    self.test_command = None
                # else:
                #     self.current_state = State.WAIT_FOR_SAFETY

            if command == 'sleep_safety':
                self.log.debug('sleep_safety')
                if self.current_state == State.STOP:
                    self.log.debug('switching state to SLEEP_SAFETY')
                    self.current_state = State.SLEEP_SAFETY

                elif self.current_state != State.SLEEP_SAFETY:
                    self.current_state = State.STOP
                    self.test_command = None


                    
                
        self.run_mission_sequence()
        pass

    def sleep_safety(self):
        # safety logic
        safety_is_enabled = not self.disable_safety

        if safety_is_enabled and not self.sent_sleep_to_nano and (not self.weightDropped and not self.drop_weight_command_sent):
            self.log.debug('inside 1')
            if not self.waiting_for_nano_sleep:
                self.log.debug('inside 2')
                self.sent_sleep_to_nano = True
                self.waiting_for_nano_sleep = True
                self.send_sleep_to_nano()
        if self.waiting_for_nano_sleep:
            self.log.info('waiting_for_nano_sleep')

    def handle_mission_state(self):
        # mission timer
        # if self.mission_timer is None:
        #     self.log.info('Mission countdown started')
        #     self.mission_timer = time.time()
        # elif time.time() - self.mission_timer > 60:
        #     self.log.info('Timeout: ending mission')
        #     self.current_state = State.END_TASK

        # Before starting a dutycycle.
        if self.time_off_duration is None: 
            # before DC starts
            self.log.info("attemting to start a new dutycycle")
            self.sendPID()
        # after
        elif self.time_on_duration is None:
            self.update_depth()
            elapsedSeconds = (time.time() - self.time_off_timer)*self.simFactor
            self.log.info(f"waiting for timeOff to finish {round(elapsedSeconds,2)} of {self.time_off_duration}")
            if elapsedSeconds > self.time_off_duration:
                self.log.info("timeOff is over")
                self.time_off_duration = None
                self.time_off_timer = None
        else:
            # TODO: add watchdog incarse PF doesn't get recived
            self.update_depth()
            pump_flag = self.pumpFlag.getLast()
            # print('PF', pump_flag)
            if pump_flag == 0:
                self.log.info("waiting for pump to start")
            else:
                self.log.info("pump is running...")
    
    def run_mission_sequence(self):
        self.log.info(self.current_state)
        self.logSensors()

        # INIT
        if self.current_state == State.INIT:
            self.current_state = State.WAIT_FOR_SAFETY

        # WAIT FOR SAFETY
        elif self.current_state == State.WAIT_FOR_SAFETY:
            if self.disable_safety:
                self.log.warning('safety is disabled: skipping safety test')
                self.current_state = State.WAIT_FOR_SENSOR_BUFFER
            self.safety_watchdog_is_enabled = True
            if self.is_safety_responding:
                self.log.info('safety is awake and pinging')
                # reset state vars
                self.wake_up_sent_to_nano = False  # ressting nano state
                self.nano_is_sleeping = False  # ressting nano state
                self.wake_up_sent_to_nano = False  # ressting nano state
                self.waiting_for_nano_sleep = False  # ressting nano state
                self.sent_sleep_to_nano = False  # ressting nano state
                self.current_state = State.WAIT_FOR_SENSOR_BUFFER
            else:
                if self.nano_is_sleeping:
                    self.log.info("waiting for safety to respond")
                else:
                    self.log.info('waiting for safety to ping')
                if not self.wake_up_sent_to_nano:
                    self.wake_up_nano()

        # WAIT_FOR_SENSOR_BUFFER
        elif self.current_state == State.WAIT_FOR_SENSOR_BUFFER:
            if self.sensorsReady():
                self.current_state = State.INFLATE_BLADDER

        # INFLATE_BLADDER  # TODO: add to exception/watchdog
        elif self.current_state == State.INFLATE_BLADDER:
            if self.bladder_is_at_max_volume:
                self.current_state = State.CALIBRATE_DEPTH_SENSORS
                return
            # self.pid_controller.p=
            self.pid_controller.d=0
            self.target_depth = -100
            self.handle_mission_state()
            

        # ACQUIRE_CLOCK


        # CALIBRATE_DEPTH_SENSORS
        elif self.current_state == State.CALIBRATE_DEPTH_SENSORS:
            if self.depth_sensors_are_calibrated:
                self.current_state = State.WAIT_FOR_WATER
                self.update_depth()
                return
            self.depth_sensors_are_calibrated = self.pressureController.calibrate()



                
        # WAIT FOR WATER
        elif self.current_state == State.WAIT_FOR_WATER:
            if not self.waterTestTimer:
                self.log.info("Waiting for water")
                self.waterTestTimer = time.time()
            elapsedSeconds = (time.time() - self.waterTestTimer)*self.simFactor
            limitSeconds = self.waterSenseDuration
            if  elapsedSeconds > limitSeconds:
                self.log.info("Done waiting for water")
                if self.pressureController.senseWater():
                    self.current_state = State.EXEC_TASK
                    self.waterTestTimer = None
                else:
                    self.log.info("water not detected")
                    self.waterTestTimer = time.time()
            else:
                self.log.info("Waiting for water")
                self.log.info(f"{round(elapsedSeconds)}/{limitSeconds} secs")






        # EXECUTE TASK
        elif self.current_state == State.EXEC_TASK:
            self.handle_mission_state()
                

        # END TASK
        elif self.current_state == State.END_TASK:
            self.log.info("Ending task")
            full_surface = self.full_surface_flag.getLast()

            if full_surface is not None:
                self.surface()
            else:
                self.log.info("Surfacing")

            if self.pressureController.senseAir():
                self.log.info("we've reached the surface!")
                self.current_state = State.WAIT_FOR_PICKUP

        # Wait for safety to sleep
        elif self.current_state == State.SLEEP_SAFETY:
            self.log.info("waiting for safety to sleep")
            self.sleep_safety()

            # let nano sleep (if pressure is)
            # keep wake-up option in case

            # send iradium flag (I:1)
            
            # if not self.disable_safety and not self.sleep_sent_to_nano and (not self.weightDropped and not self.drop_weight_command_sent):
            #     self.send_sleep_to_nano()
            
            if self.nano_is_sleeping:
                self.log.debug("nano is sleeping")
                self.is_safety_responding = False  # resetting nano state
                # self.wake_up_sent_to_nano = False  # ressting nano state
                self.waiting_for_nano_sleep = False  # ressting nano state
                self.sent_sleep_to_nano = False  # ressting nano state
                self.current_state = State.WAIT_FOR_PICKUP

        # Wait for pickup - Iradium
        elif self.current_state == State.WAIT_FOR_PICKUP:
            self.log.info("waiting for pickup")


            if not self.iridium_command_was_sent:
                self.log.info("Sending command to iridium")
                self.iridium_command_was_sent = True
                self.comm.write(f"I:1") 

            else:
                self.log.debug('iridium_command_was_sent')
                


        # EMERGENCY
        elif self.current_state == State.EMERGENCY:
            self.log.warning("Emergency")
            if not self.weightDropped:
            #     # self.comm_safety.write("N:2") # sending the command to drop the dropweight to saftey
                self.drop_weight()
            if self.pressureController.senseAir():
                self.log.info("we've reached the surface!")
                self.current_state = State.WAIT_FOR_PICKUP

            pump_flag = self.pumpFlag.getLast()
            voltage = 100
            direction = 2
            timeon = 5.0
            # if pump_flag == 0:
            self.target_depth = 0
            self.handle_mission_state()

        # STOP - TEST MODE
        elif self.current_state == State.STOP:
            self.log.warning("Stopped")
        else:
            self.log.error('unknown state')


    def wake_up_nano(self):
        self.safety_trigger.low()
        time.sleep(0.1)
        # controller.clean()
        self.wake_up_sent_to_nano = True


    def send_sleep_to_nano(self):
        # self.sleep_sent_to_nano = True
        self.comm_safety.write("N:5")

    # def sleep_nano(self):
        # if not self.disable_safety:
            # self.comm_safety.write("N:5")

    def sensorsReady(self):
        bypassSens = ["rpm"]
        for sensor in self.sensors:
            if sensor not in bypassSens and not self.sensors[sensor].isBufferFull(): # TODO: fix rpm and [and sensor!="PF"]
                self.log.warning(f"sensor {sensor} is not ready")
                return False
        bypassFlag = ["PF", "FS"]
        for flag in self.flags:
            if flag not in bypassFlag and not self.flags[flag].isBufferFull():
                self.log.warning(f"flag {flag} is not ready")
                return False

        return True
    

    def logSensors(self):
        res = {}

        for key in self.temperatureSensors:
            value = self.temperatureSensors[key].getLast()
            # print(f"{key} {value}")
            res[key]=value   

        for key in self.IMUSensors:
            value = self.IMUSensors[key].getLast()
            # print(f"{key} {value}")
            res[key]=value

        for key in self.pressureSensors:
            value = self.pressureSensors[key].getLast()
            # print(f"{key} {value}")
            res[key]=value

        res["PD"]=self.altimeter.getLast()
        res["PC"]=self.altimeter.getConfidance()
        res["HL"]=self.leak_h_flag.getLast()
        res["EL"]=self.leak_e_flag.getLast()
        res["BF"]=self.bladder_flag.getLast()
        res["SF"]=self.full_surface_flag.getLast()
        res["PF"]=self.pumpFlag.getLast()
        res["BV"]=self.bladderVolume.getLast()
        res["rpm"]=self.rpm.getLast()
        res["State"]=self.current_state.name
        res['MissionState']=self.current_mission_state.name
        res['Setpoint']=self.target_depth
        res['Error']=self.error
        res['Depth']=self.current_depth

        # timeOn display
        pump_flag = self.pumpFlag.getLast()
        if self.time_on_duration is not None and pump_flag == 1:
            del res
            res = {}
            res["BV"]=self.bladderVolume.getLast()
            res["rpm"]=self.rpm.getLast()




        headers = []
        for key in res:
            value = res[key]

            #shorten floats
            check_float = isinstance(value, float)
            if check_float:
                value = "{:.2f}".format(value)

            end = len(str(value)) + 1 - len(key)
            if len(key)>len(str(value)):
                end=1

            line = f"{key}"
            full_line = line + " "*end
            # print(line ,end=" "*end)
            headers.append(full_line)
        # print()
        self.log.info("".join(headers))

        values = []
        for key in res:
            end = 1
            # res = len(str(res[key])) + 3 - len(key)
            # if len(str(res[key])) > res:
            #     end = res
            value = res[key]

            #shorten floats
            check_float = isinstance(value, float)
            if check_float:
                value = "{:.2f}".format(value)

            if len(key)>len(str(value)):
                end=len(key) + 1 - len(str(value))
            

            line = f"{value}"
            full_line = line + " "*end
            # print(line, end=" "*end)
            values.append(full_line)
        # print()
        self.log.info("".join(values))
        # BT1   BT2   TT1   TT2   AT AP X    Y     Z    BP1     BP2     TP1     TP2     HP PD       PC   H1   H2   pump rpm
        # 23.66 23.14 23.29 23.34 0  0  0.01 -0.00 0.00 1031.60 1035.30 1022.40 1034.00 0 -26607.00 9.00 0.00 0.00 None 0

        # BT1   BT2   TT1   TT2   X    Y    Z   BP1    BP2    TP1    TP2    HP  PD          PC  H1 H2 pump BV       rpm  PF State      
        # 23.66 23.14 23.29 23.34 0.01 -0.0 0.0 1031.6 1035.3 1022.4 1034.0 0.0 -26607.0000 9.0 0  0  0    650.0000 None 0  State.INIT
        if self.weightDropped:
            self.log.warning("weight dropped!")


    def update_depth(self):
        avg = self.pressureController.get_depth()
        self.current_depth = avg  # update current depth
        self.error = self.target_depth - self.current_depth

    def sendPID(self):
        self.log.debug("calculating PID")


        # avg = self.pressureController.getAvgDepthSensorsRead()
        # self.update_depth()
        avg = self.pressureController.get_depth()
        self.current_depth = avg  # update current depth
        
        if not avg:
            self.log.error("ERROR: Could not calculate depth - not enough working sensors")
            return

        # def getTargetDepth(target_depth_in_meters):
        #     p0 = 10.35 # TODO: get pressure at sea level
        #     m = 1 # TODO: get linear function of sensors
        #     corrected = p0 + m*target_depth_in_meters # linear function
        #     target_depth = corrected * 100 # in milibar
        #     return target_depth

        # target_depth_in_meters = TARGET_DEPTH_IN_METERS
        # target_depth = getTargetDepth(target_depth_in_meters)
        target_depth = self.target_depth
    

        # PID
        error = target_depth - avg
        self.error = error
        self.log.debug('error = target_depth - avg')
        self.log.debug(f'{error} = {target_depth} - {avg}')
        # print("Error",error, "target", target_depth, "avg", avg)
        scalar = self.pid_controller.pid(error)
        direction, voltage, dc, self.time_on_duration, self.time_off_duration = self.pid_controller.unpack(scalar, error)  # this is the line.

        if self.time_off_duration < MIN_TIME_OFF_DURATION:
            self.time_off_duration = MIN_TIME_OFF_DURATION

        # if self.time_off_duration > MAX_TIME_OFF_DURATION:
        #     self.time_off_duration = MAX_TIME_OFF_DURATION

        phase = 1

        if self.simulation:
            self.comm.write(f"error:{error}\n")
            self.comm.write(f"p:{self.pid_controller.p}\n")
            self.comm.write(f"kp:{self.pid_controller.kp}\n")
            self.comm.write(f"d:{self.pid_controller.d}\n")
            self.comm.write(f"kd:{self.pid_controller.kd}\n")
            self.comm.write(f"target:{target_depth}\n")
            self.comm.write(f"phase:{phase}\n") # sim debug
            self.comm.write(f"PID:{scalar}\n") # sim debug
            self.comm.write(f"O:{self.time_off_duration}\n") # sim debug
            self.comm.write(f"dc:{dc}\n")

        
        # bv = self.sensors["BV"].getLast()
        # buffer = 15
        # maxDive =  bv<200.0 + buffer and direction == 1
        # maxAscend = bv>450.0 - buffer and direction == 2

        if self.bladder_is_at_max_volume and direction == 2:
            self.log.info("Bladder is at max volume")
            # self.idle = True
            self.time_on_duration = None
            self.time_off_duration = None
            self.time_off_timer = None
            
        elif self.bladder_is_at_min_volume and direction == 1:
            self.log.info("Bladder is at min volume")
            # self.idle = True
            self.time_on_duration = None
            self.time_off_duration = None
            self.time_off_timer = None
        else:
            self.log.info(f"sending PID - Voltage:{voltage}    direction:{direction}    timeOn:{self.time_on_duration}  timeOff:{self.time_off_duration}")
                
            if voltage == 0:
                self.time_on_duration = self.time_off_duration = None
                return            
            self.comm.write(f"V:{voltage}\n")
            self.comm.write(f"D:{direction}\n")
            self.comm.write(f"T:{self.time_on_duration}\n")


    #get line from secondary arduino;
    def get_next_serial_line_safety(self):
        # self.comm_safety.write("N:11")
        serial_line = self.comm_safety.read()  # e.g. data=['P1', '1.23']
        serial_line = serial_line.strip().decode('utf-8', 'ignore').split(":")
        
        if len(serial_line) < 2: # skip if no message
            # print("Waiting for message from safety. Received: None")
            return
        
        self.log.debug("nano>rpi: {}".format(serial_line))

        if not self.safety_watchdog_is_enabled:
            return
        
        # send "I'm alive message"
        if self.weightDropped or self.nano_is_sleeping:
            # return
            self.safteyTimer = time.time()
            # self.safteyTimer = None


        # timer if no ping from safety inflate bladder
        if not self.safteyTimer:
            self.safteyTimer = time.time()

        timeout = time.time() - self.safteyTimer > SAFETY_TIMEOUT
        if timeout:
            self.log.critical("safety not responding!")
            self.is_safety_responding = False
            # TODO: move to emergency state only if you're in exec or...
            self.current_state = State.EMERGENCY # will make weight drop on reconnection



        header = serial_line[0]
        value = None
        try:
            value = int(float(serial_line[1]))
        except ValueError as e:
            self.log.error(f"Error parsing value {serial_line[1]} from safety")
            return

        if serial_line[0].upper().startswith("N"):
            # print("adding {}".format(serial_line))
            # self.safety.add_sample(serial_line)
            # safety_callback()
            if value==1:
                # if self.current_state == State.EMERGENCY:
                #     self.comm_safety.write("N:2") # sending the command to drop the dropweight to saftey
                self.safteyTimer = time.time()
                # print("pong!")
                self.log.info("pong recieved by safety")
                self.is_safety_responding = True
                pass # ping acknowledge
            if value==2:
                # print("safety weight dropped on command acknowledge")
                self.log.info("safety acknowledges weight was dropped on command ")
                self.current_state = State.EMERGENCY                
                self.weightDropped = True
                self.comm.write("weight:1")
                pass # drop weight acknowledge
            if value==3: # Saftey requests a ping
                # print("ping!")
                self.log.info("ping sent from safety")
                self.comm_safety.write("N:1") # sending ping to saftey
            if value==4:
                # print("weight dropped due to over time acknowledge")
                self.log.info("safety acknowledges weight was dropped due to over time")
                self.current_state = State.EMERGENCY
                self.weightDropped = True
                self.comm.write("weight:1")
                pass # weight dropped due to over time

            if value==5:
                self.log.info("safety went to sleep")
                self.nano_is_sleeping = True
                self.safety_watchdog_is_enabled = False
                self.safetyTimer = None

            if value==111:
                self.log.info('safety sleep was interrupted')
                self.nano_is_sleeping = False
                if self.wake_up_sent_to_nano:
                    self.comm_safety.write('L:1')
                    self.log.info('waking safety up')
                time.sleep(0.1)
                self.safety_trigger.high()  # reset pin
            



MARGIN = 3.0

class Pilot:
    def __init__(self, log, controller) -> None:
        self.controller = controller
        self.depth = None
        self.last_depth = None
        self.mission_timer = None
        self.log = log
        if not self.controller.skip_arduino_compile:
            burner = ArduinoBurner(self.controller.log)
            burner.burn_boards()

    

        self.controller.lastTime = time.time()

    def run_once(self):

        self.controller.get_next_serial_line()
        if not self.controller.disable_safety:
            self.controller.get_next_serial_line_safety()
        if self.controller.test_mode:

            self.controller.get_cli_command()

        # update relevant data
        self.last_depth = self.depth
        self.depth = self.controller.current_depth

    def set_target_depth(self, target_depth):
        self.log.info(f'setting target depth to {target_depth} [mbar]')
        self.controller.target_depth = target_depth

    def set_mission_state(self, state):
        self.log.info(f'setting state to {state}')
        self.controller.current_mission_state = state


#-----------------------MAIN BODY--------------------------#

# def mission_1(manager):
#     while True:
#         manager.run_once()
#         if manager.depth and manager.depth != manager.last_depth:  # new depth
#             manager.log.debug('new depth reached:' + str(round(manager.depth,2)))
#             # last_depth = depth

#             threshold_reached = manager.depth - MARGIN < manager.app.target_depth < manager.depth + MARGIN
#             timer_started = manager.mission_timer is not None
#             if threshold_reached and not timer_started:
#                 manager.app.log.info('starting timer')
#                 manager.mission_timer = time.time()

#             if manager.mission_timer and time.time() - manager.mission_timer > 60:
#                 manager.log.info('time is up')
#                 manager.app.current_state = State.END_TASK


#         time.sleep(0.01)

class Captain:
    def __init__(self, log, pilot) -> None:
        self.log = log
        self.pilot = pilot

    def mission_2(self):
        # planned_depths = [20.0, 0, 40.0,'E',0]
        planned_depths = [20, 0, 20, 0]  #, 5, 0]
        # planned_depths = [11.5]
        # planned_depths = ['E']

        kd = 1000
        kp = 60
        # self.pilot.controller.pid_controller.kp = kp
        mission_state = MissionState.IDLE
        # if next_depth == 0:
        #     mission_state = MissionState.ASCENDING

        self.pilot.set_mission_state(mission_state)


        self.pilot.controller.pid_controller.kd = 0

        start_mission = False

        while True:
            self.pilot.run_once()  # RUN ONCE
            if self.pilot.controller.current_state != State.EXEC_TASK:
                start_mission = True
                continue
            if start_mission:
                self.pilot.controller.pid_controller.kp = kp
                # self.pilot.controller.pid_controller.kd = kd
                next_depth = planned_depths.pop(0)
                self.pilot.set_target_depth(next_depth)  # set the first target depth
                start_mission = False
                if self.pilot.depth < next_depth:
                    mission_state = MissionState.DESCENDING
                else:
                    mission_state = MissionState.ASCENDING
                self.pilot.set_mission_state(mission_state)
                self.pilot.controller.pid_controller.kd = 0



            if self.pilot.depth and self.pilot.depth != self.pilot.last_depth:  # new depth
                self.log.debug('new depth reached:' + str(round(self.pilot.depth,2)))
                # last_depth = depth



                if mission_state == MissionState.DESCENDING:
                    min_bladder_reached = self.pilot.controller.bladder_is_at_min_volume
                    self.log.warning(f'min_bladder_reached {min_bladder_reached}')
                    if min_bladder_reached or self.pilot.depth > self.pilot.controller.target_depth:
                        mission_state = MissionState.EN_ROUTE
                        self.pilot.set_mission_state(mission_state)
                        self.pilot.controller.pid_controller.kd = kd

                elif mission_state == MissionState.ASCENDING:
                    max_bladder_reached = self.pilot.controller.bladder_is_at_max_volume
                    self.log.warning(f'max_bladder_reached {max_bladder_reached}')
                    if max_bladder_reached or self.pilot.depth < self.pilot.controller.target_depth:
                        mission_state = MissionState.EN_ROUTE
                        self.pilot.set_mission_state(mission_state)
                        self.pilot.controller.pid_controller.kd = kd


                elif mission_state == MissionState.EN_ROUTE:

                    threshold_reached = self.pilot.depth - MARGIN < self.pilot.controller.target_depth < self.pilot.depth + MARGIN
                    timer_started = self.pilot.mission_timer is not None
                    if threshold_reached and not timer_started:
                        self.log.info('starting timer')
                        self.pilot.mission_timer = time.time()
                        mission_state = MissionState.HOLD_ON_TARGET
                        self.pilot.set_mission_state(mission_state)
                        self.log.info(mission_state)
                        

                elif mission_state == MissionState.HOLD_ON_TARGET:

                    if self.pilot.mission_timer and time.time() - self.pilot.mission_timer > 30:
                        self.log.info('hold position timer is up')
                        self.pilot.mission_timer = None
                        if not planned_depths:
                            self.pilot.controller.current_state = State.END_TASK
                            mission_state = MissionState.HOLD_ON_TARGET
                            self.pilot.set_mission_state(mission_state)
                            continue

                        next_target_depth = planned_depths.pop(0)

                        if next_target_depth == 'E':
                            self.pilot.controller.current_state = State.EMERGENCY
                            mission_state = MissionState.MISSION_ABORT
                            self.pilot.set_mission_state(mission_state)


                        self.pilot.set_target_depth(next_target_depth)
                        if next_target_depth == 0:
                            mission_state = MissionState.SURFACE
                            self.pilot.set_mission_state(mission_state)
                            self.log.info(mission_state)
                            self.pilot.controller.pid_controller.kd = 0
                            continue
                        

                        if self.pilot.depth < next_target_depth:
                            mission_state = MissionState.DESCENDING
                        else:
                            mission_state = MissionState.ASCENDING
                        self.pilot.set_mission_state(mission_state)
                        # mission_state = MissionState.EN_ROUTE
                        # self.log.info(mission_state)
                        # self.pilot.set_mission_state(mission_state)
                        self.pilot.controller.pid_controller.kd = 0
                        


                elif mission_state == MissionState.SURFACE:
                    surface_reached = self.pilot.controller.pressureController.senseAir()
                    timer_started = self.pilot.mission_timer is not None
                    if surface_reached and not timer_started:
                        self.log.info('starting timer')
                        self.pilot.mission_timer = time.time()
                        mission_state = MissionState.HOLD_ON_TARGET
                        self.pilot.set_mission_state(mission_state)
                        self.pilot.controller.comm.write(f"I:1") 
                        self.log.info(mission_state)

                elif mission_state == MissionState.MISSION_ABORT:
                    continue
                elif mission_state == MissionState.IDLE:
                    continue



            # time.sleep(0.01)     



def main():
        logger = Logger(cfg.app['simulation'])
        log = logger.get_log()
    # while True:
        try:
            controller = Controller(log)
            pilot = Pilot(log, controller)
            captain = Captain(log, pilot)
            try:
                captain.mission_2()
            except KeyboardInterrupt as e:
                log.info(e)
                log.critical('System shutdown')
                pilot.controller.clean()
                log.info('cleaning (resetting rpi gpio)')
                if not pilot.controller.disable_safety:
                    log.info('sending sleep to nano')
                    # manager.app.send_sleep_to_nano()
                    pilot.controller.sleep_safety()
                    pilot.controller.current_state = State.SLEEP_SAFETY
                    while not pilot.controller.nano_is_sleeping:
                        log.info('waiting for nano to respond/sleep')
                        pilot.run_once()
                        time.sleep(0.1)
                    log.info('nano is sleeping')
                exit(1)
            except Exception as e:
                log.exception(e)

        except Exception as e:
            log.exception(e)
            print("unknown error: emergency full surface")
            log.critical("unknown error: emergency full surface")

        print("unknown error: emergency full surface")
        log.critical("unknown error: emergency full surface")


    


if __name__ == "__main__":
    main()


