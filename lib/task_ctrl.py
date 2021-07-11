import os
import sys
import datetime
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_path + os.sep + "cfg")
import configuration as cfg

class Task:

    def __init__(self, objPres, objLog):
        self._type = cfg.task["type"]
        self._duration = cfg.task["duration"]
        self._setpoint = cfg.task["setpoint"]
        self._objPres = objPres
        self._objLog = objLog
        self._when_arrived_to_setpoint = None

    def exec(self):
        if self._type == 1: #1-pressure
            self._exec_pressure()
        elif self._type == 2: #2-density
            pass
        elif self._type == 3: #3-profiling
            pass
        else:
            return

    def _exec_pressure(self):
        current_dept = self._objPres.get_current_pressure()
        delta_from_setpoint = abs(current_dept - self._setpoint)

        if delta_from_setpoint <= cfg.task["setpoint_tollerance"]:
            # is it the first time we hit the setpoint?
            if not self._when_arrived_to_setpoint:
                #if yes, calculate mission time from now
                self._when_arrived_to_setpoint = datetime.datetime.Now()

            # how much time we've spent around the the setpoint
            if (datetime.datetime.Now() - self._when_arrived_to_setpoint).total_seconds() >= cfg.task["duration"]:
                cfg.Current_state = cfg.State.END_TASK
                return "!e!"
            else:
                pass



    def _exec_density(self):
        pass

    def _exec_profile(self):
        pass











