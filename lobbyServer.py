"""
Use this if you want to run multiple matches at once
This is the way you should usually run the server
"""

import os
import copy
import random
import time
import ul_core.net.network as network

from ul_core.net.network_manager import ConnectionClosed
from ul_core.net.network import ServerNetworkManager
from gameServer import GameServer


class LobbyServer:
    def __init__(self, verbose):
        self.network_manager = ServerNetworkManager(self)
        self.ready_players = []
        self.game_server_procs = {}
        self.verbose = self.network_manager.verbose = verbose

    #
    # Network functions
    # These must be named in camelCase for compatibility reasons
    #

    def onClientConnected(self, conn):
        for conn in self.network_manager.connections:
            conn.updateNumPlayers(len(self.network_manager.connections))
        if self.verbose:
            print("Client connected from " + str(conn.addr))

    def requestNumPlayers(self, addr):
        for conn in self.network_manager.connections:
            try:
                conn.updateNumPlayers(len(self.network_manager.connections))
            except (ConnectionResetError, BrokenPipeError):
                print("connection reset")
                pass  # If they dc'd, don't worry about it

    def addPlayer(self, addr):
        conn = next(
            conn for conn in self.network_manager.connections
            if conn.addr == addr)
        if conn not in self.ready_players:
            self.ready_players.append(conn)

    #
    # End of network functions
    #

    def update_num_players(self):
        self.requestNumPlayers(None)

    def accept_connections(self):
        try:
            self.network_manager.accept()
            self.network_manager.recv()
        except network.OpcodeError as e:
            print(e)
        except ConnectionClosed as c:
            self.network_manager.connections.remove(c.conn)
            try:
                self.ready_players.remove(c.conn)
            except ValueError:
                pass
            self.update_num_players()  # Tell everyone they DC'd
        except AttributeError as e:
            print("Client probably sending stuff it shouldn't: " + str(e))

        # Get the first 2 ready players
        ready_players = self.ready_players[:2]

        if len(ready_players) == 2:
            if self.verbose:
                print("Game time started. Forking subprocess.")
            f = os.fork()
            if f == 0:
                random.seed()  # Regenerate the random seed for this game
                netman = copy.copy(self.network_manager)
                # We need only the players for the game we're currently serving
                netman.connections = self.ready_players
                GameServer(netman).run()
            else:
                self.network_manager.connections = [
                    c for c in self.network_manager.connections
                    if c not in ready_players]
                self.game_server_procs[f] = ready_players
                # Remove the 2 players from the list of ready players
                self.ready_players = self.ready_players[2:]

        while len(self.game_server_procs) > 0:
            # Clean up when the game server finishes
            pid = os.waitpid(-1, os.WNOHANG)[0]
            if pid != 0:
                self.on_game_server_finished(pid)
            else:
                break

    def on_game_server_finished(self, procid):
        """
        Send the player back to the lobby when the child proc finishes
        """
        for pl in self.game_server_procs[procid]:
            self.network_manager.connections.append(pl)

        self.game_server_procs.pop(procid)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    lobby = LobbyServer(verbose=args.verbose)
    while 1:
        lobby.accept_connections()
        time.sleep(0.01)
