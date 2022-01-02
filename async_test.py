import asyncio
# from transitions.core import Transition
from transitions import State
import transitions
from transitions.extensions.asyncio import HierarchicalAsyncMachine, NestedAsyncState
# from cfg.configuration import State
from lib.logger import Logger
import logging

from sensors import Sensors
# import signal
import socket
from lib.pid_ctrl import PID

from transitions import Machine
from transitions.extensions.states import add_state_features, Tags, Timeout

from transitions.extensions.asyncio import AsyncTimeout, AsyncMachine

import serial_asyncio

# serial driver
class OutputProtocol(asyncio.Protocol):
    def __init__(self, queue) -> None:
        super().__init__()
        self.queue = queue

    def connection_made(self, transport):
        self.transport = transport
        print('port opened', transport)
        transport.serial.rts = False  # You can manipulate Serial object via transport
        transport.write(b'Hello, World!\n')  # Write serial data via transport

    def data_received(self, data):
        # print('data received', repr(data))
        # if b'\n' in data:
        #     self.transport.close()
        self.queue.put_nowait(data.decode())


    def connection_lost(self, exc):
        print('port closed')
        self.transport.loop.stop()

    def pause_writing(self):
        print('pause writing')
        print(self.transport.get_write_buffer_size())

    def resume_writing(self):
        print(self.transport.get_write_buffer_size())
        print('resume writing')




@add_state_features(AsyncTimeout)
class TimeoutMachine(HierarchicalAsyncMachine):
    pass



# UDP driver
class DatagramDriver(asyncio.DatagramProtocol):
    def __init__(self, queue, driver) -> None:
        super().__init__()
        self.queue = queue
        self.driver = driver
        
    def connection_made(self, transport) -> None:  # "Used by asyncio"
        self.transport = transport
        # self.driver.send_test_message(b"\n")


    def datagram_received(self, data, addr) -> None:  # "Main entrypoint for processing message"
        if not self.driver.client_address:
            self.driver.client_address = addr[0]
            self.driver.client_port = addr[1]
        # Here is where you would push message to whatever methods/classes you want.
        self.queue.put_nowait(data.decode())
        # asyncio.create_task(self.queue.put(data.decode()))
        





        # self.log_data.append(data)


class Mission:
    def __init__(self) -> None:
        self.states = [
            {'name': 'enRoute'},
            {'name': 'holdPosition'}
        ]
        # ['loading', 'dive', 'enRoute', 'holdPosition']
        self.machine = TimeoutMachine(model=self, states=self.states)

class Safety:
    def __init__(self) -> None:
        self.states = [
            {'name': 'sleeping'},
            {'name': 'active'},
            {'name': 'disabled'},
            {'name': 'disconnected'},
            {'name': 'sleepRequest'}
            ]
        self.machine = HierarchicalAsyncMachine(self, states=self.states, transitions=[])



