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

class State(Enum):
    INIT = 1
    WAIT_FOR_WATER = 2
    EXEC_TASK = 3
    END_TASK = 4
    EMERGENCY = 5

# Current_state = State.INIT

class App():
    def __init__(self):
        log = logger.Logger()
        self.lastTime = time.time()
        self.lastP=0
        self.pid_controller = PID()
        safety = Safety(cfg.safety["min_alt"], cfg.safety["max_interval_between_pings"], log)
        # flags
        # fyi = FYI(log)
        # 
        self.current_state = State.INIT

        self.timeOff = None
        self.timeOn = None
        self.dcTimer = None

        self.pressureSensors = {}
        # for i in range(6):
        sensPress = Press("Bottom Pressure 1", cfg.pressure["avg_samples"], cfg.pressure["epsilon"], log)
        self.pressureSensors["BP1"]=sensPress

        sensPress = Press("Bottom Pressure 2", cfg.pressure["avg_samples"], cfg.pressure["epsilon"], log)
        self.pressureSensors["BP2"]=sensPress

        sensPress = Press("Top Pressure 1", cfg.pressure["avg_samples"], cfg.pressure["epsilon"], log)
        self.pressureSensors["TP1"]=sensPress

        sensPress = Press("Top Pressure 2", cfg.pressure["avg_samples"], cfg.pressure["epsilon"], log)
        self.pressureSensors["TP2"]=sensPress

        sensPress = Press("Hull Presure", cfg.pressure["avg_samples"], cfg.pressure["epsilon"], log)
        self.pressureSensors["HP"]=sensPress



        self.temperatureSensors = {}
        # for i in range(5):
        sensTemp = Temp("Buttom Temperatue 1", cfg.temperature["avg_samples"], log)
        self.temperatureSensors["BT1"]=sensTemp

        sensTemp = Temp("Bottom Temperatue 2", cfg.temperature["avg_samples"], log)
        self.temperatureSensors["BT2"]=sensTemp

        sensTemp = Temp("Top Temperature 1", cfg.temperature["avg_samples"], log)
        self.temperatureSensors["TT1"]=sensTemp

        sensTemp = Temp("Top Temperature 2", cfg.temperature["avg_samples"], log)
        self.temperatureSensors["TT2"]=sensTemp




        # self.internalTemperatureSensors = {}
        # # for i in range(2):
        # sensTemp = Temp("AT", cfg.temperature["avg_samples"], log)
        # self.internalTemperatureSensors["AT"]=sensTemp

        # sensTemp = Temp("AP", cfg.temperature["avg_samples"], log)
        # self.internalTemperatureSensors["AP"]=sensTemp

        self.IMUSensors = {}
        # for i in range(3):
        sensIMU = IMU("X", cfg.imu["avg_samples"], log)
        self.IMUSensors["X"]=sensIMU

        sensIMU = IMU("Y", cfg.imu["avg_samples"], log)
        self.IMUSensors["Y"]=sensIMU

        sensIMU = IMU("Z", cfg.imu["avg_samples"], log)
        self.IMUSensors["Z"]=sensIMU

        
        self.bladderVolume = Bladder("Bladder Volume", cfg.bladder["avg_samples"], log)

        self.altimeter = Altimeter("Altimeter", cfg.altimeter["avg_samples"], log)

        self.leak_h_flag = Flag("Hull leak", log) # hull leak
        self.leak_e_flag = Flag("Engine leak", log) # Engine leak

        self.pump_is_on = Flag("Pump", log)
        self.rpm = RPM("RPM", cfg.rpm["avg_samples"], log)






        self.profile = Profile("cfg/profile.txt", log)
        # self.task_ctrl = Task(sensPress, log)



        # Main arduino
        # self.comm = ser.SerialComm(cfg.serial["port"], cfg.serial["baud_rate"], cfg.serial["timeout"], log)
        # if not self.comm.ser:
        #     print("-E- Failed to init serial port")
        #     exit()

        # Simulated via udp
        # self.comm = com.UdpComm()
        self.comm = com.UdpComm()
        if not self.comm.server_socket:
            print("-E- Failed to init udp port")
            exit() 

        # Secondary arduino (safety)
        self.comm_safety = ser.SerialComm(cfg.serial_safety["port"], cfg.serial_safety["baud_rate"], cfg.serial_safety["timeout"], log)
        if not self.comm_safety.ser:
            print("-E- Failed to init safety serial port")
            # exit()



    #get line from main arduino; decode it, store the data and execute an appropriate callback
    def get_next_serial_line(self):
        serial_line = self.comm.read() # e.g. data=['P1', '1.23']
        if serial_line == None:
            print(f"Waiting for message from arduino. Received: {serial_line}")
            return
        # print("raw: {}".format(serial_line))
        serial_line = serial_line.decode('utf-8', 'ignore').strip().split(":")
        # split_line = serial_line.split(":")
        # print(serial_line)
        header = serial_line[0]
        # print(header)
        if len(serial_line)<2:
            return #no Value, break
        value = serial_line[1]



        # Pressure


        if header=="TT1":
            self.temperatureSensors["TT1"].add_sample(value)

        elif header=="TT2":
            self.temperatureSensors["TT2"].add_sample(value)

        elif header=="BT1":
            self.temperatureSensors["BT1"].add_sample(value)

        elif header=="BT2":
            self.temperatureSensors["BT2"].add_sample(value)
            
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
            
            

        elif header=="X":
            self.IMUSensors["X"].add_sample(value)

        elif header=="Y":
            self.IMUSensors["Y"].add_sample(value)
        
        elif header=="Z":
            self.IMUSensors["Z"].add_sample(value)



        elif header=="H1":
            self.leak_h_flag.add_sample(value)

        elif header=="H2":
            self.leak_e_flag.add_sample(value)

        elif header=="PD":
            self.altimeter.add_sample(value)

        elif header=="PC":
            self.altimeter.add_confidance(value)

        elif header=="PU":
            self.pump_is_on.add_sample(value)
            # maybe pid triger
        # else:
            # logSensors() # Last sensor update

            


        # TimeOn stats:
        elif header=="RPM":
            self.rpm.add_sample(value)
            # last sensor received, send pid commands to arduino
 



        # remove
        # elif header=="AT":
        #     self.internalTemperatureSensors["AT"].add_sample(value)

        # elif header=="AP":
        #     self.internalTemperatureSensors["AP"].add_sample(value)

        elif header=="BV": # on both cycles
            self.bladderVolume.add_sample(value)
            
            # send pid
            self.comm.write(f"State:{self.current_state}\n") # debug send state

            self.logSensors()

            if self.current_state == State.INIT:
                # print("Init")
                # time.sleep(0.01)
                # check sensor buffer is full before advancing
                return
            elif self.current_state == State.WAIT_FOR_WATER:
                # print("Waiting for water")
                pass
                
            elif self.current_state == State.EXEC_TASK:
                # print("Executing task")
                pass
            elif self.current_state == State.END_TASK:
                # print("Ending task")
                pass
            elif self.current_state == State.EMERGENCY:
                # print("Emergency")
                pass

            

            # logics
            # timeOnStarted = self.timeOn > 0
            # timeOffStarted = self.timeOff > 0
            betweenOnandOff = time.time() - self.dcTimer < self.timeOn + self.timeOff

            if not self.timeOn: # first time running. still no timeOn calc available
                self.sendPID()

            
            # elif timeOnStarted and timeOffStarted and betweenOnandOff:
            elif self.dcTimer and betweenOnandOff:
                print("time Off sleep?", self.timeOn, self.timeOff)

 
            else:
                self.sendPID()

        # on done
        elif header=="PF":
            value = int(float(value))
            if value==1:
                # print("pump turned on")
                self.pump_is_on.add_sample(1)
            elif value==0:
                # print("pump is off")
                self.pump_is_on.add_sample(0)
            elif value==2:
                # print("pump not working")
                self.pump_is_on.add_sample(2)
                # leak
                

    

        time.sleep(0.01)
    
    def logSensors(self):

        res = {}

        for key in self.temperatureSensors:
            value = self.temperatureSensors[key].getLast()
            # print(f"{key} {value}")
            res[key]=value
        
        # for key in self.internalTemperatureSensors:
        #     value = self.internalTemperatureSensors[key].getLast()
        #     # print(f"{key} {value}")
        #     res[key]=value

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

        res["H1"]=self.leak_h_flag.getLast()
        res["H2"]=self.leak_e_flag.getLast()

        res["pump"]=self.pump_is_on.getLast()
        res["BV"]=self.bladderVolume.getLast()
        res["rpm"]=self.rpm.getLast()
        res["PF"]=self.pump_is_on.getLast()

        res["State"]=self.current_state


        for key in res:
            end = len(str(res[key])) + 1 - len(key)
            if len(key)>len(str(res[key])):
                end=1
            print(f"{key}" ,end=" "*end)
        print()

        for key in res:
            end = 1
            # res = len(str(res[key])) + 3 - len(key)
            # if len(str(res[key])) > res:
            #     end = res
            if len(key)>len(str(res[key])):
                end=len(key) + 1 - len(str(res[key]))
            print(f"{res[key]}" ,end=" "*end)
        print()
        # BT1   BT2   TT1   TT2   AT AP X    Y     Z    BP1     BP2     TP1     TP2     HP PD       PC   H1   H2   pump rpm
        # 23.66 23.14 23.29 23.34 0  0  0.01 -0.00 0.00 1031.60 1035.30 1022.40 1034.00 0 -26607.00 9.00 0.00 0.00 None 0

        # BT1   BT2   TT1   TT2   X    Y    Z   BP1    BP2    TP1    TP2    HP  PD          PC  H1 H2 pump BV       rpm  PF State      
        # 23.66 23.14 23.29 23.34 0.01 -0.0 0.0 1031.6 1035.3 1022.4 1034.0 0.0 -26607.0000 9.0 0  0  0    650.0000 None 0  State.INIT


    def sendPID(self):
        print("start sending PID result to arduino")
        avg = 0
        count = 0
        for sensor in self.pressureSensors:
            value = float(self.pressureSensors[sensor].getLast())
            print(f"{sensor}:{value}")
            if 10 > value or value > 65536:
                print(f"error in {sensor } sensor value: {value}")
                print("out of bound")
                break
            avg+=value
            count+=1
        
        if count==0:
            print("error /0")
            return
        avg/=count

        print(f"avg = {avg}")
            
        print()

        target_sdpeth = 1500 # on 80% plus change PID 
        print(target_sdpeth) 
        # 1022*=(1 + self.depth * 0.01) 
        # target_depth=1022*(1 + target_sdpeth) * 0.01
        # print(target_depth)

        
        # TODO: find delta time
        # TODO: divide by time
        nowTime = time.time()
        deltaTime = nowTime - self.lastTime
        print(f"loop epoch time = {deltaTime}")
        self.lastTime = nowTime

        # PID
        Error = target_sdpeth - avg
        p = Error
        print("p",p)
        if self.lastP != 0:
            d = (self.lastP - p) / deltaTime
        else:
            d = 0
        print("d",d)
        self.lastP = p

        # doInterpulation = False # TODO: move to PID.moveToPhaseTwo = True
        
        # if abs(target_sdpeth - avg) < (0.2 *  target_sdpeth):
        if False: #self.pid_controller.doInterpolation or p < 200:
            print("change PID")
            self.pid_controller.doInterpolation = True
            kp=0.1 # madeup
            kd=4.00 # madeup
        else:
            kp=0.2
            kd=7


        # Sens debug data - for sim only
        # on 20% trip change PID
        # trip = 1 - abs(target_sdpeth - avg)/target_sdpeth # precent 80%
        self.comm.write(f"error:{p}\n")

        self.comm.write(f"p:{p}\n")
        time.sleep(0.01)
        self.comm.write(f"kp:{kp}\n")
        time.sleep(0.01)
        self.comm.write(f"d:{d}\n")
        time.sleep(0.01)
        self.comm.write(f"kd:{kd}\n")
        time.sleep(0.01)
        self.comm.write(f"target:{target_sdpeth}\n")
        time.sleep(0.01)



        # PID result
        scalar = p*kp-d*kd

        direction = self.pid_controller.getDirection(scalar)
        # scalar = abs(scalar)
        voltage = self.pid_controller.normal_pumpVoltage(scalar)
        dc = self.pid_controller.interp_dutyCycle(scalar)
        self.timeOn = self.pid_controller.interp_timeOn(scalar)
        self.timeOff = self.pid_controller.calc_timeOff(self.timeOn,dc)


        phase = 1
        print("Do inter",self.pid_controller.doInterpolation)
        if self.pid_controller.doInterpolation:
            phase = 2
            print("yes")
        self.comm.write(f"phase:{phase}\n") # sim debug

        # normalize scalar
        # if abs(scalar) > 100:
        #     scalar = 100
        # if abs(scalar) < 40:
        #     scalar = 0  

        # on target, break - move to phase 3 - Collect data etc...
        # if scalar==0:
        #     return

        print("sending PID")
        self.comm.write(f"PID:{scalar}") # sim debug
        self.comm.write(f"O:{self.timeOff}\n") # sim debug
        self.comm.write(f"V:{voltage}\n")
        self.comm.write(f"D:{direction}")
        self.comm.write(f"T:{self.timeOn}\n")
        time.sleep(0.01)

        self.dcTimer = time.time()
        

        # time.sleep(timeOn + timeOff)

    #get line from secondary arduino;
    def get_next_serial_line_safety(self):
        self.comm_safety.write("N:11")
        # send "I'm alive message"

        serial_line = self.comm_safety.read()  # e.g. data=['P1', '1.23']
        print("raw: {}".format(serial_line))
        serial_line = serial_line.strip().decode('utf-8', 'ignore').split(":")

        if serial_line[0].upper().startswith("N"):
            print("adding {}".format(serial_line))
            self.safety.add_sample(serial_line)
            safety_callback()

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
    

 

    app = App()
    app.lastTime = time.time()
    while True:
        app.get_next_serial_line()
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
