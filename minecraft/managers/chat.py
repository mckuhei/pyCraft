import json

from ..networking.packets import clientbound, serverbound

class ChatManager:

    def __init__(self, assets_manager):
        self.assets = assets_manager

    def translate_chat(self, data):
        if isinstance(data, str):
            return data
        elif 'extra' in data:
            return "".join([self.translate_chat(x) for x in data['extra']])
        elif 'translate' in data and 'with' in data:
            params = [self.translate_chat(x) for x in data['with']]
            return self.assets.translate(data['translate'], params)
        elif 'translate' in data:
            return self.assets.translate(data['translate'])
        elif 'text' in data:
            return data['text']
        else:
            return "?"

    def print_chat(self, chat_packet):
        # TODO: Replace with handler
        try:
            print("[%s] %s"%(chat_packet.field_string('position'), self.translate_chat(json.loads(chat_packet.json_data))))
        except Exception as ex:
            print("Exception %r on message (%s): %s" % (ex, chat_packet.field_string('position'), chat_packet.json_data))
    
    def register(self, connection):
        connection.register_packet_listener(self.print_chat, clientbound.play.ChatMessagePacket)
    
    def send(self, connection, text):
        if not text:
            # Prevents connection bug when sending empty chat message
            return
        packet = serverbound.play.ChatPacket()
        packet.message = text
        connection.write_packet(packet)
