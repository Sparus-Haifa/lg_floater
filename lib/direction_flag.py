from lib.flag import Flag

class DirectionFlag(Flag):
    def __init__(self, name, log):
        super().__init__(name, log)


        self.machine.add_states(['up', 'down'])


    async def add_sample(self, sample_arr):
        # print(sample_arr)
        # if self.state == 'initial'
        num = int(sample_arr)
        if num ==  1: await self.to_down()
        if num ==  2: await self.to_up()
        return await super().add_sample(sample_arr)
