#!/usr/bin/env python3

from __future__ import print_function

import getpass
import sys
import re
import json
from optparse import OptionParser

from minecraft import authentication
from minecraft.exceptions import YggdrasilError
from minecraft.networking.connection import Connection
from minecraft.networking.packets import Packet, clientbound, serverbound
from minecraft.compat import input


def get_options():
    parser = OptionParser()

    parser.add_option("-u", "--username", dest="username", default=None,
                      help="username to log in with")

    parser.add_option("-p", "--password", dest="password", default=None,
                      help="password to log in with")

    parser.add_option("-s", "--server", dest="server", default=None,
                      help="server host or host:port "
                           "(enclose IPv6 addresses in square brackets)")

    parser.add_option("-o", "--offline", dest="offline", action="store_true",
                      help="connect to a server in offline mode ")

    parser.add_option("-d", "--dump-packets", dest="dump_packets",
                      action="store_true",
                      help="print sent and received packets to standard error")

    parser.add_option("-a", "--assets", dest="assets", default='minecraft',
                      help="assets directory (uncompressed)")

    parser.add_option("--mcversion", dest="mcversion", default='1.15.2',
                      help="minecraft version")

    (options, args) = parser.parse_args()

    if not options.username:
        options.username = input("Enter your username: ")

    if not options.password and not options.offline:
        options.password = getpass.getpass("Enter your password (leave "
                                           "blank for offline mode): ")
        options.offline = options.offline or (options.password == "")

    if not options.server:
        options.server = input("Enter server host or host:port "
                               "(enclose IPv6 addresses in square brackets): ")
    # Try to split out port and address
    match = re.match(r"((?P<host>[^\[\]:]+)|\[(?P<addr>[^\[\]]+)\])"
                     r"(:(?P<port>\d+))?$", options.server)
    if match is None:
        raise ValueError("Invalid server address: '%s'." % options.server)
    options.address = match.group("host") or match.group("addr")
    options.port = int(match.group("port") or 25565)

    return options


def main():
    options = get_options()

    lang = {}
    with open("%s/lang/en_us.json"%options.assets) as f:
        lang = json.loads(f.read())
        for x in lang:
            lang[x] = re.sub("\%\d+\$s", "%s", lang[x]) # HACK

    blocks = {}
    blocks_states = {}
    with open("mcdata/blocks.json") as f:
        blocks = json.loads(f.read())
    for x in blocks:
        for s in blocks[x]['states']:
            blocks_states[s['id']] = x

    registries = {}
    biomes = {}
    with open("mcdata/registries.json") as f:
        registries = json.loads(f.read())
    for x in registries["minecraft:biome"]["entries"]:
        biomes[registries["minecraft:biome"]["entries"][x]["protocol_id"]] = x

    if options.offline:
        print("Connecting in offline mode...")
        connection = Connection(
            options.address, options.port, username=options.username,
            allowed_versions=[options.mcversion])
    else:
        auth_token = authentication.AuthenticationToken()
        try:
            auth_token.authenticate(options.username, options.password)
        except YggdrasilError as e:
            print(e)
            sys.exit()
        print("Logged in as %s..." % auth_token.username)
        connection = Connection(
            options.address, options.port, auth_token=auth_token,
            allowed_versions=[options.mcversion])

    if options.dump_packets:
        def print_incoming(packet):
            if type(packet) is Packet:
                # This is a direct instance of the base Packet type, meaning
                # that it is a packet of unknown type, so we do not print it.
                return
            if type(packet) in [clientbound.play.EntityVelocityPacket, clientbound.play.EntityLookPacket]:
                # Prevents useless console spam
                return
            print('--> %s' % packet, file=sys.stderr)

        def print_outgoing(packet):
            print('<-- %s' % packet, file=sys.stderr)

        connection.register_packet_listener(
            print_incoming, Packet, early=True)
        connection.register_packet_listener(
            print_outgoing, Packet, outgoing=True)

    def handle_join_game(join_game_packet):
        print('Connected.')

    connection.register_packet_listener(handle_join_game, clientbound.play.JoinGamePacket)

    def translate_chat(data):
        if isinstance(data, str):
            return data
        elif 'extra' in data:
            return "".join([translate_chat(x) for x in data['extra']])
        elif 'translate' in data and 'with' in data:
            params = [translate_chat(x) for x in data['with']]
            return lang[data['translate']]%tuple(params)
        elif 'translate' in data:
            return lang[data['translate']]
        elif 'text' in data:
            return data['text']
        else:
            return "?"

    def print_chat(chat_packet):
        try:
            print("[%s] %s"%(chat_packet.field_string('position'), translate_chat(json.loads(chat_packet.json_data))))
        except Exception as ex:
            print("Exception %r on message (%s): %s" % (ex, chat_packet.field_string('position'), chat_packet.json_data))

    connection.register_packet_listener(print_chat, clientbound.play.ChatMessagePacket)

    def handle_block(block_packet):
        print('Block %s at %s'%(blocks_states[block_packet.block_state_id], block_packet.location))

    connection.register_packet_listener(handle_block, clientbound.play.BlockChangePacket)

    def handle_multiblock(multiblock_packet):
        for b in multiblock_packet.records:
            handle_block(b)

    connection.register_packet_listener(handle_multiblock, clientbound.play.MultiBlockChangePacket)

    def handle_chunk(chunk_packet):
        if chunk_packet.entities == []:
            return
        print('Chunk at %d,%d (%s): %s'%(chunk_packet.x, chunk_packet.z, biomes[chunk_packet.biomes[0]], chunk_packet.__dict__))

    connection.register_packet_listener(handle_chunk, clientbound.play.ChunkDataPacket)


    connection.connect()

    while True:
        try:
            text = input()
            if not text:
                continue
            if text == "/respawn":
                print("respawning...")
                packet = serverbound.play.ClientStatusPacket()
                packet.action_id = serverbound.play.ClientStatusPacket.RESPAWN
                connection.write_packet(packet)
            else:
                packet = serverbound.play.ChatPacket()
                packet.message = text
                connection.write_packet(packet)
        except KeyboardInterrupt:
            print("Bye!")
            sys.exit()


if __name__ == "__main__":
    main()
