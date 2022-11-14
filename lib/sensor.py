from collections import deque
from transitions.extensions.asyncio import HierarchicalAsyncMachine

class Sensor:
    def __init__(self, name, avg_samples, precision, log, offset = 0):
        self.name = name
        self.avg_samples = avg_samples
        self.t = deque(maxlen=self.avg_samples)
        self.precision = precision
        self.log = log
        self.machine = HierarchicalAsyncMachine(self, states=['active', 'faulty'], transitions = [], ignore_invalid_triggers=True)
        self.machine.add_transition('sensor_is_responding', 'initial', 'active', unless=['is_active'])
        self.offset = offset




    def reset(self):
        self.log.debug(f"clearing sensor {self.name} data")
        self.t.clear()

    def getName(self):
        return self.name

    def getLast(self):
        if len(self.t)<self.avg_samples:
            # print(f"{self.getName()} buffer is empty")
            # return "Buffering"
            return f"Buffering ({len(self.t)}/{self.avg_samples})"

        avg = sum(self.t)/len(self.t)
        # return self.t[0]
        return round(avg,self.precision)
        # return round(self.t[-1],self.precision)

    async def add_sample(self, sample):
        if not self.state == 'active':
            await self.to_active()
        # TODO: try catch parse
        # self.log.debug(f'{self.name}:{sample}')
        try:
            value = float(sample) + self.offset
        # except Exception as e:
        except ValueError as e:
            # print(e)
            # print(sample)
            # exit()
            self.log.error(f"SENSOR ERROR: [{self.name}] Overflow value: [{sample}]") # TODO: handle
            return
        # self.t.append(sample)
        if self.name in ['BP1','BP2','TP1','TP2']:
            value/=100


        self.t.append(value)

    def isBufferFull(self):
        return self.avg_samples == len(self.t)