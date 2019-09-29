"""
Server script.
Takes the client's actions and computes the results, then sends them back.
"""

import traceback
import random
import time

from ul_core.net.network_manager import ConnectionClosed
from ul_core.core.game import Game, EndOfGame
from ul_core.core.exceptions import IllegalMoveError
import ul_core.net.factions as factions
from ul_core.core.enums import numericEnum

from server_event_handler import ServerEventHandler


class ServerError(Exception):
    pass


State = numericEnum('FactionSelect', 'Playing')


class GameServer:
    def __init__(self, netman):
        self.network_manager = netman
        netman.handoff_to(self)
        self.addrs = [c.addr for c in self.network_manager.connections]
        self.factions = [None, None]
        self.state = State.FactionSelect

        for conn in self.network_manager.connections:
            conn.onEnteredGame()

    def other_connection(self, conn):
        """
        Get the other connection from this one
        """
        idx = self.network_manager.connections.index(conn)
        if idx == 0:
            return self.network_manager.connections[1]
        else:
            return self.network_manager.connections[0]

    #
    # Network functions
    # These must be named in camelCase for compatibility reasons
    #

    def selectFaction(self, addr, index):
        if self.state != State.FactionSelect:
            print("Can't select faction in state " + str(self.state))
            return

        available_factions = factions.availableFactions
        self.factions[self.addrs.index(addr)] = available_factions[index]
        # If both players have selected their faction, start the game
        if None not in self.factions:
            for i, conn in enumerate(self.network_manager.connections):
                self.other_connection(conn).updateEnemyFaction(
                    available_factions.index(self.factions[i]))

            self.deciding_player = random.randint(0, 1)
            self.not_deciding_player = (self.deciding_player + 1) % 2
            first_player = self.deciding_player
            self.start(first_player)

    def mulligan(self, addr, *cards):
        pl = self.players[addr]
        pl.mulligan(*cards)

        if pl.opponent.hasMulliganed:
            for c in self.network_manager.connections:
                c.updateBothPlayersMulliganed()
            self.redraw()
            self.state = State.Playing
        else:
            pl.connection.endRedraw()

    def revealFacedown(self, addr, card, target=None):
        pl = self.players[addr]
        pl.revealFacedown(card, target)
        self.redraw()

    def playFaceup(self, addr, card, target=None):
        pl = self.players[addr]
        pl.playFaceup(card, target)
        self.redraw()

    def attack(self, addr, attacker, target):
        pl = self.players[addr]
        pl.attack(attacker, target)
        self.redraw()

    def play(self, addr, card):
        pl = self.players[addr]
        pl.play(card)
        self.redraw()

    def useFactionAbility(self, addr, *args):
        try:
            self.players[addr].factionAbility(*args)
        except TypeError:  # Ignore if args are bad
            pass

        self.redraw()

    def endTurn(self, addr, target=None):
        pl = self.players[addr]
        if target is not None and isinstance(pl, factions.Faerie):
            pl.endTurn(target)
        else:
            pl.endTurn()
        self.redraw()

    def makeDecision(self, addr, *cards):
        pl = self.players[addr]
        pl.makeRequiredDecision(*cards)
        self.redraw()

    def useThiefAbility(self, addr, discard_index, cardname, target_index):
        pl = self.players[addr]
        pl.thiefAbility(
            pl.hand[discard_index],
            cardname,
            pl.opponent.facedowns[target_index])
        self.redraw()

    #
    # End of network functions
    #

    def start(self, first_player):
        self.state = State.Playing

        second_player = (first_player + 1) % 2

        self.game = Game(self.factions[first_player],
                         self.factions[second_player],
                         ServerEventHandler(self.network_manager.connections))

        # addr->player TODO rename these
        self.players = dict([
            (self.addrs[first_player], self.game.players[0]),
            (self.addrs[second_player], self.game.players[1])])

        # connection->player, player->connection
        for i, addr in enumerate(self.addrs):
            conn = self.network_manager.connections[i]
            player = self.players[addr]
            conn.player = player
            player.connection = conn

        dp = self.network_manager.connections[self.deciding_player]
        if first_player == dp:
            dp.enemyGoingSecond()
        else:
            dp.enemyGoingFirst()

        ndp = self.network_manager.connections[self.not_deciding_player]
        if first_player == self.deciding_player:
            ndp.enemyGoingFirst()
        else:
            ndp.enemyGoingSecond()

        self.game.start()
        self.redraw()

    def redraw(self):
        for pl in self.game.players:
            c = pl.connection
            enemy_player = pl.opponent

            c.setActive(int(pl.active))

            c.updateHasAttacked(*(c.hasAttacked for c in pl.faceups))

            c.updatePlayerFacedownStaleness(*(c.stale for c in pl.facedowns))

            c.updatePlayerMana(pl.mana)

            c.updateEnemyFacedownStaleness(*(c.stale for c in pl.opponent.facedowns))

            c.endRedraw()

        if self.game.requiredDecision is not None:
            effect_owner = self.game.requiredDecision.owner
            c = effect_owner.connection
            c.requestDecision(
                self.game.requiredDecision.func.__code__.co_argcount)

        for pl in self.game.players:
            for z in pl.zones:
                z.dirty = False

    def end_game(self, winner):
        for pl in self.game.players:
            if pl == winner:
                pl.connection.winGame()
            else:
                pl.connection.loseGame()

    def kick_everyone(self):
        for c in self.network_manager.connections:
            c.kick()

    def run(self):
        while 1:
            try:
                self.network_manager.recv()
            except IndexError as e:
                print(e)
            except IllegalMoveError as e:  # Client sent us an illegal move
                print(e)
                for conn in self.network_manager.connections:
                    conn.illegalMove()
                self.redraw()
            except EndOfGame as e:
                self.end_game(e.winner)
                exit(0)
            except ConnectionClosed as c:
                if c in self.network_manager.connections:
                    self.network_manager.connections.remove(c)
                # If you DC, your opponent wins
                if self.state == State.Playing:
                    try:
                        self.end_game(c.conn.player.opponent)
                    except (BrokenPipeError, ConnectionClosed):
                        # Opponent also DC'd
                        pass
                else:
                    try:
                        self.kick_everyone()
                    except (BrokenPipeError, ConnectionClosed):
                        pass
                exit(0)
            except Exception as e:  # We died due to some other error
                print(e)
                print(traceback.format_exc())
                self.kick_everyone()
                exit(1)

            time.sleep(0.01)
