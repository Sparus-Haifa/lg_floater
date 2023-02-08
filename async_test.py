import asyncio
from re import A
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

import json

import os

from enum import Enum, auto

# import cfg
import cfg.configuration as cfg


from datetime import datetime

import cfg.configuration as cfg


# serial driver
class OutputProtocol(asyncio.Protocol):
    def __init__(self, queue, name) -> None:
        super().__init__()
        self.queue = queue
        self.line = ""
        self.name = name
        self.log = logging.getLogger("normal")
        

    def connection_made(self, transport):
        self.transport = transport
        print('port opened', transport)
        transport.serial.rts = False  # You can manipulate Serial object via transport
        # transport.write(b'Hello, World!\n')  # Write serial data via transport

    def data_received(self, data):
        # print('data received', repr(data))
        self.line+=data.decode()
        # if b'\r\n' in data:
        if '\r\n' in self.line:
            tokens = self.line.split('\r\n')
            for token in tokens[:-1]:
                self.log.debug(f'{self.name}>RPi: ' + token)
                self.queue.put_nowait(token)
            self.line=tokens[-1]
        #     self.line = ''
        #     self.transport.close()
        # self.queue.put_nowait(data.decode())



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
            self.driver.client_address = "192.168.1.48" # addr[0]
            self.driver.client_port = cfg.app['simulation_udp_in_port'] # addr[1]
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


class Payload():
    def __init__(self, online):
        self.log = logging.getLogger("noraml")
        self.log.info("payload controller init")
        self.states = [
            {'name:': 'offline'},
            {'name': 'online'}
        ]
        self.machine = HierarchicalAsyncMachine(self, states=self.states, transitions=[], initial="offline")
        if online:
            self.to_online()

        

class Safety:
    def __init__(self, online, transport) -> None:
        self.log = logging.getLogger("normal")
        self.log.info("safety controller init")
        # print("safety init")
        self.transport = transport
        self.states = [
            {'name': 'sleeping', 'children': [
                {'name': 'weightFixed'},
                {'name': 'weightDropped'}
            ]},
            {'name': 'active', 'children': [
                {'name': 'weightFixed'},
                {'name': 'weightDropped'}
            ]},
            {'name': 'disabled'},
            {'name': 'disconnected'},
            {'name': 'enabled'},
            {'name': 'sleepRequest'},
            {'name': 'sleepInterrupted'}
            ]
        self.machine = HierarchicalAsyncMachine(self, states=self.states, transitions=[], initial="sleeping_weightFixed")
        
        if not online:
            # self.to_disabled()
            self.state="disabled"
            return
            
        self.to_enabled()
        # from gpio_controller_new import GPIOController
        import RPi.GPIO as GPIO
        self.RPI_TRIGGER_PIN = 14
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.RPI_TRIGGER_PIN, GPIO.OUT)
        # self.safety_trigger = GPIOController(RPI_TRIGGER_PIN)
        self.GPIO = GPIO
        # self.safety_trigger.high()
        self.high()
        # self.safety_trigger.low()
        # self.low()

    def high(self): # asleep
        self.log.debug('gpio high')
        if self.state=="disabled":
            self.log.error("safety is disabled")
            return
        # self.safety_trigger.high()
        self.GPIO.output(self.RPI_TRIGGER_PIN, self.GPIO.HIGH)

    def low(self): # awake
        self.log.debug('gpio low')
        if self.state=="disabled":
            self.log.error("safety is disabled")
            return
        # self.safety_trigger.low()
        self.GPIO.output(self.RPI_TRIGGER_PIN, self.GPIO.LOW)

    # def emergency(self):
    # # sending the command to drop the dropweight to saftey
    def drop_weight(self):
        # if self.drop_weight_command_sent:
            # self.log.debug("waiting for weight to drop")
        # else:
        # self.log.info("dropping weight")
            # if not self.disable_safety:
        self.send_nano_message("N:2")

            # self.drop_weight_command_sent = True

    def send_nano_message(self, message) -> None:
        # self.transport_nano.write(b'N:1\n')
        self.log.debug(f">NANO:{message}")
        if self.is_disabled():
            self.log.error("safety is disabled")
            return
        print(f"send_to_nano:{message}")
        self.transport.write(message.encode('utf-8'))



# enum of different emergency states
class Emergency(Enum):
    NONE = auto()
    HULL_LEAK = auto()
    ENGINE_LEAK = auto()
    PUMP_FAILURE = auto()
    SAFETY_NOT_RESPONDING = auto()
    ALTIMETER_YELLOW_LINE = auto()
    ALTIMETER_RED_LINE = auto()
    LOW_BATTERY = auto()
    SOFTWARE_ERROR = auto()
    SENSOR_ERROR = auto()

