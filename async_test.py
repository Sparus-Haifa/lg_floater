import asyncio
# from transitions.core import Transition
from transitions import State
from transitions.extensions.asyncio import HierarchicalAsyncMachine, NestedAsyncState
# from cfg.configuration import State
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

        self.mission = [30, 0, 30, 15, 'E']


        self.states = ['PID', 'wait_for_pickup', 'emergency']
        self.transitions = [
            ['init', 'initial', 'PID']
        ]
        self.states.append(NestedAsyncState(name="sensorBuffer", on_enter="check_sensor_buffer"))
        self.states.append(NestedAsyncState(name="calibrating", on_enter="calibrate"))
        self.states.append(NestedAsyncState(name="waitingForWater", on_enter="sense_water"))
        self.states.append(NestedAsyncState(name="waitingTask", on_enter="set_next_target"))


        self.machine = HierarchicalAsyncMachine(self, states=self.states, transitions=self.transitions, ignore_invalid_triggers=True) # , initial='wait_for_sensor_buffer')
        self.machine.add_transition('hull_leak_emergency', '*', 'emergency', unless=['is_wait_for_pickup', 'is_emergency'])
        self.machine.add_transition('sensors_buffers_are_full', 'wait_for_sensor_buffer', 'calibrate_depth_sensors', conditions=['sensors_are_ready'])
        self.machine.add_transition('calibrate_sensors', ['calibrate_depth_sensors'], 'wait_for_water', conditions=['sensors_are_calibrated'], before=['sensors_are_calibrated'])
        # self.to_wait_for_sensor_buffer()
        

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
            case 'PD': await self.sensors.altimeter.add_sample(value)
            case 'PC': await self.sensors.altimeter.add_confidance(value)
            case 'PU': await self.sensors.pumpFlag.add_sample(value)
            case 'RPM':  self.sensors.rpm.add_sample(value)
            case 'PF':  self.sensors.pumpFlag.add_sample(value)
            case 'BV':  await self.sensors.bladderVolume.add_sample(value)
            case 'FS':  self.sensors.full_surface_flag.add_sample(value)
            case 'I' | 'IR':  self.sensors.iridium_flag.add_sample(value)

            case _ : pass # print(f'error {msg}')

    async def handle_HL(self):
        # await self.to_PID()
        # print('handling hl')
        value = self.sensors.leak_h_flag.getLast()
        if value == 1:
            await self.hull_leak_emergency()

    def fancy_log(self, res, csv):
        headers = []
        for key in res:
            value = res[key]

            #shorten floats
            check_float = isinstance(value, float)
            if check_float:
                value = "{:.2f}".format(value)

            end = len(str(value)) + 1 - len(key)
            if len(key)>len(str(value)):
                end=1

            line = f"{key}"
            full_line = line + " "*end
            # print(line ,end=" "*end)
            headers.append(full_line)
        # print()
        if csv:
            if self.add_headers_to_csv:
                self.csv_log.critical(",".join(headers))
                self.add_headers_to_csv = False
        else:
            self.log.info("".join(headers))

        values = []
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
            

            line = f"{value}"
            full_line = line + " "*end
            # print(line, end=" "*end)
            values.append(full_line)
        # print()
        if csv:
            self.csv_log.critical(",".join(values))
        else:
            self.log.info("".join(values))
        # BT1   BT2   TT1   TT2   AT AP X    Y     Z    BP1     BP2     TP1     TP2     HP PD       PC   H1   H2   pump rpm
        # 23.66 23.14 23.29 23.34 0  0  0.01 -0.00 0.00 1031.60 1035.30 1022.40 1034.00 0 -26607.00 9.00 0.00 0.00 None 0

        # BT1   BT2   TT1   TT2   X    Y    Z   BP1    BP2    TP1    TP2    HP  PD          PC  H1 H2 pump BV       rpm  PF State      
        # 23.66 23.14 23.29 23.34 0.01 -0.0 0.0 1031.6 1035.3 1022.4 1034.0 0.0 -26607.0000 9.0 0  0  0    650.0000 None 0  State.INIT


    async def log_sensors(self):
        # print('logging sensors')
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

        self.fancy_log(res, False)
  
        await asyncio.sleep(2)
        asyncio.create_task(self.log_sensors())

    async def sensors_are_calibrated(self):
        print('calibrating')
        return self.sensors.pressureController.calibrate()


    async def check_sensor_buffer(self):
        print('checking sensor buffer')
        if await self.sensors_are_ready():
            # await self.sensors_buffers_are_full()
            print('sensors are ready!')
            asyncio.create_task(self.to_calibrating())
            return
        await asyncio.sleep(1)
        asyncio.create_task(self.check_sensor_buffer())

    async def sensors_are_ready(self):
        bypassSens = ["rpm"]
        for sensor in self.sensors.sensors:
            if sensor not in bypassSens and not self.sensors.sensors[sensor].isBufferFull(): # TODO: fix rpm and [and sensor!="PF"]
                self.log.warning(f"sensor {sensor} is not ready")
                return False
        bypassFlag = ["PF", "FS", "I"]
        for flag in self.sensors.flags:
            if flag not in bypassFlag and not self.sensors.flags[flag].isBufferFull():
                self.log.warning(f"flag {flag} is not ready")
                return False

        return True      


    async def calibrate(self):
        print("calibrating")

        await asyncio.sleep(10)

        # asyncio.create_task(self.to_calibrating())

        res = await self.sensors.pressureController.calibrate()
        if res == True:
            asyncio.create_task(self.to_waitingForWater())
            return
        
        asyncio.create_task(self.to_calibrating())

    async def sense_water(self):
        print("waiting for water")
        await asyncio.sleep(10)
        res = await self.sensors.pressureController.senseWater()
        if res == True:
            asyncio.create_task(self.to_waitingTask())
            return
        
        asyncio.create_task(self.to_waitingForWater())

    async def set_next_target(self):
        print("set_next_target")
        if not self.mission:
            print("end mission")

        next_depth = self.mission.pop(0)

        match next_depth:
            case 'E': print('emegency')
            case number if isinstance(number, int) or isinstance(number, float): print(f"got depth {number}")
            case _ : print(f"error {_}")

        




async def sequence(driver):
    loop = asyncio.get_event_loop()
    # check_buffer = driver.check_sensor_buffer()
    # loop.create_task(check_buffer)
    await driver.to_sensorBuffer()


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

    seq = sequence(driver)
    loop.create_task(seq)

    # driver.machine.to_wait_for_sensor_buffer()

    # loop.run_forever()

    

    loop.run_forever()

    loop.close()



if __name__=='__main__':
    main()
