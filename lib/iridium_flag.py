from lib.flag import Flag

class IridiumFlag(Flag):
    def __init__(self, name, log):
        super().__init__(name, log)


        self.machine.add_states(['idle', 'requesting', 'transmitting'])


    async def add_sample(self, sample_arr):
        print(sample_arr)
        # if self.state == 'initial'
        match int(float(sample_arr)):
            case 0: await self.to_idle()
            case 1: await self.to_transmitting()
            # case 2: await self.to_failure()
        return await super().add_sample(sample_arr)
