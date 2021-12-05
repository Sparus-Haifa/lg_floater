import asyncio
from transitions.core import Transition
from transitions.extensions.asyncio import HierarchicalAsyncMachine
from lib.logger import Logger
import logging

from sensors import Sensors
import signal



class DatagramDriver(asyncio.DatagramProtocol):
    def __init__(self, queue) -> None:
        super().__init__()
        self.queue = queue
        
    def connection_made(self, transport) -> None:  # "Used by asyncio"
        self.transport = transport

    def datagram_received(self, data, addr) -> None:  # "Main entrypoint for processing message"
        # Here is where you would push message to whatever methods/classes you want.
        self.queue.put_nowait(data.decode())
        # asyncio.create_task(self.queue.put(data.decode()))



        # self.log_data.append(data)


class Driver:
    def __init__(self, queue) -> None:
        self.log = logging.getLogger("normal")
        self.log_csv = logging.getLogger("csv")

        self.queue = queue
        self.sensors = Sensors()
        self.controller = Controller()

        self.states = ['wait_for_sensor_buffer', 'PID', 'wait_for_pickup', 'emergency']
        self.transitions = [
            ['init', 'initial', 'PID']
        ]
        self.machine = HierarchicalAsyncMachine(self, states=self.states, transitions=self.transitions, ignore_invalid_triggers=True, initial='wait_for_sensor_buffer')
        self.machine.add_transition('hull_leak_emergency', '*', 'emergency', unless=['is_wait_for_pickup', 'is_emergency'])




    async def consume(self):
        # log_normal = logging.getLogger("normal")
        # log_csv = logging.getLogger("csv")
        
        while True:
            msg = await self.queue.get()
            # print(f'consumed: {msg}')
            # log.debug(msg)
            # log_csv.critical("a,a,a,a,a")

            asyncio.create_task(self.handle_message(msg))
            # print(self.state)
            # await asyncio.sleep(0.1)

    async def handle_message(self, msg):
        header, value = msg.split(':')
        if not value:
            print('error')
            self.log.error(f'Message received without a value: {msg}')

        match header:
            case 'TT1' | 'TT2' | 'BT1' | 'BT2' | 'AT': await self.sensors.temperatureSensors[header].add_sample(value)
            case 'TP1' | 'TP2' | 'BP1' | 'BP2' | 'HP' | 'AP': await self.sensors.pressureSensors[header].add_sample(value)
            case 'X' | 'Y' | 'Z': await self.sensors.IMUSensors[header].add_sample(value)
            case 'HL':
                await self.sensors.leak_h_flag.add_sample(value)
                asyncio.create_task(self.handle_HL())
            case 'EL': await self.sensors.leak_e_flag.add_sample(value)
            case 'BF': await self.sensors.bladder_flag.add_sample(value)

            case _ : pass # print(f'error {msg}')

    async def handle_HL(self):
        # await self.to_PID()
        # print('handling hl')
        value = self.sensors.leak_h_flag.getLast()
        # if value == 1:
        await self.hull_leak_emergency()

    async def log_sensors(self):
        print('logging sensors')
        res = {}

        for key in self.sensors.temperatureSensors:
            value = self.sensors.temperatureSensors[key].getLast()
            # print(f"{key} {value}")
            res[key]=value   

        for key in self.sensors.IMUSensors:
            value = self.sensors.IMUSensors[key].getLast()
            # print(f"{key} {value}")
            res[key]=value

        for key in self.sensors.pressureSensors:
            value = self.sensors.pressureSensors[key].getLast()
            # print(f"{key} {value}")
            res[key]=value

        res["PD"]=self.sensors.altimeter.getLast()
        res["PC"]=self.sensors.altimeter.getConfidance()
        res["HL"]=self.sensors.leak_h_flag.state   # self.sensors.leak_h_flag.getLast()
        res["EL"]=self.sensors.leak_e_flag.getLast()
        res["BF"]=self.sensors.bladder_flag.state   # self.sensors.bladder_flag.getLast()
        res["SF"]=self.sensors.full_surface_flag.getLast()
        res["PF"]=self.sensors.pumpFlag.state   # self.sensors.pumpFlag.getLast()
        res["BV"]=self.sensors.bladderVolume.getLast()
        res["rpm"]=self.sensors.rpm.getLast()
        res["State"]=self.state   # self.sensors.current_state.name
        res['MissionState']=self.state    # self.sensors.current_mission_state.name
        res['Setpoint']=self.controller.target_depth
        res['Error']=self.controller.error
        res['Depth']=self.controller.current_depth

        print(res)
        await asyncio.sleep(1)
        asyncio.create_task(self.log_sensors())




class Controller:
    def __init__(self) -> None:
        self.current_depth = None
        self.target_depth = None
        self.error = None
        self.states = ['wait_for_sensor_buffer', 'wait_for_safety','inflate_bladder', 'calibrate_depth_sensors', 'wait_for_water', 'exec_task', 'end_task', 'sleep_safety', 'wait_for_pickup', 'emergency', 'stop', 'controlled']
        self.machine = HierarchicalAsyncMachine(self, states=self.states, transitions=[])




def main():
    # logger = Logger(False)

    logging.basicConfig()
    logging.root.setLevel(logging.NOTSET)
    logging.getLogger('transitions').setLevel(logging.WARNING)
    global log
    # log = logging.getLogger("normal")
    # log.setLevel(logging.NOTSET)
    global log_csv
    # log_csv = logging.getLogger("csv")




    queue = asyncio.Queue()
    driver = Driver(queue)



    loop = asyncio.new_event_loop()
    # loop = asyncio.get_event_loop()



    t = loop.create_datagram_endpoint(lambda: DatagramDriver(queue), local_addr=('0.0.0.0', 12000), )
    loop.run_until_complete(t) # Server starts listening
    # loop.create_task(t)


    # loop.run_until_complete(driver.consume()) # Start writing messages (or running tests)
    c = driver.consume()
    loop.create_task(c) # Start writing messages (or running tests)

    # loop.run_until_complete(driver.log_sensors())
    l = driver.log_sensors()
    loop.create_task(l)

    # loop.run_forever()
    loop.run_forever()

    loop.close()



if __name__=='__main__':
    main()
