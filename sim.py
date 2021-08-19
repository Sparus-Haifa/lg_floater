from main import State
import pygame as pg
import time
import socket
import random

from pygame.event import pump


class Comm():
    def __init__(self) -> None:
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(1.0)
        self.client_socket.setblocking(False)
        self.addr = ("127.0.0.1", 12000)
        # self.client_socket.connect(self.addr)
        self.pid = 0
        self.lastPID = 0
        self.pump = "off"
        self.voltage = 0.0
        self.timeOn = 0.0 # timeOn duration in seconds
        self.timeOff = 0.0
        self.direction = 1
        # up (D:1)
        # down (D:2)
        self.pumpOnTimeStamp = None # Time of received command to turn on pump

        # for debug
        self.p = 0
        self.kp = 0
        self.d = 0
        self.kd = 0
        self.targetDepth = 0
        self.trip = 0
        self.phase = 1
        self.error = 0
        self.current_state = 0


    def sendMessage(self, message = b'test'):
        # message 
        self.client_socket.sendto(message, self.addr)
        # self.client_socket.sendall(message)


    def recieveMessage(self):
        while True:
            try:
                message, address = self.client_socket.recvfrom(1024)
            except Exception as e:
                '''no data yet..'''
                break
                pass
                # print(e)
                # print('''no data yet..''')
            else:
                # message = message.upper()
                print(message)
                s = message.decode('utf-8','ignore')
                header, value = s.strip().split(":")
                # value = float(value)
                # print("header",header)
                # print("value",value)
                if header=="V":
                    self.voltage = float(value)
                elif header=="D":
                    self.direction = int(value)
                elif header=="T":
                    self.timeOn = float(value)
                    self.pumpOnTimeStamp = time.time()
                elif header=="PID":
                    self.lastPID = float(value)
                    self.pid = float(value)


                # for debug only
                elif header=="d":
                    self.d = float(value)
                elif header=="p":
                    self.p = float(value)
                elif header=="kd":
                    self.kd = float(value)
                elif header=="kp":
                    self.kp = float(value)
                elif header=="target":
                    self.targetDepth = float(value)
                elif header=="error":
                    self.error = float(value)
                elif header=="phase":
                    self.phase = int(value)
                elif header=="O":
                    self.timeOff = float(value)
                elif header=="State":
                    self.current_state = value