class Driver:
    def __init__(self, queue_mega, queue_nano, transport_nano) -> None:


        self.log = logging.getLogger("normal")
        self.log_csv = logging.getLogger("csv")

        self.queue_mega = queue_mega
        self.queue_nano = queue_nano
        self.sensors = Sensors()
        # self.controller = Controller()
        self.pid_controller = PID(self.log)

        self.client_address = None
        self.client_port = None

        # self.mission = [5, 'E']
        self.mission = [500, 0]
        self.target_depth = None
        self.depth = None
        self.error = None

        self.time_off_duration = None

        self.hold_on_target = True

        self.condition = asyncio.Condition()    # for notify
        self.transport_nano = transport_nano    # output for nano

        pid_states =[
            {'name': "idle"},
            {'name': "calculating", 'on_enter': 'calculate_pid'},
            {'name': "starting", 'on_enter': 'ignite','timeout': 60, 'on_timeout': 'calculate_pid'},
            {'name': "timeOn", 'on_enter': 'timeOn'},
            {'name': "timeOff", 'on_enter': 'timeOff'}
        ]


        # self.states = ['PID', 'wait_for_pickup', 'emergency']
        self.states = [
            {'name': 'buffering', 'on_enter': 'check_sensor_buffer'},
            {'name': 'calibrating', 'on_enter': 'calibrate'},
            {'name': 'sensingWater', 'on_enter': 'sense_water'},
            {'name': 'executingTask', 'initial': 'loading', 'children': [
                {'name': 'loading', 'on_enter': 'set_next_target'},
                {'name': 'sendingDescendCommand', 'on_enter': 'send_descend_command'},
                {'name': 'sendingAscendCommand', 'on_enter': 'send_ascend_command'},
                {'name': 'waitingForDescendAcknowledge', 'on_enter': 'wait_for_descend_acknowledge'},
                {'name': 'waitingForAscendAcknowledge', 'on_enter': 'wait_for_ascend_acknowledge'},
                {'name': 'descending', 'on_enter': 'descend'},
                {'name': 'ascending', 'on_enter': 'ascend'},
                {'name': 'enRoute', 'initial': 'calculating', 'children': pid_states},
                # {'name': 'holdPosition', 'initial': 'idle', 'children': pid_states},
                {'name': 'surface', 'on_enter': 'surface'}
                ]
            },  # , 'timeout': 15, 'on_timeout': 'timeout_cb'
            {'name': 'emergency', 'on_enter': 'emergency'},
            {'name': 'pickup', 'on_enter': 'wait_for_pickup'}
            
            ]

        self.transitions = [
            ['resend_dive', 'waitingForDescendAcknowledge', 'sendingDescendCommand']
        ]


        # self.machine = HierarchicalAsyncMachine(self, states=self.states, transitions=self.transitions, ignore_invalid_triggers=True) # , initial='wait_for_sensor_buffer')
        self.machine = TimeoutMachine(self, states=self.states, transitions=self.transitions, ignore_invalid_triggers=True) # , initial='wait_for_sensor_buffer')
        self.machine.add_transition('hull_leak_emergency', '*', 'emergency', unless=['is_wait_for_pickup', 'is_emergency'])
        self.machine.add_transition('sensors_buffers_are_full', 'wait_for_sensor_buffer', 'calibrate_depth_sensors', conditions=['sensors_are_ready'])
        self.machine.add_transition('calibrate_sensors', ['calibrate_depth_sensors'], 'wait_for_water', conditions=['sensors_are_calibrated'], before=['sensors_are_calibrated'])
        # self.to_wait_for_sensor_buffer()




        # self.planner = MissionPlanner()

        

    async def consume_mega(self):
        # log_normal = logging.getLogger("normal")
        # log_csv = logging.getLogger("csv")
        
        while True:
            msg = await self.queue_mega.get()
            # print(f'consumed: {msg}')
            # log.debug(msg)
            # log_csv.critical("a,a,a,a,a")

            asyncio.create_task(self.handle_message(msg))
            # print(self.state)
            # await asyncio.sleep(0.1)

    async def consume_nano(self):
        # log_normal = logging.getLogger("normal")
        # log_csv = logging.getLogger("csv")
        
        while True:
            msg = await self.queue_nano.get()
            # print(f'consumed: {msg}')
            # log.debug(msg)
            # log_csv.critical("a,a,a,a,a")

            # asyncio.create_task(self.handle_message(msg))
            print(msg)
            serial_line = msg.strip().split(":")
            if len(serial_line) < 2: # skip if no message
                # print("Waiting for message from safety. Received: None")
                return
            header = serial_line[0]
            if header!='NN':
                return
            value = None
            try:
                value = int(float(serial_line[1]))
            except ValueError as e:
                self.log.error(f"Error parsing value {serial_line[1]} from safety")
                return  
            match value:
                case 1: pass  # ping acknowledge
                case 2: pass  # acknowledges weight was dropped on command
                case 3:
                    print('ping')
                    if self.depth < 1:
                        self.send_nano_message("N:1")
                case 4: 
                    # acknowledges weight was dropped due to over time
                    await self.to_emergency()
                case 5: pass  # safety went to sleep
                case 111: pass  # safety woke up (sleep was interrupted)

    def send_nano_message(self, message) -> None:
        # self.transport_nano.write(b'N:1\n')
        self.transport_nano.write(message.encode('utf-8'))



    def send_test_message(self, message) -> None:
        sock = socket.socket(socket.AF_INET,  # Internet
                            socket.SOCK_DGRAM)  # UDP
        sock.sendto(message.encode(), (self.client_address, self.client_port))
        print(f"message {message} sent to {self.client_address}  {self.client_port}")
        # sock.flush()
        # sock.close()

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
            case 'EL':  await self.sensors.leak_e_flag.add_sample(value)
            case 'BF':  await self.sensors.bladder_flag.add_sample(value)
            case 'PD':  
                await self.sensors.altimeter.add_sample(value)
                await self.handle_PD()
            case 'PC':  await self.sensors.altimeter.add_confidance(value)
            # case 'PU':  await self.sensors.pumpFlag.add_sample(value)
            case 'RPM': await self.sensors.rpm.add_sample(value)
            case 'PF':  await self.handle_pump_flag(value)
            case 'BV':  
                await self.sensors.bladderVolume.add_sample(value)
                await self.sensors.pressureController.calculate_avg()
                self.depth = self.sensors.pressureController.get_depth()
                if self.target_depth is not None and self.depth is not None:
                    self.error = self.target_depth - self.depth
                await self.log_sensors()
                async with self.condition:
                    # self.condition.notify()
                    self.condition.notify_all()   
            case 'FS' | 'S':  
                await self.sensors.full_surface_flag.add_sample(value)
                # await self.handle_full_surface_flag(value)
            case 'I' | 'IR':  await self.sensors.iridium_flag.add_sample(value)
            case 'D': await self.sensors.direction_flag.add_sample(value)

            case _ : pass # print(f'error {msg}')

    async def handle_pump_flag(self, value):
        await self.sensors.pumpFlag.add_sample(value)

    async def handle_full_surface_flag(self, value):
        fs_flag = self.sensors.full_surface_flag.getLast()

        match fs_flag:
            case 0: 
                print('dive or surface done')
                asyncio.create_task(self.to_executingTask_enRoute())

            case 1: 
                print('init full dive')
                asyncio.create_task(self.to_executingTask_descending())

            case 2: print('init full surface')

    async def handle_HL(self):
        # await self.to_PID()
        # print('handling hl')
        value = self.sensors.leak_h_flag.getLast()
        if value == 1:
            await self.hull_leak_emergency()

    async def handle_PD(self):
        # TODO: decide which comes first from arduino
        # assuming PC comes first

        # if cfg.app["disable_altimeter"]:
        #     return
        value = self.sensors.altimeter.getLast()
        confidance = self.sensors.altimeter.getConfidance()
        if confidance > 50:
            if 10 < value and value <= 20:
                while True:
                    self.log.warning("Yellow line! Ending mission!")
                # Alert
                # self.surface()
                self.current_state = State.END_TASK
            elif value <= 10:
                self.log.critical("Red line! Aborting mission!")
                # self.drop_weight()
                self.current_state = State.EMERGENCY

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

        res["PD"] = self.sensors.altimeter.getLast()
        res["PC"] = self.sensors.altimeter.getConfidance()
        res["HL"] = self.sensors.leak_h_flag.state   # self.sensors.leak_h_flag.getLast()
        res["EL"] = self.sensors.leak_e_flag.getLast()
        res["BF"] = self.sensors.bladder_flag.state   # self.sensors.bladder_flag.getLast()
        res["SF"] = self.sensors.full_surface_flag.getLast()
        res["PF"] = self.sensors.pumpFlag.state   # self.sensors.pumpFlag.getLast()
        res["BV"] = self.sensors.bladderVolume.getLast()
        res["rpm"] = self.sensors.rpm.getLast()
        # res['MissionState'] = self.state    # self.sensors.current_mission_state.name
        res['Setpoint'] = self.target_depth
        res['Error'] = self.error
        res['Depth'] = self.depth  # self.controller.current_depth
        res['avg_p'] = self.sensors.pressureController.avg
        res['direction'] = self.sensors.direction_flag.state
        res["State"] = self.state   # self.sensors.current_state.name
        # res['planner'] = self.planner.state

        self.fancy_log(res, False)
  
        # await asyncio.sleep(2)
        # asyncio.create_task(self.log_sensors())

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
        await asyncio.sleep(3)
        asyncio.create_task(self.to_buffering())

    async def timeout_cb(self):
        while True:
            print("timeout")

    async def sensors_are_ready(self):
        bypassSens = ["rpm"]
        for sensor in self.sensors.sensors:
            if sensor not in bypassSens and not self.sensors.sensors[sensor].isBufferFull(): # TODO: fix rpm and [and sensor!="PF"]
                self.log.warning(f"sensor {sensor} is not ready")
                return False
        bypassFlag = ["PF", "FS", "I"]
        bypassFlag.append('D')
        for flag in self.sensors.flags:
            if flag not in bypassFlag and not self.sensors.flags[flag].isBufferFull():
                self.log.warning(f"flag {flag} is not ready")
                return False

        return True      

    async def calibrate(self):
        print("calibrating")
        await asyncio.sleep(5)
        res = await self.sensors.pressureController.calibrate()
        if res == True:
            asyncio.create_task(self.to_sensingWater())
            return
        
        asyncio.create_task(self.to_calibrating())

    async def sense_water(self):
        print("waiting for water")
        await asyncio.sleep(5)
        res = await self.sensors.pressureController.senseWater()
        if res == True:
            asyncio.create_task(self.to_executingTask())
            # asyncio.create_task(self.planner.to_loading())
            # asyncio.create_task(self.to_executingTask_loading())

            return
        
        asyncio.create_task(self.to_sensingWater())

    async def set_next_target(self):
        print("set_next_target")

        if not self.mission:
            print("end mission")
            if self.sense_water:
                asyncio.create_task(self.to_pickup())
                return
            self.target_depth = 0
            asyncio.create_task(self.to_executingTask_surface())
            return

        next_depth = self.mission.pop(0)

        match next_depth:
            case 'E': 
                print('emegency')
                asyncio.create_task(self.to_emergency())
            case number if isinstance(number, int) or isinstance(number, float):
                print(f"got depth {number}")
                self.target_depth = number
                # self.error = self.target_depth - self.depth  # calculate again.  also on every bv

                
                if self.target_depth == 0:
                    asyncio.create_task(self.to_executingTask_surface())
                elif  self.target_depth - self.depth > 0:
                    asyncio.create_task(self.to_executingTask_sendingDescendCommand())
                else:
                    asyncio.create_task(self.to_executingTask_sendingAscendCommand())

            case _ : print(f"error {next_depth}")
  
    async def send_descend_command(self):
        print('sending descend command')
        # self.comm.write("S:1\n")
        self.send_test_message("S:1\n")
        await self.to_executingTask_waitingForDescendAcknowledge()
        # self.send_test_message("\n")

        await asyncio.sleep(10)
        print(self.state)
        if self.state == 'executingTask_waitingForDescendAcknowledge':
            print('descend command didn\'t reach')
            asyncio.create_task(self.to_executingTask_sendingDescendCommand())
            # asyncio.create_task(self.resend_dive())

    async def send_ascend_command(self):
        print('sending ascend command')
        # self.comm.write("S:1\n")
        self.send_test_message("S:2\n")
        await self.to_executingTask_waitingForAscendAcknowledge()
        # self.send_test_message("\n")

        await asyncio.sleep(10)
        print(self.state)
        if self.state == 'executingTask_waitingForAscendAcknowledge':
            print('ascend command didn\'t reach')
            asyncio.create_task(self.to_executingTask_sendingAscendCommand())
            # asyncio.create_task(self.resend_dive())

    async def wait_for_descend_acknowledge(self):
        print('waiting descend ack')
        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.full_surface_flag.getLast() == 1)
            print("recieved a descend flag - 1")
            asyncio.create_task(self.to_executingTask_descending())

    async def wait_for_ascend_acknowledge(self):
        print('waiting ascend ack')
        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.full_surface_flag.getLast() == 2)
            print("recieved a ascend flag - 2")
            asyncio.create_task(self.to_executingTask_ascending())
            
    async def descend(self):
        print('descending...')
        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.full_surface_flag.getLast() == 0)
            print("recieved: descend flag is over - 0")
            asyncio.create_task(self.to_executingTask_enRoute())
            asyncio.create_task(self.reach_goal())

    async def ascend(self):
        print('ascending...')
        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.full_surface_flag.getLast() == 0)
            print("recieved: ascend flag is over - 0")
            asyncio.create_task(self.to_executingTask_enRoute())
            asyncio.create_task(self.reach_goal())




    async def control(self):
        asyncio.create_task(self.hibernate())
        asyncio.create_task(self.reach_goal())
        
    async def hibernate(self):
        print('hibernate')
        async with self.condition:
            await self.condition.wait_for(lambda: abs(self.target_depth - self.sensors.pressureController.get_depth()) < 10)
            print("There's no running command now, exiting.")
            asyncio.create_task(self.to_executingTask_enRoute_calculating())
        pass

    async def reach_goal(self):
        print('hold on taget. timer started/reset')
        async with self.condition:
            await self.condition.wait_for(lambda: abs(self.target_depth - self.sensors.pressureController.get_depth()) < 1)
        print("hold position!")
        # self.hold_on_target = 1
        await asyncio.sleep(20)
        self.hold_on_target = False
        # await self.condition.wait_for(lambda: abs(self.state == '')
        # asyncio.create_task(self.to_executingTask_holdPosition_calculating())
        pass


        
    async def test_condition(self):
        async with self.condition:
            await self.condition.wait_for(lambda: isinstance(self.sensors.pressureController.get_depth(), float))
            print('condition is met!')

    async def calculate_pid(self):
        self.log.debug("calculating PID")
        if self.hold_on_target == False:
            asyncio.create_task(self.to_executingTask_loading())
            self.hold_on_target = True
            return
        print('PID')
        scalar = self.pid_controller.pid(self.error)
        direction, voltage, dc, time_on_duration, time_off_duration = self.pid_controller.unpack(scalar, self.error)  # this is the line.

        # await self.sensors.direction_flag.add_sample(direction)

        valid_pid = await self.check_pid_is_valid(direction, voltage, time_on_duration, time_off_duration)

        if valid_pid:
            if self.sensors.pumpFlag.state == 'on':
                self.log.critical("pump is already on!!!")
                return

            self.time_off_duration = time_off_duration

            # send pid
            self.send_test_message(f"V:{voltage}\n")
            self.send_test_message(f"D:{direction}\n")
            self.send_test_message(f"T:{time_on_duration}\n")

            asyncio.create_task(self.to_executingTask_enRoute_starting())  # FIXME: dangerous, put await?
            return


        await asyncio.sleep(1)
        # asyncio.create_task(self.to_executingTask_enRoute_calculating())
        asyncio.create_task(self.calculate_pid())

        # while True:
        #     print(self.sensors.bladder_flag.state)
        #     await asyncio.sleep(1)

    async def check_pid_is_valid(self, direction, voltage, time_on_duration, time_off_duration):

        if voltage == 0:
            return False

        if self.sensors.bladder_flag.state == 'full' and direction == 2:  # and self.sensors.direction_flag.state == 'up':
            self.log.info("Bladder is at max volume")
            return False
            
        if self.sensors.bladder_flag.state == 'empty' and direction == 1: # and self.sensors.direction_flag.state == 'down':
            self.log.info("Bladder is at min volume")
            return False

        self.log.info(f"sending PID - Voltage:{voltage}    direction:{direction}    timeOn:{time_on_duration}  timeOff:{time_off_duration}")
        return True


    async def ignite(self):
        self.log.info("waiting for pump to start")
        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.pumpFlag.is_on())
            print("pump truned on!") 
            asyncio.create_task(self.to_executingTask_enRoute_timeOn())


    async def timeOn(self):
        self.log.info("time on")
        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.pumpFlag.is_off())
            self.log.info("time on is done")
            asyncio.create_task(self.to_executingTask_enRoute_timeOff())      

    async def timeOff(self):
        self.log.info("time off")
        await asyncio.sleep(self.time_off_duration)
        self.log.info('time off is over!')
        asyncio.create_task(self.to_executingTask_enRoute_calculating())

    async def emergency(self):
        print('emergency')
        print('sending surface command')
        self.send_test_message("S:2\n")
        
        # TODO: drop weight

        # TODO: sense air
        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.pressureController.senseAir())

        self.log.info("we've reached the surface!")

        asyncio.create_task(self.to_pickup())

        # TODO: to_pickup

    async def sense_air(self):
        return self.sensors.pressureController.senseAir()


    # async def global_timer(self):
    #     pass

    # async def mission_timer(self):
    #     pass

    async def wait_for_pickup(self):
        self.log.info("Sending command to iridium")

        await self.sensors.iridium_flag.to_requesting()
        self.send_test_message("I:1\n")
        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.iridium_flag.is_idle())
        print('trasmition is over')
        await asyncio.sleep(20)
        asyncio.create_task(self.wait_for_pickup())


    async def surface(self):
        print('surfacing...')
        self.send_test_message("S:2\n")

        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.pressureController.senseAir())
            print("sensing air")
        await self.sensors.iridium_flag.to_requesting()
        self.send_test_message("I:1\n")
        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.iridium_flag.is_idle())
        print('trasmition is over')
        await asyncio.sleep(20)
        asyncio.create_task(self.to_pickup())





