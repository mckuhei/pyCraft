#!/usr/bin/env python3

from __future__ import print_function

import getpass
import sys
import re
import json
import traceback
from optparse import OptionParser

from minecraft import authentication
from minecraft.exceptions import YggdrasilError
from minecraft.networking.connection import Connection
from minecraft.networking.packets import Packet, clientbound, serverbound
from minecraft.compat import input
from minecraft.managers import DataManager, AssetsManager, ChatManager, ChunksManager, EntitiesManager


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

    assets = AssetsManager(options.assets)
    mcdata = DataManager("./mcdata")

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
            return
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

    chat = ChatManager(assets)
    chat.register(connection)

    chunks = ChunksManager(mcdata)
    chunks.register(connection)

    def handle_join_game(join_game_packet):
        print('Connected.')

    connection.register_packet_listener(handle_join_game, clientbound.play.JoinGamePacket)

    connection.connect()

    while True:
        try:
            text = input()
            if text.startswith("!"):
                if text == "!respawn":
                    print("respawning...")
                    packet = serverbound.play.ClientStatusPacket()
                    packet.action_id = serverbound.play.ClientStatusPacket.RESPAWN
                    connection.write_packet(packet)
                elif text.startswith("!print "):
                    p = text.split(" ")
                    chunks.print_chunk(chunks.get_chunk(int(p[1]), int(p[2]), int(p[3])), int(p[4]))
                else:
                    print("Unknow test command: %s"%(text))
            else:
                chat.send(connection, text)

        except KeyboardInterrupt:
            print("Bye!")
            sys.exit()

        except Exception as ex:
            print("Exception: %s"%(ex))
            traceback.print_exc()


if __name__ == "__main__":
    main()
