import types
from . import base
from core.player import Player, IllegalMoveError
from core.card import Card, card
from core.game import destroy
from core.faction import deck


class MultiattackCard(Card):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._attackedTargets = []

    def onSpawn(self):
        self._attackedTargets = []

    def afterEndTurn(self):
        self._attackedTargets = []

    def attack(self, target):
        if target in self._attackedTargets:
            raise IllegalMoveError("Can't attack the same target twice.")

        super().attack(target)
        self._attackedTargets.append(target)

    @property
    def hasAttacked(self):
        return len(self._attackedTargets) == self.nAttacks

    @hasAttacked.setter
    def hasAttacked(self, value):
        pass


def multiattackCard(**kwargs):
    return card(MultiattackCard, **kwargs)


def spectralCrab():
    @property
    def rank(self):
        return 4 if self.facedown else 2

    return card(
        name="Spectral Crab",
        image='crab.png',
        cost=2,
        rank=rank,
        desc="Has rank 4 while face-down.")


def timeBeing():
    def onSpawn(self):
        self.controller.takeExtraTurn()

    return card(
        name="Time Being",
        image='dead-eye.png',
        cost=12,
        rank=3,
        onSpawn=onSpawn,
        desc="When this spawns, take an extra turn after this one.")


def spellScalpel():
    def onSpawn(self, target):
        destroy(target)
        self.controller.drawCard()

    return card(
        name="Spell Scalpel",
        image='scalpel-strike.png',
        cost=5,
        rank='s',
        onSpawn=onSpawn,
        desc="Destroy target card. Draw a card.")


def fog():
    return card(
        name="Fog",
        image='frog.png',
        cost=1,
        rank=1,
        isValidTarget=False,
        desc="This can't be the target of spells or abilities.")


def hydra():
    return multiattackCard(
        name="Hydra",
        image='hydra.png',
        cost=6,
        rank=3,
        nAttacks=3,
        desc="Can attack up to 3 different targets per turn.")


def doubleDragon():
    return multiattackCard(
        name="Double Dragon",
        image='double-dragon.png',
        cost=4,
        rank=2,
        nAttacks=2,
        desc="Can attack up to 2 different targets per turn.")


def headLightning():
    def onSpawn(self):
        self.controller.drawCards(3)
        self.controller.requireReplace(self)

    def replace(self, c1, c2):
        self.controller.topdeck([c1, c2])

    return card(
        name="Head Lightning",
        image='brainstorm.png',
        cost=1,
        rank='s',
        onSpawn=onSpawn,
        replace=replace,
        desc="Draw 3 cards, then put 2 cards from your hand on top of"
             "your deck.")


def roseEmblem():
    def onSpawn(self):
        self.controller.drawCards(2)

    def onDiscard(self):
        self.controller.drawCard()

    return card(
        name="Rose Emblem",
        image='rose.png',
        cost=3,
        rank='s',
        onSpawn=onSpawn,
        onDiscard=onDiscard,
        desc="Draw 2 cards. When you discard this from your hand, draw a card.")


def spellHound():
    def onSpawn(self):
        for c in self.controller.opponent.hand:
            c.visible = True

    def afterEndPhase(self):
        for c in self.controller.opponent.hand:
            c.visible = False

    return card(
        name="Spell Hound",
        image='wolf-howl.png',
        cost=3,
        rank=2,
        onSpawn=onSpawn,
        afterEndPhase=afterEndPhase,
        desc="When this spawns, look at your opponent's hand.")


def daggerEmblem():
    def onSpawn(self, target):
        if (target.faceup and not target.spell):
            destroy(target)

    def onDiscard(self):
        self.controller.drawCard()

    return card(
        name="Dagger Emblem",
        image='stiletto.png',
        cost=2,
        rank='s',
        onSpawn=onSpawn,
        onDiscard=onDiscard,
        desc="Destroy target face-up unit. When you discard this from your"
             " hand, draw a card.")


def heavyLightning():
    def afterFight(self, c2):
        self.cost = 5

    def onSpawn(self):
        for c in self.controller.opponent.facedowns[:]:
            destroy(c)
        for c in self.controller.opponent.faceups[:]:
            destroy(c)

        self.controller.drawCards(3)

    return card(
        name="Heavy Lightning",
        image='heavy-lightning.png',
        cost=11,
        rank='s',
        onSpawn=onSpawn,
        desc="Destroy all your opponent's face-up units and face-down"
             " cards. Draw 3 cards. When this is attacked, its cost"
             " becomes 5.")


class Thief(Player):
    name = "Thieves"
    iconPath = "thief_icons"
    cardBack = "dagger-rose.png"
    deck = deck(
        base.elephant,
        fog, 5,
        spectralCrab, 4,
        spellHound, 3,
        doubleDragon, 2,
        headLightning, 2,
        roseEmblem,
        daggerEmblem,
        hydra,
        timeBeing,
        heavyLightning,
        spellScalpel) + base.deck

    def thiefAbility(self, discard, name, target):
        self.failIfInactive()

        if target.zone is not self.opponent.facedowns:
            raise IllegalMoveError("Invalid target.")

        if target.name == name:
            target.zone = self.faceups
        else:
            target.visible = True
