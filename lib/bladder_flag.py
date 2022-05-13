from lib.flag import Flag

class BladderFlag(Flag):
    def __init__(self, name, log):
        super().__init__(name, log)


        self.machine.add_states(['full', 'empty', 'nonempty'], ignore_invalid_triggers=True)
        # self.machine.add_transition('to_full', ['initial', 'nonempty'], 'full')
        # self.machine.add_transition('to_empty', ['initial', 'nonempty'], 'empty')
        # self.machine.add_transition('to_nonempty', ['initial', 'full', 'empty'], 'nonempty')


    async def add_sample(self, sample_arr):
        # print(sample_arr)
        # if self.state == 'initial'
        await super().add_sample(sample_arr)
        num =  self.getLast()
        if num == 0: await self.to_nonempty()
        if num == 1: await self.to_empty()
        if num == 2: await self.to_full()
        return
        
