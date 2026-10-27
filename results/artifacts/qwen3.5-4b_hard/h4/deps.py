class CycleError(Exception):
    def __init__(self, cycle):
        super().__init__(f"cycle: {cycle}")
        self.cycle = cycle

def resolve(graph):
    raise NotImplementedError
