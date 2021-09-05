# import time
import socket
# import random
import cfg.configuration as cfg



class Comm():
    def __init__(self) -> None:
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(1.0)
        self.client_socket.setblocking(False)
        # self.addr = ("127.0.0.1", 12000)
        self.addr = ("127.0.0.1", cfg.app["simulation_udp_port"])
        # self.client_socket.connect(self.addr)

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
                # print(message)
                s = message.decode('utf-8','ignore')
                header, value = s.strip().split(":")
                # value = float(value)
                # print("header",header)
                # print("value",value)
                if header=="V":
                    self.voltage = float(value)
menu = """
1. run test 1
2. run test 2

0. stop
"""

while (True):
    print(menu)
    from_user = input()
    if from_user == '0':
        print("stopping")
        

if __name__=="__main__":
    print("main")