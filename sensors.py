from lib.rpm import RPM
from lib.flag import Flag
from lib.altimeter import Altimeter
from lib.bladder_volume import Bladder
from lib.bladder_flag import BladderFlag
from lib.pump_flag import PumpFlag
from lib.iridium_flag import IridiumFlag

from lib.direction_flag import DirectionFlag


from lib.press_ctrl import *
from lib.temp_ctrl import *
from lib.imu_ctrl import *
from lib.safety_ctrl import *
from lib.fyi_ctrl import *
from lib.profile import *
from lib.task_ctrl import *

import logging


class Sensors:
    def __init__(self) -> None:
        self.log = logging.getLogger('normal')
        self.sensors = {}
        self.flags = {}
        self.setupSensors()
        self.addSensorsToDict()
        self.addFlagsToDict()

    def setupSensors(self):
            # Pressure
            self.pressureController = Press_ctrl(cfg.pressure["avg_samples"], cfg.pressure["precision"], cfg.pressure["epsilon"], self.log)
            self.pressureController.addSensor("BP1", offset=-68)
            self.pressureController.addSensor("BP2")
            self.pressureController.addSensor("TP1")
            self.pressureController.addSensor("TP2")
            # self.pressureController.addSensor("HP")
            # self.pressureController.addSensor("AP")
            self.pressureSensors = self.pressureController.getSensors()
            self.pressureSensors["HP"] = Press("HP",cfg.pressure["avg_samples"],cfg.pressure["precision"],self.log)
            self.pressureSensors["AP"] = Press("AP",cfg.pressure["avg_samples"],cfg.pressure["precision"],self.log)


            # Temperature
            self.temperatureController = Temp_ctrl(cfg.temperature["avg_samples"], cfg.temperature["precision"], self.log)
            self.temperatureController.addSensor("BT1")
            self.temperatureController.addSensor("BT2")
            self.temperatureController.addSensor("TT1")
            self.temperatureController.addSensor("TT2")
            self.temperatureController.addSensor("AT")
            self.temperatureSensors = self.temperatureController.getSensors()

            # IMU
            self.IMUController = IMU_ctrl(cfg.imu["avg_samples"], cfg.imu["precision"], self.log)
            self.IMUController.addSensor("X")
            self.IMUController.addSensor("Y")
            self.IMUController.addSensor("Z")
            self.IMUSensors = self.IMUController.getSensors()
            
            # Other sensors
            self.bladderVolume = Bladder("Bladder Volume", cfg.bladder["avg_samples"], cfg.bladder["precision"], self.log)
            self.altimeter = Altimeter("Altimeter", cfg.altimeter["avg_samples"], cfg.altimeter["precision"], self.log)
            self.rpm = RPM("RPM", cfg.rpm["avg_samples"], cfg.rpm["precision"], self.log)


            # Flags
            self.pumpFlag = PumpFlag("Pump",self.log)  # PF
            self.bladder_flag = BladderFlag("Bladder", self.log)  # BF
            self.leak_h_flag = Flag("Hull leak", self.log)  # HL
            self.leak_e_flag = Flag("Engine leak", self.log)  # EL
            self.full_surface_flag = Flag("Full surface initiated", self.log)   
            self.iridium_flag = IridiumFlag("Iridium", self.log)  # I   

            # Direction
            self.direction_flag = DirectionFlag("direction", self.log)

            # Voltage
            self.voltage_sensor = Sensor("Voltage", avg_samples=1, precision=1, log=self.log)

            # Payload flag
            self.payload_flag = Flag("Payload", self.log) # PT

    def addSensorsToDict(self):
        for sensor in self.temperatureSensors:
            self.sensors[sensor]=self.temperatureSensors[sensor]
        for sensor in self.pressureSensors:
            self.sensors[sensor]=self.pressureSensors[sensor]
        for sensor in self.IMUSensors:
            self.sensors[sensor]=self.IMUSensors[sensor]

        self.sensors["PD"]=self.altimeter
        self.sensors["PC"]=self.altimeter
        self.sensors["BV"]=self.bladderVolume
        self.sensors["rpm"]=self.rpm
    

    def addFlagsToDict(self):
        self.flags["PF"]=self.pumpFlag
        self.flags["HL"]=self.leak_h_flag
        self.flags["EL"]=self.leak_e_flag
        self.flags["BF"]=self.bladder_flag
        self.flags["FS"]=self.full_surface_flag
        self.flags["I"]=self.iridium_flag
        self.flags["D"]=self.direction_flag
        self.flags["PT"]=self.payload_flag