class YuriSim():
    def __init__(self, comm):
        self.comm = comm
        self.sensorNames = ["BT1", "BT2", "TT1", "TT2", "AT", "AP",  "X",  "Y",  "Z",   "BP1",   "BP2",   "TP1",   "TP2", "HP",      "PD", "PC", "H1", "H2", "BV", "RPM" ] # bv
        self.sensorValue = [23.66, 23.14, 23.29, 23.34,    0,    0, 0.01,-0.00, 0.00, 1031.60, 1035.30, 1022.40, 1034.00,    0, -26607.00, 9.00, 0.00, 0.00, 0.00,  23.00 ] # cc
        self.depth = 0
        self.pumpIsOn = False
        self.startPumpTimer = False
        self.pumpOnTime = 0.0 # dateTime stamp of turning on the pump
        self.pumpTimer = 0.0 # time the pump is working in the currect duty cycle
        self.offTimer = 0
        self.currentBladderVolume = 0

        
        # print(f"{len(self.sensorNames)}, {len(self.sensorValue)}")
        # self.phase = 1
        # phase 1 - normal pid to target
        # phase 2 - interpolation
        # phase 3 - TBD

    def startSim(self):

        counter = 0.0
        frame = 0 # just a counter to time sensors i/o

        pg.init()


        myfont = pg.font.SysFont("monospace", 15)

        LIGHTBLUE = pg.Color('lightskyblue2')
        DARKBLUE = pg.Color(11, 8, 69)
        RED = pg.Color(120,8,11)
        GREEN = pg.Color(11,120,8)

        display = pg.display.set_mode((800, 500))
        width, height = display.get_size()
        clock = pg.time.Clock()

        player_image = pg.Surface((30, 60))
        player_image.fill(DARKBLUE)

        x = width * 0.45
        # self.depth = 0 # Depth in meter
        # y_change = 0 # Speed in px per 1/FPS
        
        on_ground = False
        first_loop_sync = True

        # Const params
        PIXELRATIO = 20.0 # pixel to meter
        MASS = 20.4 # kg
        GRAVITY  = 9.8 # m/sec^2
        VOLUME_FLOATER = 0.01965 # m^3
        MAX_BLADDER_VOLUME = 0.00065 # m^3
        FW = 1025 # kg / m^3
        BUOYANCY_FLOATER = GRAVITY * VOLUME_FLOATER * FW # Volume * g * fw
        DRAG_COEFFECIENT = 0.82
        FLOATAREA = 3.14 * 0.18 * 0.18 / 4
        BCONST = 0.5 * FW * DRAG_COEFFECIENT * FLOATAREA # drag_coefficient * Object_area * fluid_density (FW)
        FPS = 2
        
        # Variables
        acceleration = .000
        self.currentBladderVolume = MAX_BLADDER_VOLUME # start at max
        speed = 0
        SimFactor = 1.0

        # GUI
        button_color = [0,255,0]



        startTime = time.time()
        done = False
        while not done:
            # handle pump

            if self.comm.current_state == State.INIT:
                print("Init")
            elif self.comm.current_state == State.WAIT_FOR_WATER:
                print("Waiting for water")
            elif self.comm.current_state == State.EXEC_TASK:
                print("Executing task")
            elif self.comm.current_state == State.END_TASK:
                print("Ending task")
            elif self.comm.current_state == State.EMERGENCY:
                print("Emergency")
            
            if self.comm.timeOn > 0:
                elapsed = time.time() - self.comm.pumpOnTimeStamp # elapsed seconds since pump turned on
                # pump on
                if elapsed < self.comm.timeOn: # if on "timeOn" cycle
                    if not self.pumpIsOn: # turn on pump
                        print("starting pump")
                        print("setting timer for", self.comm.timeOn)
                        self.pumpIsOn = True
                        # self.pumpOnDuration = self.comm.timeOn
                        self.pumpOnTime = time.time()
                    else: # keep pump on
                        print("Pump is running")
                        self.pumpTimer = time.time() - self.pumpOnTime
                        self.offTimer = 0
                        # timeOnOver = self.pumpTimer > self.pumpOnDuration # Time on has passed. now time off
                        timeOnOver = self.pumpTimer > self.comm.timeOn # Time on has passed. now time off

                        bladderIsFull = self.currentBladderVolume == MAX_BLADDER_VOLUME
                        bladderIsEmpty = self.currentBladderVolume == 0
                        limitPump = self.comm.direction == 1.0 and bladderIsEmpty or self.comm.direction == 2.0 and bladderIsFull
                        if timeOnOver or limitPump: # turn on pump
                            print("turn off pump")
                            # case timeOn is 100%
                            # case timeOn is 0%
                            self.pumpIsOn = False
                            self.pumpTimer = 0
                # pump off
                elif elapsed > self.comm.timeOn and self.comm.timeOn + self.comm.timeOff: # if on "timeOff" cycle
                        print("turn off pump")
                        # case timeOn is 100%
                        # case timeOn is 0%
                        self.pumpIsOn = False
                        self.pumpTimer = 0
                        # self.offTimer = time.time() - self.pumpOnTime - self.pumpOnDuration
                        # self.offTimer = elapsed - self.pumpOnDuration
                        self.offTimer = elapsed - self.comm.timeOn


                        if self.offTimer < 0 :
                            print("pump on timer", time.time() - self.pumpOnTime)
                            print("timer error", self.offTimer)
                            assert()
                            # return
                
                # can resend PID
                elif elapsed > self.comm.timeOn + self.comm.timeOff: # after duty-cycle. if no new dc command is ready.
                    # self.pumpOnDuration = 0
                    # self.comm.timeOn=0
                    # self.comm.timeOff=0
                    pass


            else:
                print("time off?")



                # pumpOnTime = time.time()
                # while
            # if self.pumpIsOn and self.comm.pid > 10:
            #     currentBladderVolume -= 0.01 * self.comm.pid * 0.00001
            #     self.comm.pid=0
            # elif self.pumpIsOn and self.comm.pid <-10:
            #     currentBladderVolume += 0.01 * self.comm.pid * -0.00001
            #     self.comm.pid=0
            if self.pumpIsOn:
                value = 0.01 * self.comm.voltage * 0.00001
                if self.comm.direction != 1.0:
                    value*=-1
                self.currentBladderVolume -= value
                # self.comm.pid=0
                # self.pumpFlag=1
                self.sendMessage("PF",1, True)


            if self.currentBladderVolume < 0:
                self.currentBladderVolume = 0
                self.pumpIsOn = False
            if self.currentBladderVolume > MAX_BLADDER_VOLUME:
                self.currentBladderVolume = MAX_BLADDER_VOLUME
                self.pumpIsOn = False

            if not self.pumpIsOn:
                self.sendMessage("PF",0, True)
            
            button = pg.Rect(450, 160, 50, 50)
            mouse_pos = (0,0)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    done = True
                if event.type == pg.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos  # gets mouse position    
                    print("click")

                # checks if mouse position is over the button

                if button.collidepoint(mouse_pos):
                    # prints current location of mouse
                    print('button was pressed at {0}'.format(mouse_pos))
                    button_color = [255,0,0]
                    self.sendMessage("PF",2,True)


            # Add the GRAVITY value to y_change, so that
            # the object moves faster each frame.

            drag = BCONST * speed * speed
            if speed > 0:
                drag*=-1

            bouyancyBladder = self.currentBladderVolume * GRAVITY * FW

            acceleration = (MASS*GRAVITY - BUOYANCY_FLOATER - bouyancyBladder + drag)/MASS
            TIMESTEP = 1 / FPS
            speed = speed + acceleration * TIMESTEP
            speed *= SimFactor

            self.depth = self.depth + speed * TIMESTEP 

            if self.depth <=0 :
                self.depth=0
                speed=0
                acceleration = 0

            # self.depth=y
            y = self.depth * PIXELRATIO

            # Draw everything.
            display.fill(LIGHTBLUE)
            
            # render text
            diff_time = time.time() - startTime
            str_time = "{:.2f}".format(diff_time)
            label_timer = myfont.render(f"[real time:{str_time} secs]", 1, DARKBLUE)
            display.blit(label_timer, (20, 20))

            # frameRa

            fps = clock.get_fps()
            fps_str = "{:.2f}".format(fps)
            # label_fps = myfont.render(f"[fps :{fps_str} ]", 1, DARKBLUE)
            # display.blit(label_fps, (450, 100))


            counter+=SimFactor/FPS
            counter_str = "{:.2f}".format(counter)
            label_counter = myfont.render(f"[sim time:{counter_str} secs] [FPS: {fps_str}]", 1, DARKBLUE)
            display.blit(label_counter, (20, 40))

            depth_str = "{:.4f}".format(self.depth)
            label_depth = myfont.render(f"[depth:{depth_str} meter]", 1, DARKBLUE)
            display.blit(label_depth, (20, 60))

            vel_str = "{:.4f}".format(speed*FPS/SimFactor)
            label_speed = myfont.render(f"[velocity:{vel_str} m/s]", 1, DARKBLUE)
            display.blit(label_speed, (20, 80))

            acc_str = "{:.6f}".format(acceleration*FPS/SimFactor)
            label_acceleration = myfont.render(f"[acceleration:{acc_str} m/s^2]", 1, DARKBLUE)
            display.blit(label_acceleration, (20, 100))


            drag_str = "{:.6f}".format(drag*60)
            label_drag = myfont.render(f"[drag:{drag_str} N]", 1, DARKBLUE)
            display.blit(label_drag, (20, 120))




            avg = 0
            avg_count = 0
            for i, sensor in enumerate(self.sensorNames):
                if sensor.startswith("TP") or sensor == "HP" or sensor.startswith("BP"):
                    value = float(self.sensorValue[i])
                    # value*=(1 + self.depth * 1) # 1 decibar = 1 meter
                    if value<10 or value > 65536:
                        # print("sensor error:",sensor,"value=",value)
                        continue
                    value += self.depth*100
                    avg+=value
                    avg_count+=1
            if avg_count>0:
                avg/=avg_count 

            # 1000 milibar = 10.0 decibar
            # 1 decibar ~= 1 meter.
            avgSens_str = "{:.2f}".format(avg/100)
            label_avgSens = myfont.render(f"[avg depth sensors:{avgSens_str} decibar]", 1, DARKBLUE)
            display.blit(label_avgSens, (20, 160))

            targetSens_str = "{:.2f}".format(self.comm.targetDepth/100)
            label_targetSens = myfont.render(f"[target sensor pressure:{targetSens_str} decibar]", 1, DARKBLUE)
            display.blit(label_targetSens, (20, 180))






            p_str  = "{:.2f}".format(self.comm.p)
            kp_str = "{:.2f}".format(self.comm.kp)
            tp_str = "{:.2f}".format(self.comm.p*self.comm.kp)
            label_p = myfont.render(f"[p:{p_str} * kp:{kp_str} = {tp_str}]", 1, DARKBLUE)
            display.blit(label_p, (20, 240))


            d_str  = "{:.2f}".format(self.comm.d)
            kd_str = "{:.2f}".format(self.comm.kd * -1)
            td_str = "{:.2f}".format(self.comm.kd * self.comm.d * -1)
            label_d = myfont.render(f"[d:{d_str} * kd:{kd_str} = {td_str}]", 1, DARKBLUE)
            display.blit(label_d, (20, 260))

            tpid_str = "{:.2f}".format(self.comm.lastPID)
            label_tpid = myfont.render(f"[raw pid:{tpid_str}]", 1, DARKBLUE)
            display.blit(label_tpid, (20, 280))







            error_str = "{:.2f}".format(self.comm.error)
            label_trip = myfont.render(f"[error :{error_str} meter]", 1, DARKBLUE)
            display.blit(label_trip, (20, 340))

            # phase_str = "{:.2f}".format(self.comm.trip*100)
            label_phase = myfont.render(f"[phase :{self.comm.phase} ]", 1, DARKBLUE)
            display.blit(label_phase, (20, 360))

            # right side UI
            pump_str = "On" if self.pumpIsOn else "Off"
            color = GREEN if self.pumpIsOn else RED
            label_pump = myfont.render(f"[Pump :{pump_str} ]", 1, color)
            display.blit(label_pump, (450, 20))

            d_str = "Down" if self.comm.direction == 1.0 else "Up"
            label_voltage = myfont.render(f"[Direction :{d_str}]", 1, DARKBLUE)
            display.blit(label_voltage, (450, 40))

            timeOn_str = "{:.2f}".format(self.comm.timeOn)
            timeOff_str = "{:.2f}".format(self.comm.timeOff)
            label_dc = myfont.render(f"[timeOn :{timeOn_str} sec] [timeOff :{timeOff_str} sec]", 1, DARKBLUE)
            display.blit(label_dc, (450, 60))


            timerPump_str = "{:.2f}".format(self.pumpTimer)
            timerOff_str = "{:.2f}".format(self.offTimer)
            label_dc = myfont.render(f"[timer on: {timerPump_str} sec] [timer off: {timerOff_str} sec", 1, DARKBLUE)
            display.blit(label_dc, (450, 80))

            voltage_str = "{:.2f}".format(self.comm.voltage)
            label_dc = myfont.render(f"[Voltage :{voltage_str} %]", 1, DARKBLUE)
            display.blit(label_dc, (450, 100))


            bladderSize_str = "{:.2f}".format(self.currentBladderVolume*1000000)
            bladderPercent_str = "{:.2f}".format(self.currentBladderVolume*100/MAX_BLADDER_VOLUME)
            label_bladder = myfont.render(f"[bladder size:{bladderPercent_str} %] [{bladderSize_str} cc]", 1, DARKBLUE)
            display.blit(label_bladder, (450, 120))

            
            # state_str = "{:.2f}".format(self.comm.current_state)
            label_bladder = myfont.render(f"[state:{self.comm.current_state}]", 1, DARKBLUE)
            display.blit(label_bladder, (450, 140))


            
            pg.draw.rect(display, button_color, button)  # draw button


            depth = (self.comm.targetDepth - 1035)* PIXELRATIO / 100
            pg.draw.line(display, (255, 0, 0), (0, depth), (width, depth))
            # display.blit(player_image, (x, y))

            pg.draw.line(display, (0, 0, 0), (0, height-70), (width, height-70))
            display.blit(player_image, (x, y))

            pg.display.update()

            # send sensor data
            frame+=1
            # if int(counter) % 10 ==0 and counter.is_integer():
            # if frame % (FPS/SimFactor) == 0:

            self.updateBladderValue()
            if self.pumpIsOn:# and frame % FPS == 0:
                self.sendPumpSensors()
            else:
                self.sendAllSensors()
            self.comm.recieveMessage()
            clock.tick(FPS)

        pg.quit()

    def updateBladderValue(self):
        sensorNum = self.sensorNames.index("BV")
        self.sensorValue[sensorNum]=self.currentBladderVolume*1000000 # send in cc
        print(f"value of sensor {sensorNum} {self.sensorNames[sensorNum]} is {self.sensorValue[sensorNum]}")
    
    def sendPumpSensors(self):
        for sensorNum in range(len(self.sensorNames)-1,len(self.sensorNames)-3,-1):
            print("sending sensor",sensorNum)
            self.sendStats(sensorNum)

    def sendAllSensors(self):
        for sensorNum in range(len(self.sensorNames) - 1):
            self.sendStats(sensorNum)

    def sendStats(self, sensorNum):
        # self.comm.sendMessage(bytes(f"hello from sim {int(counter)}\n",'utf-8'))
        # if self.nextSensor == len(self.sensorNames) - 1:
        #     self.nextSensor = 0
        
        sensor = self.sensorNames[sensorNum]
        value = self.sensorValue[sensorNum]

        if sensor.startswith("TP") or sensor == "HP" or sensor.startswith("BP"):
            # value*=(1 + self.depth * 1) 
            if 10 < value and value < 65536: # handle bad sensors
                value += self.depth*100

        # self.comm.sendMessage(bytes(f"hello from sim {int(counter)} {message}\n",'utf-8'))

        # add noise
        plusOrMinus = random.randint(0,1)
        fraction = random.random()
        noise = value*fraction / 1000
        if plusOrMinus == 0:
            value+=noise
        else:
            value-=noise

        # add errors
        addErrors = random.randint(1,100) > 99
        if addErrors:
            value = "ovf"


        self.sendMessage(sensor,value, True)

    def sendMessage(self,header,value, rawValue):
        # message = ""
        if rawValue:
            message = header + ':' + str(value)
        else:
            message = header + ':' + "{:.4f}".format(value)
        print(f"sending: {message}")
        self.comm.sendMessage(bytes(f"{message}",'utf-8'))


        
    
if __name__=="__main__":
    comm = Comm()
    # print("hello")
    sim = YuriSim(comm)
    sim.startSim()