async def sequence(driver):
    loop = asyncio.get_event_loop()
    # check_buffer = driver.check_sensor_buffer()
    # loop.create_task(check_buffer)
    await driver.to_buffering()


async def reader(loop):
    transport, protocol = await serial_asyncio.create_serial_connection(loop, lambda: OutputProtocol(queue_nano), 'COM4', baudrate=115200)

    while True:
        await asyncio.sleep(2.0)
        # protocol.resume_reading()
        transport.write(b'N:1\n')

async def nano_driver(loop, queue_nano):
    transport, protocol = await serial_asyncio.create_serial_connection(loop, lambda: OutputProtocol(queue_nano), 'COM4', baudrate=115200)
    return transport



class Controller:
    def __init__(self) -> None:
        self.current_depth = None
        self.target_depth = None
        self.error = None
        self.states = ['wait_for_sensor_buffer', 'wait_for_safety','inflate_bladder', 'calibrate_depth_sensors', 'wait_for_water', 'exec_task', 'end_task', 'sleep_safety', 'wait_for_pickup', 'emergency', 'stop', 'enRoute']
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



    
    queue_mega = asyncio.Queue()

    # global queue_nano
    queue_nano = asyncio.Queue()

    loop = asyncio.new_event_loop()
    coro = serial_asyncio.create_serial_connection(loop, lambda: OutputProtocol(queue_nano), 'COM4', baudrate=115200)

    transport, protocol = loop.run_until_complete(coro)


    driver = Driver(queue_mega, queue_nano, transport)



    # loop = asyncio.get_event_loop()



    test_con = driver.test_condition()
    loop.create_task(test_con)



    # udp_driver = DatagramDriver(queue)
    # t = loop.create_datagram_endpoint(udp_driver, local_addr=('0.0.0.0', 12000), )

    t = loop.create_datagram_endpoint(lambda: DatagramDriver(queue_mega, driver), local_addr=('0.0.0.0', 12000), )
    loop.run_until_complete(t) # Server starts listening
    # loop.create_task(t)


    # loop.run_until_complete(driver.consume()) # Start writing messages (or running tests)
    c = driver.consume_mega()
    loop.create_task(c) # Start writing messages (or running tests)


    n = driver.consume_nano()
    loop.create_task(n)

    # loop.run_until_complete(driver.log_sensors())
    # l = driver.log_sensors()
    # loop.create_task(l)

    seq = sequence(driver)
    loop.create_task(seq)

    # driver.machine.to_wait_for_sensor_buffer()

    # loop.run_forever()

    # asyncio_serial
    # coro = serial_asyncio.create_serial_connection(loop, OutputProtocol, '/dev/ttyUSB0', baudrate=115200)
    # coro = serial_asyncio.create_serial_connection(loop, lambda: OutputProtocol(queue_nano), 'COM4', baudrate=115200)
    # loop.create_task(coro)

    # loop.create_task(reader(loop))

    # transport.write(b'N:1\n')


    

    loop.run_forever()

    loop.close()



if __name__=='__main__':
    main()
