from transitions.extensions.asyncio import HierarchicalAsyncMachine


class Flag:
    def __init__(self, name, log):
        # super().__init__(name, 1)
        # self.avg_samples = avg_samples
        self.log = log
        self.name = name

        self.status = None

        # self._queues_are_full = False
        self.log.info(f"{self.name} flag controller was initialized successfully")

        self.machine = HierarchicalAsyncMachine(self, states=[], transitions = [])
        # self.machine.add_transition('flag_is_responding', 'initial', 'active', unless=['is_active'])

    def reset(self):
        self.log.debug(f"clearing flag {self.name} data")
        self.status = None

    async def add_sample(self, sample_arr):
        # if not self.state == 'active':
        #     await self.to_active()
        # await self.flag_is_responding()

    
        self.status=int(float(sample_arr))
        # self.status=sample_arr


    def getLast(self):
        return self.status

    def isBufferFull(self):
        return self.status != None