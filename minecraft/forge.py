from .networking.connection import Connection, LoginReactor, STATE_PLAYING
from .networking.packets import clientbound, serverbound, PacketBuffer
from .networking.types import VarInt, VarIntPrefixedByteArray, Boolean

class ForgeConnection(Connection):

    def _handshake(self, next_state=STATE_PLAYING):
        handshake = serverbound.handshake.HandShakePacket()
        handshake.protocol_version = self.context.protocol_version
        handshake.server_address = self.options.address + "\0FML2\0"
        handshake.server_port = self.options.port
        handshake.next_state = next_state
        self.write_packet(handshake)

    def connect(self):
        self.forge_config = ForgeConfig()
        super().connect()
        if len(self.allowed_proto_versions) == 1:
            self.reactor = ForgeLoginReactor(self)


class ForgeConfig:
    def __init__(self):
        self.mods = []
        self.channels = {}
        self.registries_list = []
        self.registries = {}
        self.configs = {}

class ForgeLoginReactor(LoginReactor):

    def react(self, packet):
        if packet.packet_name == "login plugin request":
        
            if packet.channel == "fml:loginwrapper":
                fc = self.connection.forge_config
            
                packet_data = PacketBuffer()
                packet_data.send(packet.data)
                packet_data.reset_cursor()
                loc = VarIntPrefixedByteArray.read(packet_data).decode()
                size = VarInt.read(packet_data)
                hs_type = VarInt.read(packet_data)
                
                if loc == "fml:handshake" and hs_type == 1: # S2CModList
                    fc.mods = []
                    count = VarInt.read(packet_data)
                    for i in range(count):
                        fc.mods.append(VarIntPrefixedByteArray.read(packet_data).decode())
                    
                    fc.channels = {}
                    count = VarInt.read(packet_data)
                    for i in range(count):
                        k = VarIntPrefixedByteArray.read(packet_data).decode()
                        v = VarIntPrefixedByteArray.read(packet_data).decode()
                        fc.channels[k] = v
                    
                    fc.registries_list = []
                    count = VarInt.read(packet_data)
                    for i in range(count):
                        fc.registries_list.append(VarIntPrefixedByteArray.read(packet_data).decode())
                    
                elif loc == "fml:handshake" and hs_type == 3: # S2CRegistry
                    reg = VarIntPrefixedByteArray.read(packet_data).decode()
                    fc.registries[reg] = {}
                    if Boolean.read(packet_data):
                        fc.registries[reg]['ids'] = {}
                        count = VarInt.read(packet_data)
                        for i in range(count):
                            k = VarIntPrefixedByteArray.read(packet_data).decode()
                            v = VarInt.read(packet_data)
                            fc.registries[reg]['ids'][k] = v

                        fc.registries[reg]['aliases'] = {}
                        count = VarInt.read(packet_data)
                        for i in range(count):
                            k = VarIntPrefixedByteArray.read(packet_data).decode()
                            v = VarIntPrefixedByteArray.read(packet_data).decode()
                            fc.registries[reg]['aliases'][k] = v

                        fc.registries[reg]['overrides'] = {}
                        count = VarInt.read(packet_data)
                        for i in range(count):
                            k = VarIntPrefixedByteArray.read(packet_data).decode()
                            v = VarIntPrefixedByteArray.read(packet_data).decode()
                            fc.registries[reg]['aliases'][k] = v
                            
                        fc.registries[reg]['blocked'] = []
                        count = VarInt.read(packet_data)
                        for i in range(count):
                            fc.registries[reg]['blocked'].append(VarInt.read(packet_data))

                        fc.registries[reg]['dummied'] = []
                        count = VarInt.read(packet_data)
                        for i in range(count):
                            fc.registries[reg]['dummied'].append(VarIntPrefixedByteArray.read(packet_data).decode())
                    
                elif loc == "fml:handshake" and hs_type == 4: # S2CConfigData
                    k = VarIntPrefixedByteArray.read(packet_data).decode()
                    v = VarIntPrefixedByteArray.read(packet_data).decode()
                    fc.configs[k] = v
                    
                else:
                    print("!!! Unknow %s type %s"%(loc, hs_type))
                    print("!!! ", packet_data.read())

                response_data = PacketBuffer()
                VarIntPrefixedByteArray.send(loc.encode(), response_data)
                VarInt.send(1, response_data)
                VarInt.send(99, response_data)
                response_data.reset_cursor()
                self.connection.write_packet(serverbound.login.PluginResponsePacket(message_id=packet.message_id, successful=True, data=response_data.read()))

            else:
                print("!!! Unknow channel: %s"%(packet.channel))
                print("!!! ", packet.data)
                self.connection.write_packet(serverbound.login.PluginResponsePacket(message_id=packet.message_id, successful=False))
        else:
            super().react(packet)
