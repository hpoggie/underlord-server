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

from server_event_handler import ServerEventHandler


class ServerError(Exception):
    pass


class GameServer:
    def __init__(self, netman):
        self.networkManager = netman
        netman.handoff_to(self)
        self.addrs = [c.addr for c in self.networkManager.connections]
        self.factions = [None, None]

        for conn in self.networkManager.connections:
            conn.onEnteredGame()

    #
    # Network functions
    # These must be named in camelCase for compatibility reasons
    #

    def selectFaction(self, addr, index):
        available_factions = factions.availableFactions
        self.factions[self.addrs.index(addr)] = available_factions[index]
        # If both players have selected their faction, start the game
        started = hasattr(self, 'game')
        if (None not in self.factions and
                not started and
                not hasattr(self, 'decidingPlayer')):
            # TODO: kludge
            for i in range(len(self.factions)):
                self.networkManager.connections[
                    (i + 1) % len(self.factions)].updateEnemyFaction(
                    available_factions.index(self.factions[i]))

            self.wait_on_going_first_decision()

    def decideWhetherToGoFirst(self, addr, value):
        if self.addrs.index(addr) is not self.decidingPlayer:
            print("That player doesn't get to decide who goes first.")
            return

        if value:
            first_player = self.decidingPlayer
        else:
            first_player = self.notDecidingPlayer

        self.start(first_player)
        del self.decidingPlayer
        del self.notDecidingPlayer

    def mulligan(self, addr, *cards):
        pl = self.players[addr]
        pl.mulligan(*cards)

        if pl.opponent.hasMulliganed:
            for addr, c in self.connections.items():
                c.updateBothPlayersMulliganed()
            self.redraw()
        else:
            self.connections[addr].updatePlayerHand(pl.hand)
            self.connections[addr].endRedraw()

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

    def wait_on_going_first_decision(self):
        self.decidingPlayer = random.randint(0, 1)
        self.notDecidingPlayer = (self.decidingPlayer + 1) % 2
        conn = self.networkManager.connections[self.decidingPlayer]
        conn.requestGoingFirstDecision()

    def start(self, first_player):
        second_player = (first_player + 1) % 2

        self.game = Game(self.factions[first_player],
                         self.factions[second_player],
                         ServerEventHandler(self.networkManager.connections))

        # addr->player TODO rename these
        self.players = dict([
            (self.addrs[first_player], self.game.players[0]),
            (self.addrs[second_player], self.game.players[1])])

        # connection->addr
        self.connections = dict([
            (addr, self.networkManager.connections[i])
            for i, addr in enumerate(self.addrs)])

        # connection->player, player->connection
        for i, addr in enumerate(self.addrs):
            conn = self.networkManager.connections[i]
            player = self.players[addr]
            conn.player = player
            player.connection = conn

        ndp = self.networkManager.connections[self.notDecidingPlayer]
        if first_player == self.decidingPlayer:
            ndp.enemyGoingFirst()
        else:
            ndp.enemyGoingSecond()

        self.game.start()
        self.redraw()

    def redraw(self):
        for addr, pl in self.players.items():
            c = self.connections[addr]
            enemy_player = pl.opponent

            c.setActive(int(pl.active))

            if pl.faceups.dirty:
                c.updatePlayerFaceups(pl.faceups)

            for i, card in enumerate(pl.faceups):
                if hasattr(card, 'counter'):
                    c.updatePlayerCounter(i, card.counter)

            c.updateHasAttacked(*(c.hasAttacked for c in pl.faceups))

            if enemy_player.faceups.dirty:
                c.updateEnemyFaceups(enemy_player.faceups)

            for i, card in enumerate(pl.opponent.faceups):
                if hasattr(card, 'counter'):
                    c.updateEnemyCounter(i, card.counter)

            if pl.hand.dirty:
                c.updatePlayerHand(pl.hand)
            if pl.facedowns.dirty:
                c.updatePlayerFacedowns(pl.facedowns)

            c.updatePlayerFacedownStaleness(*(c.stale for c in pl.facedowns))

            c.updatePlayerManaCap(pl.manaCap)
            c.updatePlayerMana(pl.mana)

            if enemy_player.hand.dirty:
                c.updateEnemyHand(enemy_player.hand)
            if enemy_player.facedowns.dirty:
                c.updateEnemyFacedowns(enemy_player.facedowns)

            c.updateEnemyFacedownStaleness(*(c.stale for c in pl.opponent.facedowns))

            c.updateEnemyManaCap(enemy_player.manaCap)

            if pl.graveyard.dirty:
                c.updatePlayerGraveyard(pl.graveyard)
            if enemy_player.graveyard.dirty:
                c.updateEnemyGraveyard(pl.opponent.graveyard)

            c.endRedraw()

        if self.game.requiredDecision is not None:
            effect_owner = self.game.requiredDecision.owner
            c = self.connections[next(addr for addr, player
                    in self.players.items() if player == effect_owner)]
            c.requestDecision(
                self.game.requiredDecision.func.__code__.co_argcount)

        for pl in self.game.players:
            for z in pl.zones:
                z.dirty = False

    def end_game(self, winner):
        for addr, pl in self.players.items():
            if pl == winner:
                self.connections[addr].winGame()
            else:
                self.connections[addr].loseGame()

    def kick_everyone(self):
        for c in self.networkManager.connections:
            c.kick()

    def run(self):
        while 1:
            try:
                self.networkManager.recv()
            except IndexError as e:
                print(e)
            except IllegalMoveError as e:  # Client sent us an illegal move
                print(e)
                for conn in self.networkManager.connections:
                    conn.illegalMove()
                self.redraw()
            except EndOfGame as e:
                self.end_game(e.winner)
                exit(0)
            except ConnectionClosed as c:
                if c in self.networkManager.connections:
                    self.networkManager.connections.remove(c)
                # If you DC, your opponent wins
                if hasattr(self, 'players'):
                    try:
                        self.end_game(self.players[c.conn.addr].opponent)
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
