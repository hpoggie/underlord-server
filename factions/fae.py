from core.player import Player
from core.exceptions import InvalidTargetError
from core.faction import deck
from core.card import Card
import factions.base as base


class faerieMoth(Card):
    name = "Faerie Moth"
    icon = 'butterfly.png'
    cost = 1
    rank = 1
    fast = True
    desc = "Fast."


class oberonsGuard(Card):
    name = "Oberon's Guard"
    icon = 'elf-helmet.png'
    cost = 2
    rank = 2
    desc = ("When this spawns, you may return target face-down card you "
            "control to its owner's hand.")

    def onSpawn(self, target):
        if target.zone is not self.controller.facedowns:
            raise InvalidTargetError()

        target.zone = target.owner.hand


class titaniasGuard(Card):
    name = "Titania's Guard"
    icon = 'batwing-emblem.png'
    cost = 4
    rank = 4
    desc = "When this spawns, turn target face-up unit face-down."

    def onSpawn(self, target):
        if not target.faceup or target.spell:
            raise InvalidTargetError()

        target.zone = target.controller.facedowns


class preciseDiscard(Card):
    name = "Precise Discard"
    icon = 'card-pick.png'
    cost = 2
    rank = 'il'
    desc = "Look at your opponent's hand and discard a card from it."

    def onSpawn(self):
        def discard(card):
            if card.zone is not self.controller.opponent.hand:
                raise InvalidTargetError()

            card.zone = card.owner.graveyard

        self.controller.replaceCallback = discard


class faerieDragon(Card):
    name = "Faerie Dragon"
    icon = ''
    cost = 5
    rank = 4
    desc = ("If this would be destroyed while face-up, return it to its "
            "owner's hand instead.")

    def moveToZone(self, zone):
        if self.faceup and zone is self.owner.graveyard:
            super().moveToZone(self.owner.hand)
        else:
            super().moveToZone(zone)


class Faerie(Player):
    deck = deck(
        faerieMoth, 5,
        oberonsGuard, 4,
        titaniasGuard, 2,
        preciseDiscard, 2) + base.deck

    def endPhase(self, card=None):
        self.failIfInactive()
        self.game.endPhase(keepFacedown=[card])
