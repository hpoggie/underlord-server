"""
Player class.
A player has the following characteristics:
    Zones
    Mana cap
    Mana
"""
from copy import deepcopy
from random import shuffle
from .enums import *

startHandSize = 5
maxManaCap = 15


class IllegalMoveError (Exception):
    pass


class Player:
    def __init__(self, faction):
        self.hand = []
        self.facedowns = []
        self.faceups = []
        self.face = ["A human face."]  # Need to have a dummy zone to attack
        self.faction = faction
        self.deck = deepcopy(faction.deck)
        for card in self.deck:
            card.owner = self
            card._zone = self.deck
        self.graveyard = []
        self._manaCap = 1
        self.mana = 1

        self.iconPath = faction.iconPath
        self.cardBack = faction.cardBack

        self.hasMulliganed = False

    @property
    def manaCap(self):
        return self._manaCap

    @manaCap.setter
    def manaCap(self, value):
        self._manaCap = value
        if self._manaCap > 15:
            self.getEnemy().win()

    def shuffle(self):
        shuffle(self.deck)

    def drawOpeningHand(self):
        for i in range(0, startHandSize):
            self.drawCard()

    def drawCard(self):
        if len(self.deck) != 0:
            self.deck[-1].zone = self.hand

    def isActivePlayer(self):
        return self.game.activePlayer == self

    def getEnemy(self):
        index = 1 if self.game.players[0] == self else 0
        return self.game.players[index]

    def getCard(self, zone, index):
        return zone[index]

    def win(self):
        self.game.end(winner=self)

    # Actions

    def mulligan(self, *cards):
        if self.hasMulliganed:
            raise IllegalMoveError("Can't mulligan twice.")

        if self.game.turn is not None:
            raise IllegalMoveError("Can only mulligan before the game has started.")

        for i in range(len(cards)):
            self.drawCard()
        for c in cards:
            c.zone = self.deck
        self.shuffle()

        self.hasMulliganed = True
        if self.getEnemy().hasMulliganed:
            self.game.finishMulligans()

    def failIfInactive(self, *args):
        if not self.isActivePlayer():
            raise IllegalMoveError("Can only play facedowns during your turn.")

    def play(self, card):
        self.failIfInactive()
        if self.game.phase != Phase.play:
            raise IllegalMoveError("""
            Can only play facedowns during play phase.""")

        if card.zone != self.hand:
            raise IllegalMoveError("""
            Can't play a card that's not in your hand.""")

        card.zone = self.facedowns
        card.hasAttacked = False

    def revealFacedown(self, card):
        self.failIfInactive()
        if self.game.phase != Phase.reveal:
            raise IllegalMoveError("""
            Can only reveal facedowns during reveal phase.""")

        if self.mana < card.cost:
            raise IllegalMoveError("Not enough mana.")

        if card.zone != self.facedowns:
            raise IllegalMoveError("Can't reveal a card that's not face-down.")

        self.mana -= card.cost
        card.zone = self.faceups

    def playFaceup(self, card):
        self.failIfInactive()
        if self.game.phase != Phase.reveal:
            raise IllegalMoveError("""
                    Can only play faceups during reveal phase.""")

        if card not in self.hand:
            raise IllegalMoveError("""
                    Can't play a card face-up that's not in hand.""")

        if not card.playsFaceUp:
            raise IllegalMoveError("That card does not play face-up.")

        if self.mana < card.cost:
            raise IllegalMoveError("Not enough mana.")

        self.mana -= card.cost
        card.zone = self.faceups

    def attack(self, attacker, target):
        self.failIfInactive()
        if attacker.hasAttacked:
            raise IllegalMoveError("Can only attack once per turn.")

        if self.game.phase != Phase.play:
            raise IllegalMoveError("Can only attack during attack phase.")

        if attacker.zone != self.faceups:
            raise IllegalMoveError("Can only attack with face-up cards.")

        taunts = [c for c in self.getEnemy().faceups if c.taunt]
        if len(taunts) > 0 and target not in taunts:
            raise IllegalMoveError("Must attack units with taunt first.")

        if target != self.getEnemy().face and target.zone not in [
                target.owner.faceups, target.owner.facedowns]:
            raise IllegalMoveError(
                "Can only attack face-up / face-down targets or a player.")

        attacker.hasAttacked = True

        if target == self.face:
            self.attackFace(attacker)
        else:
            self.game.fight(target, attacker)

    def attackFace(self, attacker):
        self.failIfInactive()
        self.getEnemy().manaCap += attacker.rank

    def endPhase(self):
        self.failIfInactive()
        self.game.endPhase()

    def endTurn(self):
        self.failIfInactive()
        while self.isActivePlayer():
            self.endPhase()
