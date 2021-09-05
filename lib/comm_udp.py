import cfg
import random
import socket
import errno
from time import sleep


class UdpComm():
    def __init__(self, port) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.settimeout(1.0)
        # self.server_socket.setblocking(False)
        # self.server_socket.bind(('', 12000))
        self.server_socket.bind(('', port))
        self.address= ("127.0.0.1", 12003)


    def read(self):
        try:
            message, self.address = self.server_socket.recvfrom(1024)
        except socket.error as e:
            err = e.args[0]
            if err== errno.EAGAIN or err==errno.EWOULDBLOCK:
                return b""
        else:
            return message
            

    def write(self, message = b"noting\n"):
        line = bytes(message, encoding='utf-8')
        self.server_socket.sendto(line, self.address)




if __name__=="__main__":
    comm = UdpComm()
    i = 0
    while True:
        i+=1
        comm.read()
        if i % 100 == 0:
            comm.write(bytes(f"Yolo {i}\n",'utf-8'))
        sleep(0.01)
    # rand = random.randint(0, 10)
    
