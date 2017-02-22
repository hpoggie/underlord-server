import base
from core.card import Card, Faction


def failIfTaunts(self, attacker, target):
    if target == Zone.face:
        for card in self.getEnemy().facedowns:
            if hasattr(card, 'Taunt') and card.Taunt:
                raise IllegalMoveError("Can't attack into Taunts.")


def setup(game):
    for player in game.players:
        player.attack.funcs.insert(0, failIfTaunts)


def strix():
    return Card(
        name="Strix",
        image="owl.png",
        cost=1,
        rank=1
        )


def equus():
    def equusGetRank(self):
        return 2 if (self.owner.manaCap % 2 == 0) else 5

    equus = Card(
        name="Equus",
        image="horse-head.png",
        cost=3,
        )
    equus.setRankAbility(equusGetRank)

    return equus


def grail():
    class Grail(Card):
        @property
        def Taunt(self):
            return self.owner.manaCap % 2 == 0

    grail = Grail(
        name="Grail",
        image="holy-grail.png"
        )
    return grail

Templars = Faction(
    name="Templars",
    iconPath="./templar_icons",
    cardBack="templar-shield.png",
    deck=[
        base.one(), base.one(), base.one(), base.one(),
        base.sweep(), base.sweep(),
        base.spellBlade(),
        strix(),
        equus(),
        equus(),
        grail()
        ],
    setup=setup
    )