import random
import socket
import errno
from time import sleep


class TcpComm():
    def __init__(self) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.server_socket.settimeout(1.0)
        # self.server_socket.setblocking(False)
        self.server_socket.bind(('', 12000))
        self.address= ("127.0.0.1", 12003)
        self.server_socket.listen()
        self.conn, self.addr = self.server_socket.accept()


    def read(self):
        try:
            message = self.conn.recv(1024)
        except socket.error as e:
            err = e.args[0]
            if err== errno.EAGAIN or err==errno.EWOULDBLOCK:
                return b""
        else:
            return message
            

    def write(self, message = b"noting\n"):
        line = bytes(message, encoding='utf-8')
        self.conn.sendall(line, self.address)




if __name__=="__main__":
    comm = TcpComm()
    i = 0
    while True:
        i+=1
        comm.read()
        if i % 100 == 0:
            comm.write(bytes(f"Yolo {i}\n",'utf-8'))
        sleep(0.01)
    # rand = random.randint(0, 10)
    
