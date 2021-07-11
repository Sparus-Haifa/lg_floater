import datetime
import os
import sys
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_path + os.sep + "cfg")
import configuration as cfg

class PID:
    def __init__(self):
        last_cmd_was_sent_at = None

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


    def interp(self, current_err):
        x1 = 0
        x2 = cfg.task["fullduty_min_distance"] #the border between full to partial
        y1 = cfg.task["max_interval_between_movements"]
        y2 = cfg.task["min_interval_between_movements"]

        m = (y2-y1)/(x2-x1)
        partial_duty_sleep_time = m * current_err + cfg.task["max_interval_between_movements"]
        print("partial_duty_sleep_time: " + str(partial_duty_sleep_time))


if __name__ == "__main__":
    pid = PID()
    pid.interp(50)
    pid.interp(60)
    pid.interp(70)
    pid.interp(80)


