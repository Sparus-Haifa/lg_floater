from lib.flag import Flag

class DirectionFlag(Flag):
    def __init__(self, name, log):
        super().__init__(name, log)


        self.machine.add_states(['up', 'down', 'idle'])


    async def add_sample(self, sample_arr):
        # print(sample_arr)
        # if self.state == 'initial'
        num = int(sample_arr)
        if num ==  0: await self.to_idle()
        if num ==  1: await self.to_down()
        if num ==  2: await self.to_up()
        # print("direction flag")
        # print(self.state)
        return await super().add_sample(sample_arr)
