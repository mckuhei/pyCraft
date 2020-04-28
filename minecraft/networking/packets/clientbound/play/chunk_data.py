from minecraft.networking.packets import Packet
from minecraft.networking.types import (
    VarInt, Integer, Boolean, Nbt
)


class ChunkDataPacket(Packet):
    @staticmethod
    def get_id(context):
        return 0x22 # FIXME

    packet_name = 'chunk data'

    def read(self, file_object):
        self.x = Integer.read(file_object)
        self.z = Integer.read(file_object)
        self.full_chunk = Boolean.read(file_object)
        self.bit_mask_y = VarInt.read(file_object)
        self.heightmaps = Nbt.read(file_object)
        self.biomes = []
        if self.full_chunk:
            for i in range(1024):
                self.biomes.append(Integer.read(file_object))
        size = VarInt.read(file_object)
        self.data = file_object.read(size)
        size_entities = VarInt.read(file_object)
        self.entities = []
        for i in range(size_entities):
            self.entities.append(Nbt.read(file_object))

    def write_fields(self, packet_buffer):
        Integer.send(self.x, packet_buffer)
        Integer.send(self.z, packet_buffer)
        Boolean.send(self.full_chunk, packet_buffer)
        VarInt.send(self.bit_mask_y, packet_buffer)
        Nbt.send(self.heightmaps, packet_buffer)
        if self.full_chunk:
            for i in range(1024):
                Integer.send(self.biomes[i], packet_buffer)
        VarInt.send(len(self.data), packet_buffer)
        packet_buffer.send(self.data)
        VarInt.send(len(self.entities), packet_buffer)
        for e in self.entities:
            Nbt.send(e, packet_buffer)
        
