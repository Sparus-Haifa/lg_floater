import socket
import asyncio
import os, random

HOST, PORT = 'localhost', 12000


def send_test_message(message: 'Message to send to UDP port 514') -> None:
    sock = socket.socket(socket.AF_INET,  # Internet
                         socket.SOCK_DGRAM)  # UDP
    sock.sendto(message.encode(), (HOST, PORT))


async def write_messages() -> "Continuously write messages to UDP port 514":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fp = open(os.path.join(dir_path, "tests/example.log"))
    print("writing")
    for line in fp.readlines():
        await asyncio.sleep(random.uniform(0.1, 3.0))
        send_test_message(line)


class SyslogProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        super().__init__()

    def connection_made(self, transport) -> "Used by asyncio":
        self.transport = transport

    def datagram_received(self, data, addr) -> "Main entrypoint for processing message":
        # Here is where you would push message to whatever methods/classes you want.
        print(f"Received Syslog message: {data}")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    t = loop.create_datagram_endpoint(SyslogProtocol, local_addr=('0.0.0.0', PORT))
    loop.run_until_complete(t) # Server starts listening
    # loop.run_until_complete(write_messages()) # Start writing messages (or running tests)
    loop.run_forever()