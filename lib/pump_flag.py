from lib.flag import Flag

class PumpFlag(Flag):
    def __init__(self, name, log):
        super().__init__(name, log)


        self.machine.add_states(['off', 'on', 'failure'])
        # self.machine.add_transition('to_on', '*', 'on')
        # self.machine.add_transition('to_off', '*', 'off')
        # self.machine.add_transition('to_failure', '*', 'failure')


    async def add_sample(self, sample_arr):
        print(sample_arr)
        # if self.state == 'initial'
        num =  int(float(sample_arr))
        if num == 0: await self.to_off()
        if num == 1: await self.to_on()
        if num == 2: await self.to_failure()
        return await super().add_sample(sample_arr)