class Driver:
    def __init__(self, queue_mega, transport_mega, queue_nano, transport_nano, queue_cli, queue_payload, transport_payload, condition, condition_safety) -> None:


        # self.simulation = False  # use UDP or serial
        self.simulation = cfg.app["simulation"]  # use UDP or serial
        # logger = Logger(self.simulation)
        # self.log = logger.get_log()
        # self.log_csv = logger.get_csv_log()
        self.log = logging.getLogger("normal")
        self.log_csv = logging.getLogger("csv")
        # self.log.debug('init driver')
        self.log.info('init driver')
        # self.log_csv.warning("test")

        
        self.add_headers_to_csv = True  # add headers to csv file

        self.queue_mega = queue_mega
        self.queue_nano = queue_nano
        self.queue_cli = queue_cli
        self.queue_payload = queue_payload
        self.sensors = Sensors()
        # self.controller = Controller()
        self.pid_controller = PID(self.log)

        self.client_address = None
        self.client_port = None

        # self.mission = [5, 'E']
        # self.mission = [500, 0]
        # self.mission = [15, 0, 15, 0]
        # self.mission = [0.8, 0]
        # self.mission = [20, 0]
        self.mission = cfg.task['mission']

        self.target_depth = None
        self.depth = None
        self.error = None

        self.time_off_duration = None

        self.done_holding_target = True


        # self.condition = asyncio.Condition()    # for notify
        self.condition = condition
        self.condition_safety = condition_safety
        self.transport_nano = transport_nano    # output for nano
        self.transport_mega = transport_mega    # output for mega
        self.transport_payload = transport_payload  # output for payload

        self.test_mode = AsyncMachine(states=['off', 'on'], initial='on')


        self.running_tasks = []

        self.emergencies = []
        self.emergency_task = None # await asyncio.create_task(self.emergency())

        pid_states =[
            {'name': "idle"},
            {'name': "calculating", 'on_enter': 'launch_calculate_pid'},
            {'name': "starting", 'on_enter': 'launch_ignite','timeout': 60, 'on_timeout': 'calculate_pid'},
            {'name': "timeOn", 'on_enter': 'launch_timeOn'},
            {'name': "timeOff", 'on_enter': 'launch_timeOff'}
        ]



        # self.states = ['PID', 'wait_for_pickup', 'emergency']
        self.states = [
            {'name': 'stopped'},
            {'name': 'wakingSafety', 'on_enter': 'wakeup_safety'},
            {'name': 'sleepingSafety', 'on_enter': 'sleep_safety'},
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
                {'name': 'holdPosition', 'initial': 'idle', 'children': pid_states},
                {'name': 'surface', 'on_enter': 'surface'}
                ]
            },  # , 'timeout': 15, 'on_timeout': 'timeout_cb'
            {'name': 'emergency', 'children': [
                {'name': 'hullLeak'},
                {'name': 'engineLeak'},
                {'name': 'pumpFailure'},
                {'name': 'safetyNotResponding'},
                {'name': 'altimeter'},
                {'name': 'lowBattery'},
                {'name': 'softwareError'},
                {'name': 'sensorError'}
            ]},
            {'name': 'pickup', 'on_enter': 'wait_for_pickup'}
            
            ]

        self.transitions = [
            ['resend_dive', 'waitingForDescendAcknowledge', 'sendingDescendCommand']
        ]


        # self.machine = HierarchicalAsyncMachine(self, states=self.states, transitions=self.transitions, ignore_invalid_triggers=True) # , initial='wait_for_sensor_buffer')
        self.machine = TimeoutMachine(self, states=self.states, transitions=self.transitions, ignore_invalid_triggers=True) # , initial='wait_for_sensor_buffer')
        # self.machine.add_transition('hull_leak_emergency', '*', 'emergency', unless=['is_wait_for_pickup', 'is_emergency'])
        # self.machine.add_transition('sensors_buffers_are_full', 'wait_for_sensor_buffer', 'calibrate_depth_sensors', conditions=['sensors_are_ready'])
        # self.machine.add_transition('hold', 'executingTask_enRoute_', 'calibrate_depth_sensors', conditions=['sensors_are_ready'])

        # self.machine.add_transition('calibrate_sensors', ['calibrate_depth_sensors'], 'wait_for_water', conditions=['sensors_are_calibrated'], before=['sensors_are_calibrated'])
        # self.to_wait_for_sensor_buffer()
        # self.machine.add_transition('check_sensors', ['initial', 'buffering'], 'calibrating', before=['check_sensor_buffer'])


        # if not self.disable_safety:
        # self.safety = Safety()
            

        # self.planner = MissionPlanner()

    async def create_task(self, coro):
        task = asyncio.create_task(coro)
        self.running_tasks.append(task)
        return task


    async def consume_cli(self):
        while True:
            msg = await self.queue_cli.get()
            print(msg)
            serial_line = msg.strip().split(':')
            if len(serial_line)<2:
                return
            header, value = serial_line
            self.log.info(f"CLI:{header}:{value}")
            # match header:
            if header == 'water':
                self.log.info("water test")
                await asyncio.create_task(self.test_mode.to_on())
                asyncio.create_task(self.to_sensingWater())
        
            elif header == 'dive':
                self.log.info('dive command')
                await asyncio.create_task(self.test_mode.to_on())
                asyncio.create_task(self.to_executingTask_sendingDescendCommand())
            
            elif header == 'surface':
                self.log.info('surface command')
                await asyncio.create_task(self.test_mode.to_on())
                asyncio.create_task(self.to_executingTask_sendingAscendCommand())

            elif header == 'restart': 
                self.log.info('restarting')
                await asyncio.create_task(self.test_mode.to_off())
                task = asyncio.create_task(self.to_buffering())
                task.set_name('buffering')
                self.running_tasks.append(task)
            elif header == 'stop':
                print('stopping')
                self.log.info("stop") 
                await asyncio.create_task(self.test_mode.to_on())
                # stop all tasks
                await asyncio.create_task(self.stop_tasks())
                # restart emergency task
                self.log.info("stopping emergency task")
                if self.emergency_task is not None:
                    self.emergency_task.cancel()
                    self.log.info("awaiting emegency cancel")
                    # try:
                    #     await self.emergency_task
                    # except asyncio.CancelledError:
                    try:
                        await self.emergency_task
                    except asyncio.CancelledError:
                        pass
                        print(f"task emergency is cancelled now")
                    self.log.info("emergency task stopped")
                self.emergency_task = asyncio.create_task(self.emergency())
                # change state to stopped
                asyncio.create_task(self.to_stopped())
            
            elif header == 'mission': 
                self.mission = json.loads(value)
                asyncio.create_task(self.to_executingTask_loading())

            elif header == 'calibrate': 
                asyncio.create_task(self.to_calibrating())

            elif header == 'wakeup_safety': 
                # self.test_mode = True
                await asyncio.create_task(self.test_mode.to_on())
                asyncio.create_task(self.to_wakingSafety())

            elif header == 'sleep_safety': 
                # self.test_mode = True
                await asyncio.create_task(self.test_mode.to_on())
                asyncio.create_task(self.to_sleepingSafety())

            elif header == 'emergency':
                self.log.warning("CLI:emergency") 
                # self.test_mode = True
                # await asyncio.create_task(self.test_mode.to_on())
                self.emergencies.append(Emergency.NONE)
                # asyncio.create_task(self.to_emergency())
                # await asyncio.create_task(self.safety.drop_weight())
                # self.safety.drop_weight()

            elif header == "drop":
                self.log.info("drop")
                self.safety.drop_weight()
                

    async def consume_mega(self):
        # log_normal = logging.getLogger("normal")
        # log_csv = logging.getLogger("csv")
        self.log.info('init consume mega')
        # print("waiting for mega message")
        
        while True:
            msg = await self.queue_mega.get()
            # self.log.debug(f"MEGA:{msg}")
            # print(f'consumed: {msg}')
            # log.debug(msg)
            # log_csv.critical("a,a,a,a,a")
            lines = msg.splitlines()
            for line in lines:
                asyncio.create_task(self.handle_message(line)) # TODO: add await?
            # print(self.state)
            # await asyncio.sleep(0.1)

    async def consume_payload(self):
        self.log.info('init consume payload')
        while True:
            msg = await self.queue_payload.get()
            # self.log.debug(f"PAYLOAD:{msg}")
            # print("pl msg")
            # print(msg)
            lines = msg.splitlines()
            for line in lines:
                # asyncio.create_task(self.handle_message(line))
                # self.log.info(line)
                try:
                    header, value = line.split(':')
                    if header == 'PT' : await self.sensors.payload_flag.add_sample(value)
                except ValueError as e:
                    # print(f'{e}: [{line}]')
                    continue
                    # return
                if not value:
                    print('error')
                    self.log.error(f'Message received without a value: {line}')

    async def consume_nano(self):
        # log_normal = logging.getLogger("normal")
        # log_csv = logging.getLogger("csv")
        self.log.info("init consume nano")
        
        while True:
            msg = await self.queue_nano.get()
            # print(msg)
            # self.log.debug(f"NANO:{msg}")
            # print(f'consumed: {msg}')
            # log.debug(msg)
            # log_csv.critical("a,a,a,a,a")

            # asyncio.create_task(self.handle_message(msg))
            # print(msg)
            serial_line = msg.strip().split(":")
            if len(serial_line) < 2: # skip if no message
                # print("Waiting for message from safety. Received: None")
                continue
                # return
            header = serial_line[0]
            if header!='NN':
                continue
                # return
            value = None
            try:
                value = int(float(serial_line[1]))
            except ValueError as e:
                self.log.error(f"Error parsing value {serial_line[1]} from safety")
                continue
                # return  
            # match value:
            if value == 1:
                # ping acknowledge
                self.log.info('ping acknowledge')
                if self.safety.is_sleepInterrupted():
                    self.log.info('safety is active')
                    await self.safety.to_active_weightFixed()
                    if self.is_wakingSafety():
                        if self.test_mode.is_off():
                            await self.to_buffering()
                        else:
                            await self.to_stopped()
            elif value == 2:
                self.log.warning("safety acknowledges weight was dropped on command")
                asyncio.create_task(self.safety.to_active_weightDropped())
                self.safety.high()
            elif value == 3:
                self.log.info('safety ping')
                # if not self.depth or self.depth < 1:  # why?
                self.safety.send_nano_message("N:1")
                    # print('sent n:1')
            elif value == 4: 
                # acknowledges weight was dropped due to over time
                self.log.warning('weight was dropped due to over time!')
                # check if safety not responding is already detected
                if Emergency.SAFETY_NOT_RESPONDING in self.emergencies:
                    return
                self.emergencies.append(Emergency.SAFETY_NOT_RESPONDING)
                await self.to_emergency()
            elif value == 5:
                self.log.warning("safety received go to sleep command")
                pass  # safety received go to sleep command
  
            elif value == 111: 
                if not self.is_wakingSafety():
                    self.log.error("Safety woke up accidently!!")
                    print('waiting')
                    await sleep_safety()
                    print('waiting done')
                    continue

                
                self.log.info('safety woke up (sleep was interrupted). waiting on first ping...')
                await self.safety.to_sleepInterrupted()
                await asyncio.sleep(2)
                self.safety.send_nano_message('L:1')
            elif value == 222: 
                # self.safety
                self.log.info("222")
                print(222)
                self.safety.high() # keep safety asleep
                async with self.condition_safety:
                    self.condition_safety.notify_all() 
                self.log.info('safety went to sleep (sleep initiated)')
                if self.safety.is_active_weightDropped():
                    await self.safety.to_sleeping_weightDropped()
                else:
                    await self.safety.to_sleeping()

            else:
                print('unknown nano msg', msg)


            # print(self.safety.state)
            # print(self.state)


    def send_mega_message(self, message) -> None:
        self.log.debug(f">MEGA({self.client_address}:{self.client_port}):{message}")
        if not self.simulation:
            self.log.debug(f">MEGA:{message}")
            self.transport_mega.write(message.encode('utf-8'))
        else:
            self.log.debug(f">MEGA ({self.client_address}:{self.client_port}):{message}")
            sock = socket.socket(socket.AF_INET,  # Internet
                                socket.SOCK_DGRAM)  # UDP
            sock.sendto(message.encode(), (self.client_address, self.client_port))
            # print(f"message {message} sent to {self.client_address}  {self.client_port}")
            # sock.flush()
            # sock.close()


    async def wakeup_safety(self):
        # print('waking up safety')
        self.log.info('waking up safety')

        self.safety.low()
        # self.safety.send_nano_message()

    async def sleep_safety(self):
        print('sleeping safety')
        self.log.info('sleeping safety')
        self.safety.high()
        self.log.info("safety GPIO high")
        await asyncio.sleep(2)
        self.safety.send_nano_message("N:5")
        async with self.condition_safety:
            # await self.condition_safety.wait_for(lambda: self.sensors.full_surface_flag.getLast() == 1)
            await self.condition_safety.wait_for(lambda: self.safety.is_sleeping())
            print("condition met")
            
        # self.safety.send_nano_message()


    async def handle_message(self, msg):
        # self.log.debug(f"MEGA:{msg}")
        try:
            header, value = msg.split(':')
        except ValueError as e:
            print(f'{e}: [{msg}]')
            return
        if not value:
            print('error')
            self.log.error(f'Message received without a value: {msg}')

        # match header:
        if header in  ['TT1', 'TT2', 'BT1', 'BT2', 'AT']: await self.sensors.temperatureSensors[header].add_sample(value)
        if header in ['TP1', 'TP2', 'BP1', 'BP2', 'HP', 'AP']: await self.sensors.pressureSensors[header].add_sample(value)
        if header in ['X', 'Y', 'Z'] : await self.sensors.IMUSensors[header].add_sample(value)
        if header == 'HL':
            await self.sensors.leak_h_flag.add_sample(value)
            asyncio.create_task(self.handle_HL())
        if header == 'EL':
            await self.sensors.leak_e_flag.add_sample(value)
            asyncio.create_task(self.handle_EL())
        if header == 'BF':  await self.sensors.bladder_flag.add_sample(value)
        if header == 'PD':  
            await self.sensors.altimeter.add_sample(value)
            await self.handle_PD()
        if header == 'PC':  await self.sensors.altimeter.add_confidance(value)
        # if header == 'PU':  await self.sensors.pumpFlag.add_sample(value)
        if header == 'RPM': await self.sensors.rpm.add_sample(value)
        if header == 'PF':  await self.handle_pump_flag(value)
        if header == 'BV':  
            await self.sensors.bladderVolume.add_sample(value)
            await self.sensors.pressureController.calculate_avg()
            self.depth = self.sensors.pressureController.get_depth()
            if self.target_depth is not None and self.depth is not None:
                self.error = self.target_depth - self.depth
            await self.log_sensors()  # LOG SENSORS
        if header in ['FS', 'S']: 
            self.log.debug("surface/dive")
            await self.sensors.full_surface_flag.add_sample(value)
            # await self.handle_full_surface_flag(value)
        if header in ['I', 'IR']:  await self.sensors.iridium_flag.add_sample(value)
        # if header == 'D': await self.sensors.direction_flag.add_sample(value)


        else : pass # print(f'error {msg}')
        async with self.condition:
            # self.condition.notify()
            self.condition.notify_all()   
            # self.log.debug('notify')
            # print('notify')

    async def handle_pump_flag(self, value):
        await self.sensors.pumpFlag.add_sample(value)

    async def handle_full_surface_flag(self, value):
        fs_flag = self.sensors.full_surface_flag.getLast()

        # match fs_flag:
        if fs_flag== 0: 
            print('dive or surface done')
            asyncio.create_task(self.to_executingTask_enRoute())

        if fs_flag== 1: 
            print('init full dive')
            asyncio.create_task(self.to_executingTask_descending())

        if fs_flag== 2: print('init full surface')

    async def handle_HL(self):
        value = self.sensors.leak_h_flag.getLast()
        if value == 1:
            # print('HL!')
            # check if hull leak is already detected
            if Emergency.HULL_LEAK in self.emergencies: return
            self.log.critical('hull leak detected')
            # add emergency
            self.emergencies.append(Emergency.HULL_LEAK)
            # change state to emergency
            asyncio.create_task(self.to_emergency())

    async def handle_EL(self):
        value = self.sensors.leak_e_flag.getLast()
        if value == 1:
            # print('EL!')
            # check if engine leak is already detected
            if Emergency.ENGINE_LEAK in self.emergencies: return
            self.log.critical('engine leak detected')
            # add emergency
            self.emergencies.append(Emergency.ENGINE_LEAK)
            # change state to emergency
            asyncio.create_task(self.to_emergency())

    async def handle_PD(self):
        # TODO: decide which comes first from arduino
        # assuming PC comes first

        # if cfg.app["disable_altimeter"]:
        #     return
        # print('altimeter')
        # return

        value = self.sensors.altimeter.getLast()
        confidance = self.sensors.altimeter.getConfidance()
        if self.depth is None or self.is_stopped():
            return
        if False and confidance > 50:
            if 10 < value and value <= 20:
                # while True:
                # Alert
                # self.surface()
                # self.current_state = State.END_TASK
                # if self.state != "emergency":
                #     await self.to_emergency()
                if Emergency.ALTIMETER_YELLOW_LINE in self.emergencies: return
                self.log.critical("Yellow line! Ending mission!")
                self.emergencies.append(Emergency.ALTIMETER_YELLOW_LINE)
                asyncio.create_task(self.to_emergency())

            elif value <= 10:
                if Emergency.ALTIMETER_RED_LINE in self.emergencies: return
                self.log.critical("Red line! Aborting mission!")
                self.emergencies.append(Emergency.ALTIMETER_RED_LINE)
                asyncio.create_task(self.to_emergency())
                # self.drop_weight()
                # self.current_state = State.EMERGENCY  # TODO: fix
                # if self.state != "emergency":
                #     await self.to_emergency()

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
            if self.add_headers_to_csv: # Add headers
                self.log_csv.critical(",".join(headers))
                self.add_headers_to_csv = False
            self.log.critical("".join(headers))
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
            self.log_csv.critical(",".join(values))
            self.log.critical("".join(values))
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
        res['Voltage'] = self.sensors.voltage_sensor.getLast()
        res["State"] = self.state   # self.sensors.current_state.name
        res["Safety"] = self.safety.state   # 
        # res['planner'] = self.planner.state
        res['Payload'] = self.sensors.payload_flag.getLast()
        res['TestMode'] = self.test_mode.state
        

        self.fancy_log(res, True)
  
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
            if self.test_mode.is_off():
                task = asyncio.create_task(self.to_calibrating())
                task.set_name('to_calibrating')
                self.running_tasks.append(task)
                return
            if self.test_mode.is_on():
                asyncio.create_task(self.to_stopped())
                return
        await asyncio.sleep(3)
        task = asyncio.create_task(self.check_sensor_buffer())
        self.running_tasks.append(task)

    async def timeout_cb(self):
        while True:
            print("timeout")

    async def sensors_are_ready(self):
        bypassSens = ["rpm", "Voltage"]
        for sensor in self.sensors.sensors:
            if sensor not in bypassSens and not self.sensors.sensors[sensor].isBufferFull(): # TODO: fix rpm and [and sensor!="PF"]
                self.log.warning(f"sensor {sensor} is not ready")
                return False
        bypassFlag = ["PF", "FS", "I", "PT"]
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
        # return if state is not calibrating
        if self.state != 'calibrating':
            return
        if res == True:
            if self.test_mode.is_on():
                asyncio.create_task(self.to_stopped())
                return
            if self.test_mode.is_off():
                task = asyncio.create_task(self.to_sensingWater())
                self.running_tasks.append(task)
                return
        
        task = asyncio.create_task(self.to_calibrating())
        self.running_tasks.append(task)

    async def sense_water(self):
        if self.state == 'stopped':
            return
        print("waiting for water")
        await asyncio.sleep(5)
        # retry if state is not sensing water
        if self.state != 'sensingWater':
            return
        res = await self.sensors.pressureController.senseWater()
        if res == True:
            if self.test_mode.is_on():
                asyncio.create_task(self.to_stopped())
                return
            task = asyncio.create_task(self.to_executingTask())
            self.running_tasks.append(task)
            return
        
        task = asyncio.create_task(self.sense_water())
        self.running_tasks.append(task)

    async def set_next_target(self):
        if self.depth is None:
            # await asyncio.create_task(self.to_calibrating())
            self.log.error('no calibration')
            return


        self.log.info("setting next target")
        if not self.mission:
            self.log.info("ending mission")
            if self.sense_water:
                task = asyncio.create_task(self.to_pickup())
                self.running_tasks.append(task)
                return
            self.target_depth = 0
            task = asyncio.create_task(self.to_executingTask_surface())
            self.running_tasks.append(task)
            return

        next_depth = self.mission.pop(0)
        self.done_holding_target = False # reset hold on target
        self.holding_on_target = False # am i currently on "holding on target state/timer"


        # match next_depth:
        if next_depth == 'E': 
            self.log.info('emegency test - next depth')
            # add emergency test to emergencies list
            self.emergencies.append(Emergency.NONE)
            # change state to emergency
            asyncio.create_task(self.to_emergency())
        
        # check if next_depth is a number
        if isinstance(next_depth, int) or isinstance(next_depth, float):
            self.log.info(f"got depth {next_depth}")
            self.target_depth = next_depth
            # self.error = self.target_depth - self.depth  # calculate again.  also on every bv

            
            if self.target_depth == 0:
                task = asyncio.create_task(self.to_executingTask_surface())
                self.running_tasks.append(task)
            elif  self.target_depth - self.depth > 0:
                task = asyncio.create_task(self.to_executingTask_sendingDescendCommand())
                self.running_tasks.append(task)
            else:
                task = asyncio.create_task(self.to_executingTask_sendingAscendCommand())
                self.running_tasks.append(task)

        else : self.log.critical(f"error {next_depth}")
  
    async def send_descend_command(self):
        self.log.info('sending descend command')
        # self.comm.write("S:1\n")
        self.send_mega_message("S:1\n")
        task = asyncio.create_task(self.to_executingTask_waitingForDescendAcknowledge())
        self.running_tasks.append(task)

        await asyncio.sleep(10)
        if self.state == 'executingTask_waitingForDescendAcknowledge':
            self.log.error('descend command didn\'t reach')
            # asyncio.create_task(self.to_executingTask_sendingDescendCommand())
            task = asyncio.create_task(self.send_descend_command())  # FIXME
            self.running_tasks.append(task)
            # asyncio.create_task(self.resend_dive())

    async def send_ascend_command(self):
        self.log.info('sending ascend command')
        # self.comm.write("S:1\n")
        self.send_mega_message("S:2\n")
        task = asyncio.create_task(self.to_executingTask_waitingForAscendAcknowledge())
        self.running_tasks.append(task)

        # watchdog
        await asyncio.sleep(10)
        print(self.state)
        if self.state == 'executingTask_waitingForAscendAcknowledge':
            self.log.error('ascend command didn\'t reach')
            task = asyncio.create_task(self.to_executingTask_sendingAscendCommand())
            self.running_tasks.append(task)

    async def wait_for_descend_acknowledge(self):
        self.log.info('waiting descend ack')
        # wait for full surface flag to be 1
        # while self.sensors.full_surface_flag.getLast() != 1:
        #     print(self.state)
        #     await asyncio.sleep(1)
        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.full_surface_flag.getLast() == 1)
            self.log.debug("recieved a descend flag - 1")
            self.log.debug("self.sensors.full_surface_flag.getLast() == " + str(self.sensors.full_surface_flag.getLast()))

            await self.sensors.direction_flag.add_sample(1)
            await self.sensors.voltage_sensor.add_sample(100)
            

            if self.test_mode.is_on():
                asyncio.create_task(self.to_stopped())
                return

            # if executing task
            task = asyncio.create_task(self.to_executingTask_descending())
            self.running_tasks.append(task)



    async def wait_for_ascend_acknowledge(self):
        self.log.info('waiting ascend ack')
        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.full_surface_flag.getLast() == 2)
            self.log.debug("recieved a ascend flag - 2")

            await self.sensors.direction_flag.add_sample(2)
            await self.sensors.voltage_sensor.add_sample(100)


            if self.test_mode.is_on():
                asyncio.create_task(self.to_stopped())
                return

            task = asyncio.create_task(self.to_executingTask_ascending())
            self.running_tasks.append(task)
            
    async def descend(self):
        self.log.info('descending...')
        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.full_surface_flag.getLast() == 0)
            self.log.debug("recieved: descend flag is over - 0")
            await self.sensors.direction_flag.add_sample(0)
            await self.sensors.voltage_sensor.add_sample(0)
            task = asyncio.create_task(self.to_executingTask_enRoute())
            self.running_tasks.append(task)
            task = asyncio.create_task(self.reach_goal())
            self.running_tasks.append(task)


    async def ascend(self):
        self.log.info('ascending...')
        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.full_surface_flag.getLast() == 0)
            self.log.debug("recieved: ascend flag is over - 0")
            await self.sensors.direction_flag.add_sample(0)
            await self.sensors.voltage_sensor.add_sample(0)
            task = asyncio.create_task(self.to_executingTask_enRoute())
            self.running_tasks.append(task)
            task = asyncio.create_task(self.reach_goal())
            self.running_tasks.append(task)




    # async def control(self):
    #     asyncio.create_task(self.hibernate())
    #     asyncio.create_task(self.reach_goal())
        
    # async def hibernate(self):
    #     print('hibernate')
    #     async with self.condition:
    #         await self.condition.wait_for(lambda: abs(self.target_depth - self.sensors.pressureController.get_depth()) < 10)
    #         print("There's no running command now, exiting.")
    #         asyncio.create_task(self.to_executingTask_enRoute_calculating())
    #     pass

    async def reach_goal(self):
        self.log.info("en route to goal")
        async with self.condition:
            await self.condition.wait_for(lambda: abs(self.target_depth - self.sensors.pressureController.get_depth()) < 0.1)
            self.log.debug('abs(self.target_depth - self.sensors.pressureController.get_depth()) < 0.1')
            self.log.debug(str(self.target_depth) +' - ' + str(self.sensors.pressureController.get_depth()) +' < 0.1')
        self.log.info('target reached! holding on taget! timer started/reset')
        # self.log.info("holding position!")
        self.holding_on_target = True

        # await self.to_executingTask_enRoute_calculating
        # self.hold_on_target = 1
        # self.done_holding_target = False
        await asyncio.sleep(120)
        self.done_holding_target = True
        self.holding_on_target = False
        # await self.condition.wait_for(lambda: abs(self.state == '')
        # asyncio.create_task(self.to_executingTask_holdPosition_calculating())
        pass


        
    async def test_condition(self):
        async with self.condition:
            await self.condition.wait_for(lambda: isinstance(self.sensors.pressureController.get_depth(), float))
            print('condition is met!')


    async def launch_calculate_pid(self):
        self.log.info('launching calculate_pid')
        task = asyncio.create_task(self.calculate_pid())
        self.running_tasks.append(task)


    async def launch_ignite(self):
        self.log.info('launching ignite')
        task = asyncio.create_task(self.ignite())
        self.running_tasks.append(task)

        
    async def launch_timeOn(self):
        self.log.info('launching timeOn')
        task = asyncio.create_task(self.timeOn())
        self.running_tasks.append(task)


    async def launch_timeOff(self):
        self.log.info('launching timeOff')
        task = asyncio.create_task(self.timeOff())
        self.running_tasks.append(task)
        

    async def calculate_pid(self):
        self.log.debug("calculating PID")
        if self.done_holding_target == True:
            self.log.info("done holding on target - load new target")
            self.done_holding_target = False
            task = asyncio.create_task(self.to_executingTask_loading())
            self.running_tasks.append(task)
            return
        self.log.info('Calculating PID')
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
            self.send_mega_message(f"V:{voltage}\n")
            self.send_mega_message(f"D:{direction}\n")
            self.send_mega_message(f"T:{time_on_duration}\n")

            # log pid
            await self.sensors.direction_flag.add_sample(direction)
            await self.sensors.voltage_sensor.add_sample(voltage)

            if self.holding_on_target:
                task = asyncio.create_task(self.to_executingTask_holdPosition_starting())  # FIXME: dangerous, put await?
                self.running_tasks.append(task)

            else:
                task = asyncio.create_task(self.to_executingTask_enRoute_starting())  # FIXME: dangerous, put await?
                self.running_tasks.append(task)
            return
        
        # zero volate and direction flags
        await self.sensors.direction_flag.add_sample(0)
        await self.sensors.voltage_sensor.add_sample(0)

        # just setting the state
        if self.holding_on_target:
            task = asyncio.create_task(self.to_executingTask_holdPosition_calculating())
            self.running_tasks.append(task)
        else:
            task = asyncio.create_task(self.to_executingTask_enRoute_calculating())
            self.running_tasks.append(task)

        # await asyncio.sleep(1)
        # calling state function on every iteration
        async with self.condition:
            await self.condition.wait()
            # await asyncio.sleep(0.1)
            task = asyncio.create_task(self.calculate_pid())
            self.running_tasks.append(task)

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

        # PID is vaild!
        self.log.info(f"sending PID - Voltage:{voltage:.4f}    direction:{direction:.4f}    timeOn:{time_on_duration:.4f}  timeOff:{time_off_duration:.4f}")
        return True


    async def ignite(self):
        self.log.info("waiting for pump to start")
        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.pumpFlag.is_on())
            print("pump truned on!")
            
            if self.holding_on_target:
                task = asyncio.create_task(self.to_executingTask_holdPosition_timeOn())
                self.running_tasks.append(task)
            else:
                task = asyncio.create_task(self.to_executingTask_enRoute_timeOn())
                self.running_tasks.append(task)


    async def timeOn(self):
        self.log.info("time on")
        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.pumpFlag.is_off())
            self.log.info("time on is done")
            if self.holding_on_target:
                task = asyncio.create_task(self.to_executingTask_holdPosition_timeOff())      
                self.running_tasks.append(task)
            else:
                task = asyncio.create_task(self.to_executingTask_enRoute_timeOff())      
                self.running_tasks.append(task)

    async def timeOff(self):
        self.log.info("time off")
        # zero volate and direction flags
        await self.sensors.direction_flag.add_sample(0)
        await self.sensors.voltage_sensor.add_sample(0)

        await asyncio.sleep(self.time_off_duration)
        self.log.info('time off is over!')
        if self.holding_on_target:
            task = asyncio.create_task(self.to_executingTask_holdPosition_calculating())
            self.running_tasks.append(task)
        else:
            task = asyncio.create_task(self.to_executingTask_enRoute_calculating())
            self.running_tasks.append(task)

    # stop all tasks
    async def stop_tasks(self):
        self.log.info("stopping all tasks")
        # print(self.running_tasks)
        for task in self.running_tasks:
            print(task)
            print(f"{task.get_coro().__qualname__} , Finished: {task.done()}")
            # if task.get_coro().__qualname__ == 'HierarchicalAsyncMachine.trigger_event':
            if task.done():
                continue
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                print(f"task {task.get_name()} is cancelled now")
        self.log.info("all tasks stopped")
        
        # print(self.running_tasks)
        self.running_tasks = []
        

        # if pump is on, wait for it to turn off
        if self.sensors.pumpFlag.state == 'on':
            self.log.info("waiting for pump to turn off")
            async with self.condition:
                await self.condition.wait_for(lambda: self.sensors.pumpFlag.is_off())
                self.log.info("pump turned off")

        # self.running_tasks = []

    async def emergency(self):
        # continuesly check if there is an emergency
        self.log.info("emergency handler started")
        task = asyncio.current_task()
        while not self.emergencies:
            self.log.info("emergency online")
            if task.cancelled():
                print("Task was cancelled")
                return
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                print("Task was cancelled")
                return




        self.log.critical('emergency detected!')
        # change state to emergency

        await asyncio.create_task(self.to_emergency())

        # stop all tasks
        self.log.info("stopping all tasks from emergency handler")
        # await self.stop_tasks()
        await asyncio.create_task(self.stop_tasks())


        await asyncio.create_task(self.to_emergency())




        critical_emergencies =  [Emergency.ALTIMETER_RED_LINE, Emergency.ENGINE_LEAK, Emergency.PUMP_FAILURE, Emergency.HULL_LEAK]

        # check if we should drop the weight
        # if [Emergency.ALTIMETER_RED_LINE, Emergency.ENGINE_LEAK, Emergency.PUMP_FAILURE, Emergency.HULL_LEAK] in self.emergencies:
        if any(emergency in critical_emergencies for emergency in self.emergencies):
            # drop the weight
            self.safety.drop_weight()
            self.log.critical('sending drop weight command')


        # check if pump didn't fail
        if not self.sensors.pumpFlag.state == 'failure':
            self.log.info('sending surface command')
            self.send_mega_message("S:2\n")
        
                    

        # check if we've reached the surface every 5 seconds with a timeout of 30 seconds
        self.log.info("waiting for surface")
        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.pressureController.senseAir())# TODO: add timeout, if depth isn't changing for 5 seconds, then we are on the surface or stuck
            
            self.log.info("surface reached")

        self.log.info("we've reached the surface!")

        # start the pickup task without changing the state
        task = asyncio.create_task(self.wait_for_pickup())
        self.running_tasks.append(task)

        # periodically check if we should drop the weight
        while True:
            # print(self.emergencies)
            # if [Emergency.ALTIMETER_RED_LINE, Emergency.ENGINE_LEAK, Emergency.PUMP_FAILURE, Emergency.HULL_LEAK] in self.emergencies:
            if any(emergency in critical_emergencies for emergency in self.emergencies):
                # drop the weight
                self.log.critical('sending drop weight command')
                self.safety.drop_weight()
                # self.send_mega_message("S:3\n")
                return
            await asyncio.sleep(1)


    async def sense_air(self):
        return self.sensors.pressureController.senseAir()


    # async def global_timer(self):
    #     pass

    # async def mission_timer(self):
    #     pass

    async def wait_for_pickup(self):
        self.log.info("Sending command to iridium")
        while True:
            self.log.info("waiting for iridium to be ready")
            await self.sensors.iridium_flag.to_requesting()
            self.log.info("iridium is ready")
            self.log.info("sending iridium message")
            self.send_mega_message("I:1\n")
            async with self.condition:
                await self.condition.wait_for(lambda: self.sensors.iridium_flag.is_idle())
            self.log.info("iridium message sent")
            await asyncio.sleep(60)
            # task = asyncio.create_task(self.wait_for_pickup())
            # self.running_tasks.append(task)


    async def surface(self):
        print('surfacing...')
        # Send command
        self.send_mega_message("S:2\n")
        # wait until you sense air
        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.pressureController.senseAir())
            print("sensing air")
        # Send a single iridium message
        await self.sensors.iridium_flag.to_requesting()
        self.send_mega_message("I:1\n")
        # Wait for message to be sent
        async with self.condition:
            await self.condition.wait_for(lambda: self.sensors.iridium_flag.is_idle())
        print('trasmition is over')
        await asyncio.sleep(20)
        # asyncio.create_task(self.to_pickup())
        task = asyncio.create_task(self.to_executingTask_loading())
        self.running_tasks.append(task)





