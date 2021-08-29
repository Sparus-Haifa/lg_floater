from lib.pid_ctrl import PID
from lib.rpm import RPM
from lib.flag import Flag
from lib.altimeter import Altimeter
from lib.bladder_volume import Bladder
import time
import cfg.configuration as cfg
import lib.logger as logger
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

import sys # for args


class State(Enum):
    INIT = 0
    WAIT_FOR_SAFETY = 1
    WAIT_FOR_WATER = 2
    EXEC_TASK = 3
    END_TASK = 4
    WAIT_FOR_PICKUP = 5
    EMERGENCY = 6

# Current_state = State.INIT

class App():
    def __init__(self, simulation):
        log = logger.Logger()
        self.lastTime = time.time()
        self.lastP=0 # TODO: move to pid module
        self.pid_controller = PID()
        # safety = Safety(cfg.safety["min_alt"], cfg.safety["max_interval_between_pings"], log)

        self.current_state = State.INIT
        self.is_safety_responding = False
        self.weightDropped = False
        self.safteyTimer = None
        # self.idle = True  # dutycycle is off: init state, bladder already at max or min state etc.

        self.bladder_is_at_min_volume = False
        self.bladder_is_at_max_volume = False


        self.waterSenseDuration = 5 # sould be 5 min = 60*5 [sec]
        self.waterTestTimer = None

        # Task execusion timers
        self.time_off_duration = None
        self.time_on_duration = None
        # self.dcTimer = None
        self.time_off_timer = None
        
        # self.pid_sent
        self.pid_sent_time = None
        self.simulation = simulation
        self.simFactor = 1.0

        self.sensors = {}
        self.flags = {}

        # Pressure
        self.pressureController = Press_ctrl(cfg.pressure["avg_samples"], cfg.pressure["precision"], cfg.pressure["epsilon"], log)
        self.pressureController.addSensor("BP1")
        self.pressureController.addSensor("BP2")
        self.pressureController.addSensor("TP1")
        self.pressureController.addSensor("TP2")
        self.pressureController.addSensor("HP")
        self.pressureController.addSensor("AP")
        self.pressureSensors = self.pressureController.getSensors()

        # Temperature
        self.temperatureController = Temp_ctrl(cfg.temperature["avg_samples"], cfg.temperature["precision"], log)
        self.temperatureController.addSensor("BT1")
        self.temperatureController.addSensor("BT2")
        self.temperatureController.addSensor("TT1")
        self.temperatureController.addSensor("TT2")
        self.temperatureController.addSensor("AT")
        self.temperatureSensors = self.temperatureController.getSensors()

        # IMU
        self.IMUController = IMU_ctrl(cfg.imu["avg_samples"], cfg.imu["precision"], log)
        self.IMUController.addSensor("X")
        self.IMUController.addSensor("Y")
        self.IMUController.addSensor("Z")
        self.IMUSensors = self.IMUController.getSensors()
        
        # Other sensors
        self.bladderVolume = Bladder("Bladder Volume", cfg.bladder["avg_samples"], cfg.bladder["precision"], log)
        self.altimeter = Altimeter("Altimeter", cfg.altimeter["avg_samples"], cfg.altimeter["precision"], log)
        self.rpm = RPM("RPM", cfg.rpm["avg_samples"], cfg.rpm["precision"], log)


        # Flags
        self.pumpFlag = Flag("Pump flag",log)  # PF
        self.bladder_flag = Flag("Bladder flag", log)  # BF
        self.leak_h_flag = Flag("Hull leak", log)  # HL
        self.leak_e_flag = Flag("Engine leak", log)  # EL
        self.full_surface_flag = Flag("Full surface initiated", log)


        self.addSensorsToDict()
        self.addFlagsToDict()


        self.profile = Profile("cfg/profile.txt", log)
        # self.task_ctrl = Task(sensPress, log)

        # Main arduino
        if not self.simulation:
            self.comm = ser.SerialComm(cfg.serial["port"], cfg.serial["baud_rate"], cfg.serial["timeout"], log)
            if not self.comm.ser:
                print("-E- Failed to init serial port")
                exit()
        else:
        # Simulated via udp
            self.comm = com.UdpComm()
            if not self.comm.server_socket:
                print("-E- Failed to init udp port")
                exit() 

        # Secondary arduino (safety)
        self.comm_safety = ser.SerialComm(cfg.serial_safety["port"], cfg.serial_safety["baud_rate"], cfg.serial_safety["timeout"], log)
        if not self.comm_safety.ser:
            print("-E- Failed to init safety serial port")
            exit()


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


    #get line from main arduino; decode it, store the data and execute an appropriate callback
    def get_next_serial_line(self):
        serial_line = self.comm.read() # e.g. data=['P1', '1.23']
        if serial_line == None:
            # print(f"Waiting for message from arduino. Received: {serial_line}")
            return
        serial_line = serial_line.decode('utf-8', 'ignore').strip().split(":")
        if serial_line!=b"" and ("User message received" in serial_line) or ("U:" in serial_line):
            print("raw: {}".format(serial_line))
        header = serial_line[0]
        if len(serial_line)<2:
            return #no Value, break
        value = serial_line[1]




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

    def handle_PD(self):
        # TODO: decide which comes first from arduino
        # assuming PC comes first
        value = self.altimeter.getLast()
        confidance = self.altimeter.getConfidance()
        if confidance > 50:
            if 10 < value and value <= 20:
                print("Yellow line! Ending mission!")
                # Alert
                # Start emergency ascending with bladder first
                self.comm_safety.write("S:1")
                self.current_state = State.END_TASK
            elif value <= 10:
                print("Red line! Aborting mission!")
                self.current_state = State.EMERGENCY


    def handle_PF(self, lastValue):
        value = self.pumpFlag.getLast()
        if value==0:
            # pump is off:
            # 1. pump init
            # 2. pump cut on time
            # 3. pump cut before time
            if lastValue and lastValue != value:
                print("Pump turned off. Starting timeOff timer.")
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
            print("pump turned on")
            # self.pumpFlag.add_sample(1)
            pass
        elif value==2:
            # print("pump not working")
            # self.pumpFlag.add_sample(2)
            # leak
            self.current_state = State.EMERGENCY
            self.comm_safety.write("N:2")
        else:
            print("PF value error",value)
            # assert()


    def handle_BV(self):
         # send pid
        if self.simulation:
            self.comm.write(f"State:{self.current_state}\n")  # debug send state

        self.run_mission_sequence()
        


    
    def run_mission_sequence(self):
        self.logSensors()

        # INIT
        if self.current_state == State.INIT:
            # TODO: add waiting for safety to ping
            if self.sensorsReady():
                self.current_state = State.WAIT_FOR_SAFETY
            return

        # WAIT FOR SAFETY
        elif self.current_state == State.WAIT_FOR_SAFETY:
            if self.is_safety_responding:
                self.current_state = State.WAIT_FOR_WATER
            else:
                print("waiting for safety to respond")
                
        # WAIT FOR WATER
        elif self.current_state == State.WAIT_FOR_WATER:
            if not self.waterTestTimer:
                print("Waiting for water")
                self.waterTestTimer = time.time()
            elapsedSeconds = (time.time() - self.waterTestTimer)*self.simFactor
            limitSeconds = self.waterSenseDuration
            if  elapsedSeconds > limitSeconds:
                print("Done waiting for water")
                if self.pressureController.senseWater():
                    self.current_state = State.EXEC_TASK
                else:
                    print("water not detected")
                    self.waterTestTimer = time.time()
            else:
                print("Waiting for water")
                print(f"{round(elapsedSeconds)}/{limitSeconds} secs")
            return

        # EXECUTE TASK
        elif self.current_state == State.EXEC_TASK:
            # print("Executing task")

            # Before starting a dutycycle.
            if self.time_off_duration is None: 
                # before DC starts
                print("starting a new dutycycle")
                self.sendPID()
            # after
            elif self.time_on_duration is None:
                elapsedSeconds = (time.time() - self.time_off_timer)*self.simFactor
                print(f"waiting for timeOff to finish {round(elapsedSeconds,2)} of {self.time_off_duration}")
                if elapsedSeconds > self.time_off_duration:
                    print("timeOff is over")
                    self.time_off_duration = None
                    self.time_off_timer = None

            else:
                print("waiting for timeOn to finish")


        # END TASK
        elif self.current_state == State.END_TASK:
            # print("Ending task")
            pass

        # EMERGENCY
        elif self.current_state == State.EMERGENCY:
            print("Emergency")
            # self.comm_safety.write("N:2") # sending the command to drop the dropweight to saftey
            return



    def sensorsReady(self):
        bypassSens = ["rpm"]
        for sensor in self.sensors:
            if sensor not in bypassSens and not self.sensors[sensor].isBufferFull(): # TODO: fix rpm and [and sensor!="PF"]
                print(f"sensor {sensor} is not ready")
                return False
        bypassFlag = ["PF", "FS"]
        for flag in self.flags:
            if flag not in bypassFlag and not self.flags[flag].isBufferFull():
                print(f"flag {flag} is not ready")
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
        res["State"]=self.current_state

        for key in res:
            value = res[key]

            #shorten floats
            check_float = isinstance(value, float)
            if check_float:
                value = "{:.2f}".format(value)

            end = len(str(value)) + 1 - len(key)
            if len(key)>len(str(value)):
                end=1

            print(f"{key}" ,end=" "*end)
        print()

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
            

            
            print(f"{value}" ,end=" "*end)
        print()
        # BT1   BT2   TT1   TT2   AT AP X    Y     Z    BP1     BP2     TP1     TP2     HP PD       PC   H1   H2   pump rpm
        # 23.66 23.14 23.29 23.34 0  0  0.01 -0.00 0.00 1031.60 1035.30 1022.40 1034.00 0 -26607.00 9.00 0.00 0.00 None 0

        # BT1   BT2   TT1   TT2   X    Y    Z   BP1    BP2    TP1    TP2    HP  PD          PC  H1 H2 pump BV       rpm  PF State      
        # 23.66 23.14 23.29 23.34 0.01 -0.0 0.0 1031.6 1035.3 1022.4 1034.0 0.0 -26607.0000 9.0 0  0  0    650.0000 None 0  State.INIT
        if self.weightDropped:
            print("weight dropped!")


    def sendPID(self):
        print("calculating PID")


        def getAvgDepthSensorsRead():
            avg = 0
            count = 0
            for sensor in self.pressureSensors:
                value = float(self.pressureSensors[sensor].getLast())
                # print(f"{sensor}:{value}")
                if 10 > value or value > 65536:
                    print(f"error in {sensor } sensor value: {value} is out of bound!")
                    # print("")
                    continue
                avg+=value
                count+=1
            
            if count==0:
                print("error /0") # no valid presure sensors data
                return None
            avg/=count
            return avg

        avg = getAvgDepthSensorsRead()
        if not avg:
            print("ERROR: Could not calculate depth - not enough working sensors")
            return

        def getTargetDepth(target_depth_in_meters):
            p0 = 10.35 # TODO: get pressure at sea level
            m = 1 # TODO: get linear function of sensors
            corrected = p0 + m*target_depth_in_meters # linear function
            target_depth = corrected * 100 # in milibar
            return target_depth

        target_depth_in_meters = 50
        target_depth = getTargetDepth(target_depth_in_meters)
    

        # PID
        error = target_depth - avg
        # print("Error",error, "target", target_depth, "avg", avg)
        scalar = self.pid_controller.pid(error)
        direction, voltage, dc, self.time_on_duration, self.time_off_duration = self.pid_controller.unpack(scalar)

        if self.time_off_duration < 0.5:
            self.time_off_duration = 0.5

        if self.time_off_duration > 20.0:
            self.time_off_duration = 20.0

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

        
        # bv = self.sensors["BV"].getLast()
        # buffer = 15
        # maxDive =  bv<200.0 + buffer and direction == 1
        # maxAscend = bv>450.0 - buffer and direction == 2

        if self.bladder_is_at_max_volume and direction == 2:
            print("Bladder is at max volume")
            # self.idle = True
            self.time_on_duration = None
            self.time_off_duration = None
            self.time_off_timer = None
            
        elif self.bladder_is_at_min_volume and direction == 1:
            print("Bladder is at min volume")
            # self.idle = True
            self.time_on_duration = None
            self.time_off_duration = None
            self.time_off_timer = None
        else:
            print(f"sending PID - Voltage:{voltage}    direction:{direction}    timeOn:{self.time_on_duration}  timeOff:{self.time_off_duration}")
            self.comm.write(f"V:{voltage}\n")
            self.comm.write(f"D:{direction}\n")
            self.comm.write(f"T:{self.time_on_duration}\n")
            # TODO: dont start untill arduino sends PF=1
            # self.idle = False
        # time.sleep(0.01)

        # self.time_off_timer = time.time()
        

        # time.sleep(timeOn + timeOff)

    #get line from secondary arduino;
    def get_next_serial_line_safety(self):
        # self.comm_safety.write("N:11")
        
        # send "I'm alive message"

        # timer if no ping from safety inflate bladder
        if not self.safteyTimer:
            self.safteyTimer = time.time()

        timeout = time.time() - self.safteyTimer > 30
        if timeout:
            print("safety not responding!")
            self.is_safety_responding = False
            self.current_state = State.EMERGENCY # will make weight drop on reconnection
            # TODO: inflate bladder

        serial_line = self.comm_safety.read()  # e.g. data=['P1', '1.23']
        serial_line = serial_line.strip().decode('utf-8', 'ignore').split(":")
        
        if len(serial_line) < 2: # skip if no message
            # print("Waiting for message from safety. Received: None")
            return
        
        # print("raw: {}".format(serial_line))

        header = serial_line[0]
        value = None
        try:
            value = int(float(serial_line[1]))
        except ValueError as e:
            print(f"Error parsing value {value} from safety")
            return

        if serial_line[0].upper().startswith("N"):
            # print("adding {}".format(serial_line))
            # self.safety.add_sample(serial_line)
            # safety_callback()
            if value==1:
                # if self.current_state == State.EMERGENCY:
                #     self.comm_safety.write("N:2") # sending the command to drop the dropweight to saftey
                self.safteyTimer = time.time()
                print("pong!")
                self.is_safety_responding = True
                pass # ping acknowledge
            if value==2:
                print("safety weight dropped on command acknowledge")
                self.current_state = State.EMERGENCY                
                self.weightDropped = True
                pass # drop weight acknowledge
            if value==3: # Saftey requests a ping
                print("ping!")
                self.comm_safety.write("N:1") # sending ping to saftey
            if value==4:
                print("weight dropped due to over time acknowledge")
                self.current_state = State.EMERGENCY
                self.weightDropped = True
                pass # weight dropped due to over time
            

    def end_mission(why):
        log.write("mission was ended: {}".format(why))



    #---------- Callbacks--------------#

    #when a new temperature sample arrives
    def t_callback():
        pass

    #when a new pressure sample arrives
    # def p_callback():
    #     if cfg.Current_state == cfg.State.INIT:
    #         if sensPress._queues_are_full:
    #             cfg.Current_state = cfg.State.WAIT_FOR_WATER

    #     elif cfg.Current_state == cfg.State.WAIT_FOR_WATER:
    #         if sensPress.get_delta_up_down() >= cfg.pressure["epsilon"]:
    #             cfg.Current_state = cfg.State.EXEC_TASK

    #     elif cfg.Current_state == cfg.State.EXEC_TASK:
    #         cmd_to_send = task_ctrl.exec()
    #         if cmd_to_send: #not None
    #             comm.write(cmd_to_send)



    #when a new IMU sample arrives
    def imu_callback():
        pass

    #when a new IMU sample arrives
    # def safety_callback():
    #     if safety.is_emergency_state():
    #         comm_safety.write("N:13") #report emergency to secondary arduino
    #         comm.write("U:193")


#-----------------------MAIN BODY--------------------------#

if __name__ == "__main__":
    
    # print("num of args",len(sys.argv))
    # print("args",sys.argv)

    # app = App()

    def isSimulation():
        if len(sys.argv)>1:
            arg = sys.argv[1]
            if "True" in arg:
                return True
            return False

    if isSimulation():
        print("Simulation mode")
        app = App(True)
    else:
        app = App(False)


 

    app.lastTime = time.time()
    while True:
        app.get_next_serial_line()
        app.get_next_serial_line_safety()
        # time.sleep(0.01)

        # logSensors()
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
