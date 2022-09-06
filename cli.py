# import time
from logging import exception
import socket
# import random
import cfg.configuration as cfg
from enum import Enum
import json


class Comm():
    def __init__(self) -> None:
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(1.0)
        self.client_socket.setblocking(False)
        # self.addr = ("127.0.0.1", 12000)
        self.addr = (cfg.app["host_ip"], cfg.app["test_mode_udp_port"])
        # self.client_socket.connect(self.addr)

    def sendMessage(self, message = b'test'):
        # message 
        line = bytes(message, encoding='utf-8')
        self.client_socket.sendto(line, self.addr)
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
                # print(message)
                s = message.decode('utf-8','ignore')
                header, value = s.strip().split(":")
                # value = float(value)
                # print("header",header)
                # print("value",value)
                print(header,value)
menu = """
1. set target depth in decibar
2. water sense 
3. execute task
4. wait for pickup 
5. surface
6. wakeup safety
7. sleep safety
8. send PID
9. restart
10. dive
11. calibrate
12. emergency
13. drop weight
0. stop
"""


class Direction(Enum):
    DOWN = 1
    UP = 2







class CLI():
    def __init__(self) -> None:
        self.com = Comm()
        self.direction = Direction.DOWN
        self.voltage = 0
        self.timeOn = 5.0
        self.timeOff = 0.5
        self.repeat = 0
        self.cycle = 0


    def sub_menu(self):
        while True:
            self.pid_menu = f"""
1. Direction: {self.direction.value} ({self.direction.name})
2. Voltage: {self.voltage}
3. TimeOn: {self.timeOn}
4. TimeOff: {self.timeOff}
5. Repeat: {self.repeat}
   Cycle: {self.cycle}
"""

            print(self.pid_menu)
            from_user = input()

            if from_user == '1':
                val = input("Direction:")
                if val == '1':
                    self.direction = Direction.DOWN
                elif val == '2':
                    self.direction = Direction.UP

            if from_user == '2':
                val = input("Voltage:")
                self.voltage = val

            if from_user == '3':
                val = input("TimeOn:")
                self.timeOn = val

            if from_user == '4':
                val = input("TimeOff:")
                self.timeOff = val

            if from_user == '5':
                val = input("Repeat:")
                self.repeat = val

            if from_user == '6':
                val = input("Direction:")



    
    def run(self):
        while (True):
            print(menu)
            from_user = input()
            
            if from_user == '1':
                mission_input = input("mission:")
                depths = mission_input.split(',')
                mission = []
                for value in depths:
                    if value == 'E':
                        mission.append('E')
                        continue
                    try:
                        value = float(value)
                    except ValueError as e:
                        print(e)
                        print("illegal value")
                        break

                    if value < 0:
                        print("illegal value")
                        break
                    
                    mission.append(value)

                print(f"setting mission to {mission}")
                self.com.sendMessage(f"mission:{json.dumps(mission)}")

            if from_user == '2':
                print("water test")
                self.com.sendMessage("water:0")

            if from_user == '3':
                print("exec_task")
                self.com.sendMessage("exec_task:0")

            if from_user == '4':
                print("wait for pickup")
                self.com.sendMessage("pickup:0")

            if from_user == '5':
                print("surface")
                self.com.sendMessage("surface:0")

            if from_user == '6':
                print('sending wakeup safety')
                self.com.sendMessage('wakeup_safety:0')

            if from_user == '7':
                print('sending sleep  safety')
                self.com.sendMessage('sleep_safety:0')

            if from_user == '8':
                print('send PID')
                self.sub_menu()

            if from_user == '9':
                print("restarting")
                self.com.sendMessage("restart:0")

            if from_user == '10':
                print('dive')
                self.com.sendMessage("dive:0")

            if from_user == '11':
                print('calibrate')
                self.com.sendMessage("calibrate:0")

            if from_user == '12':
                print('emergency')
                self.com.sendMessage("emergency:0")

            if from_user == '13':
                print('drop weight')
                self.com.sendMessage("drop:0")
            
            if from_user == '0':
                print("stopping")
                self.com.sendMessage("stop:0")

    



if __name__=="__main__":
    print("main")
    c = CLI()
    c.run()

        
        