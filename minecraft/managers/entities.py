

from ..networking.packets import clientbound

class EntitiesManager:

    def __init__(self, data_manager):
        self.data = data_manager
        self.entities = {}

    def register(self, connection):
        pass