async def sequence(driver):
    return
    loop = asyncio.get_event_loop()
    # check_buffer = driver.check_sensor_buffer()
    # loop.create_task(check_buffer)

    if driver.test_mode.is_off():
        await driver.to_buffering()
        # await driver.to_wakingSafety()
        print('try to move to state waking safety')


    # await driver.check_sensors()


# async def reader(loop):
#     transport, protocol = await serial_asyncio.create_serial_connection(loop, lambda: OutputProtocol(queue_nano), 'COM4', baudrate=115200)

#     while True:
#         await asyncio.sleep(2.0)
#         # protocol.resume_reading()
#         transport.write(b'N:1\n')

# async def nano_driver(loop, queue_nano):
#     transport, protocol = await serial_asyncio.create_serial_connection(loop, lambda: OutputProtocol(queue_nano), 'COM4', baudrate=115200)
#     return transport



class Controller:
    def __init__(self) -> None:
        self.current_depth = None
        self.target_depth = None
        self.error = None
        self.states = ['wait_for_sensor_buffer', 'wait_for_safety','inflate_bladder', 'calibrate_depth_sensors', 'wait_for_water', 'exec_task', 'end_task', 'sleep_safety', 'wait_for_pickup', 'emergency', 'stop', 'enRoute']
        self.machine = HierarchicalAsyncMachine(self, states=self.states, transitions=[])





