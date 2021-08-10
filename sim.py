import pygame as pg
import time
import socket


class Comm():
    def __init__(self) -> None:
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.settimeout(1.0)
        self.client_socket.setblocking(False)
        self.addr = ("127.0.0.1", 12000)
        self.pid = 0
        self.lastPID = 0
        self.pump = "off"
        self.voltage = 0.0
        self.timeOn = 0.0
        self.timeOff = 0.0
        self.direction = 1
        # up (D:1)
        # down (D:2)

        # for debug
        self.p = 0
        self.kp = 0
        self.d = 0
        self.kd = 0
        self.targetDepth = 0
        self.trip = 0
        self.phase = 1


    def sendMessage(self, message = b'test'):
        # message 
        self.client_socket.sendto(message, self.addr)


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
                value = float(value)
                # print("header",header)
                # print("value",value)
                if header=="V":
                    # if self.direction != 1.0:
                        # value*=-1
                    # self.pid = value
                    # self.lastPID = value
                    self.voltage = value
                    # if self.voltage < 40:
                        # self.voltage = 40
                elif header=="D":
                    self.direction = value
                elif header=="T":
                    # self.T = value
                    # self.pid = self.pid * value
                    self.timeOn = value
                elif header=="PID":
                    self.lastPID = value
                    self.pid = value


                # for debug only
                elif header=="d":
                    self.d = value
                elif header=="p":
                    self.p = value
                elif header=="kd":
                    self.kd = value
                elif header=="kp":
                    self.kp = value
                elif header=="target":
                    self.targetDepth = value
                elif header=="trip":
                    self.trip = value
                elif header=="phase":
                    self.phase = value



