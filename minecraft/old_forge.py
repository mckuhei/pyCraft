from minecraft.networking.connection import Connection, LoginReactor, STATE_PLAYING
from minecraft.networking.packets import clientbound, serverbound, Packet, PacketBuffer, AbstractPluginMessagePacket
from minecraft.networking.types import VarInt, String
import sys,time,json

class ForgeConnection(Connection):

    def __init__(self,*args,**kwargs):
        auto_find_mods = kwargs.pop('auto_find_mods',False)
        super().__init__(*args,**kwargs);
        self.forge_config = ForgeConfig()
        self.register_packet_listener(self.handle_fml_packet,AbstractPluginMessagePacket)
        if auto_find_mods:
            handle_exit = self.handle_exit
            self.handle_exit = None
            self.wait = True
            self.status(self.handle_motd)
            if self.wait:
                time.sleep(1)
            self.handle_exit = handle_exit
    def handle_motd(self,response):
        if response.get('modinfo') and response['modinfo'].get('modList'):
            for mod in response['modinfo']['modList']:
                self.forge_config.mods[mod['modid']] = mod['version']
        self.wait = False

    def handle_fml_packet(self,packet):
        if packet.channel == "FML|HS":
            if packet.data[0]==0: # Server Hello
                self.fml_proto_ver = packet.data[1]
                self.write_packet(serverbound.play.PluginMessagePacket(channel="REGISTER",data=b'\0'.join([b'FML|HS', b'FML', b'FML|MP', b'FML', b'FORGE'])))
                self.write_packet(serverbound.play.PluginMessagePacket(channel="FML|HS",data=bytes([1,self.fml_proto_ver])))
                buffer = PacketBuffer()
                buffer.send(bytes([2]))
                VarInt.send(len(self.forge_config.mods.keys()),buffer);
                for mod,version in self.forge_config.mods.items():
                    String.send(mod,buffer)
                    String.send(version,buffer)
                self.write_packet(serverbound.play.PluginMessagePacket(channel="FML|HS",data=buffer.get_writable()))
            if packet.data[0]==2: #Server mod list
                buffer = PacketBuffer()
                buffer.send(packet.data[1:])
                buffer.reset_cursor()
                for i in range(VarInt.read(buffer)):
                    mod = String.read(buffer)
                    version = String.read(buffer)
                    self.forge_config.server_mods[mod]=version
                self.write_packet(serverbound.play.PluginMessagePacket(channel="FML|HS",data=bytes([255,2])))
            if packet.data[0]==3: #Regsitry data
                buffer = PacketBuffer()
                buffer.send(packet.data[1:])
                buffer.reset_cursor()
                if buffer.read(1)==0:
                    self.write_packet(serverbound.play.PluginMessagePacket(channel="FML|HS",data=bytes([255,3])))
                regsitry = Regsitry(String.read(buffer))
                for i in range(VarInt.read(buffer)):
                    name = String.read(buffer)
                    id = VarInt.read(buffer)
                    regsitry.registries[name] = id
                regsitry.substitutions=[String.read(buffer) for i in range(VarInt.read(buffer))]
                self.forge_config.registries.append(regsitry)
            if packet.data[0]==255: #Handshark ack
                phase = 4
                if packet.data[1]==3:
                    phase=5
                self.write_packet(serverbound.play.PluginMessagePacket(channel="FML|HS",data=bytes([255,phase])))
            if packet.data[0]==254: #Reset handshark
                mods = forge_config.mods.copy()
                self.forge_config = ForgeConfig()
                self.forge_config.mods = mods;




    def _handshake(self, next_state=STATE_PLAYING):
        handshake = serverbound.handshake.HandShakePacket()
        handshake.protocol_version = self.context.protocol_version
        handshake.server_address = self.options.address + "\0FML\0"
        handshake.server_port = self.options.port
        handshake.next_state = next_state
        self.write_packet(handshake)



class ForgeConfig:
    def __init__(self):
        self.mods = {}
        self.server_mods = {}
        self.registries = []

class Regsitry(object):
    def __init__(self, name):
        self.name = name
        self.registries = {}
        self.substitutions = []
        #self.dummies = [] # TODO: Dummies

if __name__ == '__main__':
    connection = ForgeConnection(
            "127.0.0.1", 65535, username="Test", initial_version=340,allowed_versions=[340],auto_find_mods=True)
    def print_incoming(packet):
        if type(packet) is Packet:
            # This is a direct instance of the base Packet type, meaning
            # that it is a packet of unknown type, so we do not print it
            # unless explicitly requested by the user.
            if False:
                 print('--> [unknown packet] %s' % packet, file=sys.stderr)
        else:
            print('--> %s' % packet, file=sys.stderr)

    def print_outgoing(packet):
        print('<-- %s' % packet, file=sys.stderr)

    connection.register_packet_listener(
            print_incoming, Packet, early=True)
    connection.register_packet_listener(
            print_outgoing, Packet, outgoing=True)
    connection.connect()
    while 1:
        input("")