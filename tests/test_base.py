from . import dummyCards
from .util import newGame
import factions.base
from core.exceptions import InvalidTargetError


def testSweep():
    game, p1, p2 = newGame(
        [factions.base.sweep()],
        [dummyCards.one(), dummyCards.one(), dummyCards.one()])

    p1.endPhase()
    p1.play(p1.hand[0])
    p1.endPhase()

    # play 2 cards face-up and 1 face-down
    for c in p2.hand[:-1]:
        c.cost = 0
        c.playsFaceup = True
        p2.playFaceup(c)
    p2.endPhase()
    p2.play(p2.hand[0])
    p2.endPhase()

    p1.mana = 4
    p1.revealFacedown(p1.facedowns[0])

    assert len(p2.faceups) == 0
    assert len(p2.facedowns) == 1


def testMindControlTrap():
    game, p1, p2, = newGame(
        [dummyCards.one()],
        [factions.base.mindControlTrap()])

    p1.endPhase()
    p1.play(p1.hand[0])
    p1.endPhase()

    p2.endPhase()
    p2.play(p2.hand[0])
    p2.endPhase()

    p1.revealFacedown(p1.facedowns[0])
    p1.endPhase()

    attacker = p1.faceups[0]
    p1.attack(p1.faceups[0], p2.facedowns[0])

    assert(len(p1.faceups) == 0)
    assert(p2.faceups[0] == attacker)


def testSpellBlade():
    game, p0, p1 = newGame([factions.base.spellBlade()])

    p0.endPhase()
    p0.play(p0.hand[0])
    p0.endTurn()

    p1.drawCard()
    p1.mana = 3
    p1.playFaceup(p1.hand[0], "foobar")

    # If target is invalid, spell blade fizzles
    assert len(p0.hand) == 0