class YuriSim():
    def __init__(self, comm):
        self.comm = comm
        self.sensorNames = ["BT1", "BT2", "TT1", "TT2", "AT", "AP",  "X",  "Y",  "Z",   "BP1",   "BP2",   "TP1",   "TP2", "HP",      "PD", "PC", "H1", "H2", "PU", "RPM" ]
        self.sensorValue = [23.66, 23.14, 23.29, 23.34,    0,    0, 0.01,-0.00, 0.00, 1031.60, 1035.30, 1022.40, 1034.00,    0, -26607.00, 9.00, 0.00, 0.00,    0, 23.00 ] 
        self.nextSensor = 0
        self.depth = 0
        # print(f"{len(self.sensorNames)}, {len(self.sensorValue)}")
        # self.phase = 1
        # phase 1 - normal pid to target
        # phase 2 - interpolation
        # phase 3 - TBD

    def startSim(self):

        counter = 0.0
        frame = 0 # just a counter to time sensors i/o

        pg.init()
        FPS = 2
        SimFactor = 1.0

        myfont = pg.font.SysFont("monospace", 15)

        LIGHTBLUE = pg.Color('lightskyblue2')
        DARKBLUE = pg.Color(11, 8, 69)

        display = pg.display.set_mode((800, 500))
        width, height = display.get_size()
        clock = pg.time.Clock()

        player_image = pg.Surface((30, 60))
        player_image.fill(DARKBLUE)

        x = width * 0.45
        # self.depth = 0 # Depth in meter
        y_change = 0 # Speed in px per 1/FPS
        on_ground = False
        first_loop_sync = True

        # A constant value that you add to the y_change each frame.
        PIXELRATIO = 1.0 # pixel to meter
        MASS = 20.3 # kg
        GRAVITY  = 9.8 # m/sec^2
        VOLUME_FLOATER = 0.0197 # m^3
        MAX_BLADDER_VOLUME = 0.00065 # m^3
        currentBladderVolume = MAX_BLADDER_VOLUME # start at max
        FW = 1025 # kg / m^3
        BUOYANCY_FLOATER = GRAVITY * VOLUME_FLOATER * FW #9.6 # Volume * g * fw
        NETFORCE = .000
        BCONST = 1.0 # drag_coefficient * Object_area * fluid_density (FW)


        startTime = time.time()
        done = False
        while not done:
            if self.comm.pid > 10:
                currentBladderVolume -= 0.01 * self.comm.pid * 0.00001
                self.comm.pid=0
            elif self.comm.pid <-10:
                currentBladderVolume += 0.01 * self.comm.pid * -0.00001
                self.comm.pid=0
            if currentBladderVolume < 0:
                currentBladderVolume = 0
            if currentBladderVolume > MAX_BLADDER_VOLUME:
                currentBladderVolume = MAX_BLADDER_VOLUME
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    done = True


            # Add the GRAVITY value to y_change, so that
            # the object moves faster each frame.

            drag = BCONST * y_change* y_change
            if y_change < 0:
                drag*=-1

            bouyancyBladder = currentBladderVolume * GRAVITY * FW

            NETFORCE = MASS*GRAVITY - BUOYANCY_FLOATER - bouyancyBladder - drag
            NETFORCE /= FPS
            NETFORCE *= SimFactor


            y_change += NETFORCE
            self.depth += y_change
            # Stop the object when it's near the bottom of the screen.
            # if self.depth >= (height - 130)*PIXELRATIO:
            #     self.depth = (height - 130)*PIXELRATIO
            #     y_change = 0
            #     on_ground = True
            if self.depth <=0 :
                y_change=0
                self.depth=0

            # self.depth=y
            y = self.depth * PIXELRATIO

            # Draw everything.
            display.fill(LIGHTBLUE)
            
            # render text
            diff_time = time.time() - startTime
            str_time = "{:.4f}".format(diff_time)
            label_timer = myfont.render(f"[real time:{str_time} secs]", 1, DARKBLUE)
            display.blit(label_timer, (20, 20))

            # frameRa
            counter+=SimFactor/FPS
            counter_str = "{:.4f}".format(counter)
            label_counter = myfont.render(f"[sim time:{counter_str} secs]", 1, DARKBLUE)
            display.blit(label_counter, (20, 40))

            depth_str = "{:.4f}".format(self.depth)
            label_depth = myfont.render(f"[depth:{depth_str} meter]", 1, DARKBLUE)
            display.blit(label_depth, (20, 60))

            vel_str = "{:.4f}".format(y_change*FPS/SimFactor)
            label_speed = myfont.render(f"[velocity:{vel_str} m/s]", 1, DARKBLUE)
            display.blit(label_speed, (20, 80))

            g_str = "{:.6f}".format(GRAVITY)
            label_g = myfont.render(f"[gravity :{g_str} m/s^2]", 1, DARKBLUE)
            display.blit(label_g, (20, 100))  



            buoyancy_str = "{:.6f}".format(BUOYANCY_FLOATER)
            label_buoyancy = myfont.render(f"[object buoyancy:{buoyancy_str} m/s^2]", 1, DARKBLUE)
            display.blit(label_buoyancy, (20, 120))

            bladder_str = "{:.6f}".format(bouyancyBladder)
            label_bladder = myfont.render(f"[bladder buoyancy:{bladder_str} m/s^2]", 1, DARKBLUE)
            display.blit(label_bladder, (20, 140))

            bladderSize_str = "{:.2f}".format(currentBladderVolume*1000000)
            bladderPercent_str = "{:.2f}".format(currentBladderVolume*100/MAX_BLADDER_VOLUME)
            label_bladder = myfont.render(f"[bladder size:{bladderPercent_str} %] [{bladderSize_str} cc]", 1, DARKBLUE)
            display.blit(label_bladder, (20, 160))

            totalb_str = "{:.6f}".format(BUOYANCY_FLOATER + currentBladderVolume)
            label_totalb = myfont.render(f"[total buoyancy:{totalb_str} m/s^2]", 1, DARKBLUE)
            display.blit(label_totalb, (20, 180))

            drag_str = "{:.6f}".format(drag*60)
            label_drag = myfont.render(f"[drag:{drag_str} m/s^2]", 1, DARKBLUE)
            display.blit(label_drag, (20, 200))

            acc_str = "{:.6f}".format(NETFORCE*FPS/SimFactor)
            label_acceleration = myfont.render(f"[acceleration:{acc_str} m/s^2]", 1, DARKBLUE)
            display.blit(label_acceleration, (20, 220))

            p_str  = "{:.2f}".format(self.comm.p)
            kp_str = "{:.2f}".format(self.comm.kp)
            tp_str = "{:.2f}".format(self.comm.p*self.comm.kp)
            label_p = myfont.render(f"[p:{p_str} * kp:{kp_str} = {tp_str}]", 1, DARKBLUE)
            display.blit(label_p, (20, 240))


            d_str  = "{:.2f}".format(self.comm.d)
            kd_str = "{:.2f}".format(self.comm.kd)
            td_str = "{:.2f}".format(self.comm.kd * self.comm.d)
            label_d = myfont.render(f"[d:{d_str} * kd:{kd_str} = {td_str}]", 1, DARKBLUE)
            display.blit(label_d, (20, 260))

            tpid_str = "{:.2f}".format(self.comm.lastPID)
            label_tpid = myfont.render(f"[raw pid:{tpid_str}]", 1, DARKBLUE)
            display.blit(label_tpid, (20, 280))




            avg = 0
            avg_count = 0
            for i, sensor in enumerate(self.sensorNames):
                if sensor.startswith("TP") or sensor == "HP" or sensor.startswith("BP"):
                    value = float(self.sensorValue[i])
                    value*=(1 + self.depth * 0.001)
                    if value<10 or value > 65536:
                        continue
                    avg+=value
                    avg_count+=1
            if avg_count>0:
                avg/=avg_count 

            # 1000 milibar = 10.0 decibar
            # 1 decibar ~= 1 meter.
            avgSens_str = "{:.2f}".format(avg/100)
            label_avgSens = myfont.render(f"[avg depth sensors:{avgSens_str} decibar]", 1, DARKBLUE)
            display.blit(label_avgSens, (20, 300))

            targetSens_str = "{:.2f}".format(self.comm.targetDepth/100)
            label_targetSens = myfont.render(f"[target sensor pressure:{targetSens_str} decibar]", 1, DARKBLUE)
            display.blit(label_targetSens, (20, 320))

            trip_str = "{:.2f}".format(self.comm.trip*100)
            label_trip = myfont.render(f"[trip percentage:{trip_str} %]", 1, DARKBLUE)
            display.blit(label_trip, (20, 340))

            # phase_str = "{:.2f}".format(self.comm.trip*100)
            label_phase = myfont.render(f"[phase :{self.comm.phase} ]", 1, DARKBLUE)
            display.blit(label_phase, (20, 360))

            # right side UI
            label_pump = myfont.render(f"[pump :{self.comm.pump} ]", 1, DARKBLUE)
            display.blit(label_pump, (450, 20))

            d_str = "Down"
            if self.comm.direction != 1.0:
                d_str = "Up"
            
            
            voltage_str = "{:.2f}".format(self.comm.voltage)
            label_voltage = myfont.render(f"[PID to pump :{voltage_str} %] [direction :{d_str}]", 1, DARKBLUE)
            display.blit(label_voltage, (450, 40))

            timeOn_str = "{:.2f}".format(self.comm.timeOn)
            label_dc = myfont.render(f"[timeOn :{timeOn_str} sec] [timeOff :{self.comm.timeOff} sec]", 1, DARKBLUE)
            display.blit(label_dc, (450, 60))


            fps = clock.get_fps()
            fps_str = "{:.2f}".format(fps)
            label_fps = myfont.render(f"[fps :{fps_str} ]", 1, DARKBLUE)
            display.blit(label_fps, (450, 80))



            pg.draw.line(display, (0, 0, 0), (0, height-70), (width, height-70))
            display.blit(player_image, (x, y))

            pg.display.update()

            # send sensor data
            frame+=1
            # if int(counter) % 10 ==0 and counter.is_integer():
            # if frame % (FPS/SimFactor) == 0:
            if frame % FPS == 0:
                self.sendAllSensors()
            self.comm.recieveMessage()
            clock.tick(FPS)

        pg.quit()

    def sendAllSensors(self):
        for _ in range(len(self.sensorNames)):
            self.sendStats()

    def sendStats(self):
        # self.comm.sendMessage(bytes(f"hello from sim {int(counter)}\n",'utf-8'))
        if self.nextSensor == len(self.sensorNames):
            self.nextSensor = 0
        
        sensor = self.sensorNames[self.nextSensor]
        value = self.sensorValue[self.nextSensor]

        if sensor.startswith("TP") or sensor == "HP" or sensor.startswith("BP"):
            value*=(1 + self.depth * 0.001) 
        message = sensor + ':' + "{:.2f}".format(value)
        # self.comm.sendMessage(bytes(f"hello from sim {int(counter)} {message}\n",'utf-8'))
        print(f"sending: {message}")
        self.comm.sendMessage(bytes(f"{message}\n",'utf-8'))

        self.nextSensor+=1
    
if __name__=="__main__":
    comm = Comm()
    # print("hello")
    sim = YuriSim(comm)
    sim.startSim()
