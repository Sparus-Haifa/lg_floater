import datetime
import os
import sys
import time
# from time import sleep, time
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_path + os.sep + "cfg")
import configuration as cfg

class PID:
    def __init__(self, log):
        # last_cmd_was_sent_at = None
        self.log = log
        self.doInterpolation = False
        # 
        self.lastP = None
        self.lastTime = time.time()
        self.p = None
        self.d = None
        self.i = None
        self.kp = cfg.task["kp"]  # 1000  # 10
        self.kd = cfg.task["kd"]  # 60  # 250
        self.ki = cfg.task["ki"]  # 0 # 0.001

    def reset_d(self):
        self.lastP = None

    def pid(self, error):
        # set timers
        nowTime = time.time()
        deltaTime = (nowTime - self.lastTime)
        self.lastTime = nowTime

        # calc PID
        # P
        self.p = error
        # I
        # D
        if self.lastP != None:
            self.d = (self.lastP - self.p) / deltaTime
            self.i+= (self.p + self.lastP) * deltaTime / 2
        else:
            self.d = 0
            self.i = 0

        if self.i < -50:
            self.i = -50
        if 50 < self.i:
            self.i = 50
            
        self.lastP = self.p
        scalar = self.p*self.kp-self.d*self.kd+self.i*self.ki
        self.log.info('scalar = self.p*self.kp - self.d*self.kd + self.i*self.ki')
        self.log.info(f'{scalar} = {self.p}*{self.kp} - {self.d}*{self.kd} + {self.i}*{self.ki}')
        return scalar

    def unpack(self, scalar, error):
        direction = self.getDirection(scalar)
        voltage = self.normal_pumpVoltage(scalar)
        dc = self.interp_dutyCycle(error)
        self.timeOn = self.interp_timeOn(error)
        self.timeOff = self.calc_timeOff(self.timeOn,dc)
        return direction, voltage, dc, self.timeOn, self.timeOff      

    def get_next_move(self, curr_press):
        setpoint_err = cfg.task["setpoint"] - curr_press
        cmd = "U:" if setpoint_err < 0 else "D:"

        if abs(setpoint_err) > cfg.task["fullduty_min_distance"]: #fullduty mode
            last_cmd_was_sent_at = datetime.datetime.Now()
            return cmd + cfg.task["fullduty_exec_time"]
        else: #partial mode
            coefficient = cfg.task["setpoint"] - abs(setpoint_err)/cfg.task["setpoint"]
            partial_duty_exec_time = coefficient * cfg.task["fullduty_exec_time"]
            partial_duty_sleep_time = self.interp(setpoint_err)
            if partial_duty_sleep_time < (datetime.datetime.Now() - self.last_cmd_was_sent_at):
                pass

    # absolute value and limit between 40% to 100%
    def normal_pumpVoltage(self, current_err):
        voltage = abs(int(current_err))
        if voltage >= 100:
            voltage = 100
        if voltage <= 20:
            # voltage = 40
            voltage = 0
        if 20 < voltage <= 40:
            voltage = 40
                    

        # print("voltage", voltage)
        return voltage

    def getDirection(self,curr_err):
        # up (D:1)
        # down (D:2)
        return 1 if curr_err > 0 else 2
        
    def interp_timeOn(self, current_err):
        max_error = 10.0
        current_err = abs(current_err)
        if current_err > max_error:
            current_err = max_error
        x1 = 0 # no error - spot on target!
        x2 = max_error # max error
        y1 = 0.5 # min timeOn is 0.5 sec
        y2 = 2 # max timeOn is 5 secs

        m = (y2-y1)/(x2-x1)

        # print("m",m)

        timeOn = y1 + m * current_err
        self.log.debug(f"timeOn: {timeOn}")
        return round(timeOn,1)

    def interp_dutyCycle(self, current_err):
        max_error = 10.0
        current_err = abs(current_err)
        if current_err > max_error:
            current_err = max_error
            return 1

        x1 = 0 # no error
        x2 = max_error # max error
        y1 = 0.1 # min utility 0% (min dc)
        if current_err == max_error:
            y2 = 0.2 # max utility 100% (max dc)
        else:
            y2 = 1

        m = (y2-y1)/(x2-x1)
        # print("m",m)

        dc = y1 + m * current_err
        self.log.debug(f"duty cycle: {dc}")
        return dc

    def calc_timeOff(self, timeOn, dc):
        # dc = timeOn/(timeOn+timeOff)
        # dc * (timeOn+timeOff) = timeOn
        # dc * timeOn + dc * timeOff = timeOn
        # timeOff * dc = timeOn - dc * timeOn
        # timeOff = timeOn / dc - timeOn
        # timeOff = (timeOn * (1-dc) )/dc


        # dc = timeOn/(timeOn+timeOff)
        # dc * (timeOn+timeOff) = timeOn
        # timeOn + timeOff = timeOn / dc
        timeOff = timeOn / dc - timeOn
        # print("timeOff",timeOff)
        return timeOff


if __name__ == "__main__":
    pid = PID()
    # pid.interp_pumpVoltage(100)
    # pid.interp_pumpVoltage(90)
    # pid.interp_pumpVoltage(80)
    # pid.interp_pumpVoltage(70)
    # pid.interp_pumpVoltage(60)
    # pid.interp_pumpVoltage(50)
    # pid.interp_pumpVoltage(40)
    # pid.interp_pumpVoltage(30)
    # pid.interp_pumpVoltage(20)
    # pid.interp_pumpVoltage(10)
    # pid.interp_pumpVoltage(5)

    for err in range(100,0,-10):
        print("error",err)
        timeOn = pid.interp_timeOn(err)
        dc = pid.interp_dutyCycle(err)
        timeOff = pid.calc_timeOff(timeOn,dc)
        print("timeOff",timeOff)
    # pid.interp_dutyCycle(100)
    # pid.interp_dutyCycle(90)
    # pid.interp_dutyCycle(80)
    # pid.interp_dutyCycle(70)
    # pid.interp_dutyCycle(60)
    # pid.interp_dutyCycle(50)
    # pid.interp_dutyCycle(40)
    # pid.interp_dutyCycle(30)
    # pid.interp_dutyCycle(20)
    # pid.interp_dutyCycle(10)
    # pid.interp_dutyCycle(5)

    



