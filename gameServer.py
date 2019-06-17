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

    # actions

    def selectFaction(self, addr, index):
        availableFactions = factions.availableFactions
        self.factions[self.addrs.index(addr)] = availableFactions[index]
        # If both players have selected their faction, start the game
        started = hasattr(self, 'game')
        if (None not in self.factions and
                not started and
                not hasattr(self, 'decidingPlayer')):
            # TODO: kludge
            for i in range(len(self.factions)):
                self.networkManager.connections[
                    (i + 1) % len(self.factions)].updateEnemyFaction(
                    availableFactions.index(self.factions[i]))

            self.waitOnGoingFirstDecision()

    def waitOnGoingFirstDecision(self):
        self.decidingPlayer = random.randint(0, 1)
        self.notDecidingPlayer = (self.decidingPlayer + 1) % 2
        conn = self.networkManager.connections[self.decidingPlayer]
        conn.requestGoingFirstDecision()

    def decideWhetherToGoFirst(self, addr, value):
        if self.addrs.index(addr) is not self.decidingPlayer:
            print("That player doesn't get to decide who goes first.")
            return

        if value:
            firstPlayer = self.decidingPlayer
        else:
            firstPlayer = self.notDecidingPlayer

        self.start(firstPlayer)
        del self.decidingPlayer
        del self.notDecidingPlayer

    def start(self, firstPlayer):
        secondPlayer = (firstPlayer + 1) % 2

        self.game = Game(self.factions[firstPlayer],
                         self.factions[secondPlayer],
                         ServerEventHandler(self.networkManager.connections))

        # addr->player TODO rename these
        self.players = dict([
            (self.addrs[firstPlayer], self.game.players[0]),
            (self.addrs[secondPlayer], self.game.players[1])])

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
        if firstPlayer == self.decidingPlayer:
            ndp.enemyGoingFirst()
        else:
            ndp.enemyGoingSecond()

        self.game.start()
        self.redraw()

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

    def useThiefAbility(self, addr, discardIndex, cardname, targetIndex):
        pl = self.players[addr]
        pl.thiefAbility(
            pl.hand[discardIndex],
            cardname,
            pl.opponent.facedowns[targetIndex])
        self.redraw()

    def redraw(self):
        for addr, pl in self.players.items():
            c = self.connections[addr]
            enemyPlayer = pl.opponent

            c.setActive(int(pl.active))

            if pl.faceups.dirty:
                c.updatePlayerFaceups(pl.faceups)

            for i, card in enumerate(pl.faceups):
                if hasattr(card, 'counter'):
                    c.updatePlayerCounter(i, card.counter)

            c.updateHasAttacked(*(c.hasAttacked for c in pl.faceups))

            if enemyPlayer.faceups.dirty:
                c.updateEnemyFaceups(enemyPlayer.faceups)

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

            if enemyPlayer.hand.dirty:
                c.updateEnemyHand(enemyPlayer.hand)
            if enemyPlayer.facedowns.dirty:
                c.updateEnemyFacedowns(enemyPlayer.facedowns)

            c.updateEnemyFacedownStaleness(*(c.stale for c in pl.opponent.facedowns))

            c.updateEnemyManaCap(enemyPlayer.manaCap)

            if pl.graveyard.dirty:
                c.updatePlayerGraveyard(pl.graveyard)
            if enemyPlayer.graveyard.dirty:
                c.updateEnemyGraveyard(pl.opponent.graveyard)

            c.endRedraw()

        if self.game.requiredDecision is not None:
            effectOwner = self.game.requiredDecision.owner
            c = self.connections[next(addr for addr, player
                    in self.players.items() if player == effectOwner)]
            c.requestDecision(
                self.game.requiredDecision.func.__code__.co_argcount)

        for pl in self.game.players:
            for z in pl.zones:
                z.dirty = False


    def endGame(self, winner):
        for addr, pl in self.players.items():
            if pl == winner:
                self.connections[addr].winGame()
            else:
                self.connections[addr].loseGame()

    def kickEveryone(self):
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
                self.endGame(e.winner)
                exit(0)
            except ConnectionClosed as c:
                if c in self.networkManager.connections:
                    self.networkManager.connections.remove(c)
                # If you DC, your opponent wins
                if hasattr(self, 'players'):
                    try:
                        self.endGame(self.players[c.conn.addr].opponent)
                    except (BrokenPipeError, ConnectionClosed):
                        # Opponent also DC'd
                        pass
                else:
                    try:
                        self.kickEveryone()
                    except (BrokenPipeError, ConnectionClosed):
                        pass
                exit(0)
            except Exception as e:  # We died due to some other error
                print(e)
                print(traceback.format_exc())
                self.kickEveryone()
                exit(1)

            time.sleep(0.01)