def log_exceptions(loop, context):
    """
    Exception handler
    """
        # first, handle with default handler
    exception = context.get('exception')
    loop.default_exception_handler(context)
    msg = context.get("exception", context["message"])
    if isinstance(exception, ZeroDivisionError):
        print("In exception handler.")
    logger = logging.getLogger("normal")
    # logger.error(f"Caught exception: {msg}")
    print(f"Caught exception: {msg}")
    logger.exception("Unhandled exception")
    # logger.exception(context)


def main():
    # logger = Logger(False)

    # logging.basicConfig()
    # logging.root.setLevel(logging.NOTSET)
    # logging.getLogger('transitions').setLevel(logging.WARNING)

    # global log
    # log = logging.getLogger("normal")
    # log.setLevel(logging.NOTSET)
    # global log_csv
    # log_csv = logging.getLogger("csv")

    # simulation = False
    SIMULATION = cfg.app['simulation']
    # client_address = cfg.app['simulator_ip_address']
    client_port = cfg.app['simulation_udp_port']
    logger = Logger(SIMULATION)
    log = logging.getLogger("normal")

    log.info(f"init log at {logger.path}")


    




    loop = asyncio.new_event_loop()

    loop.set_exception_handler(log_exceptions)
    
    # queue_mega = asyncio.Queue(loop=loop)
    # queue_nano = asyncio.Queue(loop=loop)
    # queue_cli = asyncio.Queue(loop=loop)
    # queue_payload = asyncio.Queue(loop=loop)

    queue_mega = asyncio.Queue()
    queue_nano = asyncio.Queue()
    queue_cli = asyncio.Queue()
    queue_payload = asyncio.Queue()

    corutines = []


    def listPorts():
        """!
        @brief Provide a list of names of serial ports that can be opened as well as a
        a list of Arduino models.
        @return A tuple of the port list and a corresponding list of device descriptions
        """

        # import serial
        import serial.tools.list_ports

        ports = list(  serial.tools.list_ports.comports() )

        serial_ports = {}
        for port in ports:
            # print(port, port.description)
            # if not port.description.startswith( "Arduino" ):
            #     # correct for the somewhat questionable design choice for the USB
            #     # description of the Arduino Uno
            #     if port.manufacturer is not None:
            #         if port.manufacturer.startswith( "Arduino" ) and \
            #         port.device.endswith( port.description ):
            #             port.description = "Arduino Uno"
            #         else:
            #             continue
            #     else:
            #         continue
            # if port.device:
            #     resultPorts.append( port.device )
            #     descriptions.append( str( port.description ) )
            if port.description.startswith("FT232R"):
                serial_ports['nano']=port.device
            elif port.description.startswith("USB"):
                serial_ports['payload']=port.device
            elif port.description.startswith("ttyACM0"):
                serial_ports['mega']=port.device


        return (serial_ports)

    serial_ports = listPorts()
    print(serial_ports)
    # listPorts()

    # return


    # Nano
    if not SIMULATION and 'nano' in serial_ports:
        # coro_nano = serial_asyncio.create_serial_connection(loop, lambda: OutputProtocol(queue_nano), 'COM4', baudrate=115200)
        coro_nano = serial_asyncio.create_serial_connection(loop, lambda: OutputProtocol(queue_nano, "nano"), serial_ports['nano'], baudrate=115200)
        transport_nano, protocol = loop.run_until_complete(coro_nano)
        corutines.append(coro_nano)
        safety = Safety(online = True, transport = transport_nano)
    else:
        transport_nano = None
        safety = Safety(online = False, transport = transport_nano)

    # init mega serial connection

    if not SIMULATION:
        coro_mega = serial_asyncio.create_serial_connection(loop, lambda: OutputProtocol(queue_mega, "mega"), serial_ports['mega'], baudrate=115200)
        transport_mega, protocol = loop.run_until_complete(coro_mega)
        corutines.append(coro_mega)
    else:
        transport_mega = None

    # Payload_imu serial connection
    
    if not SIMULATION and 'payload' in serial_ports:
        log.info("payload connected")
        coro_payload = serial_asyncio.create_serial_connection(loop, lambda: OutputProtocol(queue_payload, 'payload'), serial_ports['payload'], baudrate=115200)
        transport_payload, protocol = loop.run_until_complete(coro_payload)
        corutines.append(coro_payload)
    else:
        transport_payload = None


    # condition = asyncio.Condition(loop=loop)    # for notify
    # condition_safety = asyncio.Condition(loop=loop)    # for notify
    # condition = asyncio.Condition(loop=loop)    # for notify
    # condition_safety = asyncio.Condition(loop=loop)    # for notify

    condition = asyncio.Condition()    # for notify
    condition_safety = asyncio.Condition()    # for notify
    condition = asyncio.Condition()    # for notify
    condition_safety = asyncio.Condition()    # for notify


    driver = Driver(queue_mega, transport_mega, queue_nano, transport_nano, queue_cli, queue_payload, transport_payload, condition, condition_safety)


    # if SIMULATION:
    #     driver.client_address = client_address
    #     driver.client_port = client_port

    # SAFETY
    # if not self.disable_safety:
    driver.safety = safety





    # loop = asyncio.get_event_loop()




    # test_con = driver.test_condition()
    # loop.create_task(test_con)



    # udp_driver = DatagramDriver(queue)
    # t = loop.create_datagram_endpoint(udp_driver, local_addr=('0.0.0.0', 12000), )

    # Simulation - Listen to UDP/IP
    udp_mega_corutine = loop.create_datagram_endpoint(lambda: DatagramDriver(queue_mega, driver), local_addr=('0.0.0.0', cfg.app['simulation_udp_out_port']), )
    loop.run_until_complete(udp_mega_corutine) # Server starts listening
    corutines.append(udp_mega_corutine)
    
    # loop.create_task(t)
    cli_coro = loop.create_datagram_endpoint(lambda: DatagramDriver(queue_cli, driver), local_addr=('0.0.0.0', 5000), )
    loop.run_until_complete(cli_coro)
    corutines.append(cli_coro)


    # loop.run_until_complete(driver.consume()) # Start writing messages (or running tests)

    
    consume_mega_corutine = loop.create_task(driver.consume_mega()) # Start writing messages (or running tests)
    corutines.append(consume_mega_corutine)
    
    consume_nano_corutine = loop.create_task(driver.consume_nano())
    corutines.append(consume_nano_corutine)

    consume_cli_corutine = loop.create_task(driver.consume_cli())
    corutines.append(consume_cli_corutine)

    consume_payload_corutine = loop.create_task(driver.consume_payload())
    corutines.append(consume_payload_corutine)

    # start emergency task
    emergency_corutine = loop.create_task(driver.emergency())
    driver.emergency_task = emergency_corutine
    corutines.append(emergency_corutine)

    driver.emergency_task = emergency_corutine
    corutines.append(emergency_corutine)





    # loop.run_until_complete(driver.log_sensors())
    # l = driver.log_sensors()
    # loop.create_task(l)

    seq = sequence(driver)
    seq_corutine =  loop.create_task(seq)
    corutines.append(seq_corutine)


    # driver.machine.to_wait_for_sensor_buffer()

    # loop.run_forever()

    # asyncio_serial
    # coro = serial_asyncio.create_serial_connection(loop, OutputProtocol, '/dev/ttyUSB0', baudrate=115200)
    # coro = serial_asyncio.create_serial_connection(loop, lambda: OutputProtocol(queue_nano), 'COM4', baudrate=115200)
    # loop.create_task(coro)

    # loop.create_task(reader(loop))

    # transport.write(b'N:1\n')


    
    try:
        loop.run_forever()
    except KeyboardInterrupt as e:
        # log.exception(e)
        log.info('graceful shutdown')
        log.info('disabling safety. please wait...')
        if driver.safety is not None:
            pass
            # # await self.safety.to_sleeping()
            # loop = asyncio.new_event_loop()
            # c = driver.safety.to_sleeping()
            # loop.create_task(c)
            # safety = Safety()
            import time
            # safety.high()
            # time.sleep(1)
            # safety.low()
            # time.sleep(1)
            # safety.high()
            # time.sleep(1)
            # safety.low()
            # time.sleep(1)
            # safety.high()
            # driver.send_nano_message("N:5")
            if not driver.safety.is_sleeping(allow_substates=True) and not driver.safety.is_disabled():
                loop.run_until_complete(driver.sleep_safety())
                time.sleep(2)
        """Cleanup tasks tied to the service's shutdown."""
        # logging.info(f"Received exit signal {signal.name}...")
        log.info("Closing database connections")
        log.info("Nacking outstanding messages")
        tasks = [t for t in asyncio.all_tasks(loop) if t is not
                asyncio.current_task()]
        
        # # tasks = corutines

        [task.cancel() for task in tasks]

            # loop.run_forever()
        # tasks = Task.all_tasks()
        for t in [t for t in tasks if not (t.done() or t.cancelled())]:
            # give canceled tasks the last chance to run
            loop.run_until_complete(t)

        log.info(f"Cancelling {len(tasks)} outstanding tasks")
        asyncio.gather(*tasks, return_exceptions=True)
        log.info(f"Flushing metrics")
            # loop.stop()
    except AttributeError as e:
        log.exception(e)

    except RuntimeError as e:
        print('loop error')
        print(e)

    finally:
        print('stopping loop')
        tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()]
        loop.run_until_complete(asyncio.wait(tasks))
        loop.stop()



if __name__=='__main__':
    main()
