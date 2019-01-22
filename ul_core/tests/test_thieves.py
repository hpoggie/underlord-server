from .util import newGame
import factions.base as base
import factions.thieves as thieves
from ul_core.core.exceptions import IllegalMoveError, InvalidTargetError


def testThiefAbility():
    game, p0, p1 = newGame(thieves.Thief)
    game.start()

    p0.endTurn()
    p1.endPhase()
    p1.endPhase()
    c = next(c for c in p1.deck + p1.hand if c.name == 'Elephant')
    c.zone = p1.facedowns

    p1.endTurn()
    p0.thiefAbility(p0.hand[0], 'Elephant', c)
    assert c.zone is p0.faceups

    try:
        p0.thiefAbility(p0.hand[0], 'Elephant', c)
    except IllegalMoveError:
        pass
    else:
        assert False


def testThiefAbilityWrongGuess():
    game, p0, p1 = newGame(thieves.Thief)
    game.start()

    p0.endTurn()
    p1.endPhase()
    p1.endPhase()
    c = next(c for c in p1.deck + p1.hand if c.name == 'Elephant')
    c.zone = p1.facedowns

    p1.endTurn()

    p0.thiefAbility(p0.hand[0], 'Corvus', c)
    assert c.zone is p1.facedowns

    try:
        p0.thiefAbility(p0.hand[0], 'Corvus', c)
    except IllegalMoveError:
        pass
    else:
        assert False


def testThiefAbilityWrongPhase():
    game, p0, p1 = newGame(thieves.Thief)
    game.start()

    p0.endTurn()
    p1.endPhase()
    p1.endPhase()
    c = next(c for c in p1.deck + p1.hand if c.name == 'Sweep')
    c.zone = p1.facedowns

    p1.endTurn()
    p0.endPhase()

    try:
        p0.thiefAbility(p0.hand[0], 'Sweep', c)
    except IllegalMoveError:
        pass
    else:
        assert False

def testHydra():
    game, p0, p1 = newGame(
        [thieves.hydra()],
        [thieves.fog() for i in range(4)])
    game.start()

    hydra = p0.hand[0]
    hydra.zone = p0.faceups
    for c in p1.hand[:]:
        c.zone = p1.faceups

    p0.endPhase()
    for i in range(3):
        p0.attack(hydra, p1.faceups[0])

    assert len(p1.faceups) == 1
    try:
        p0.attack(hydra, p1.faceups[0])
    except IllegalMoveError:
        pass
    else:
        assert False


def testHeadLightning():
    game, p0, p1 = newGame(thieves.Thief)

    hl = next(c for c in p0.deck if c.name == "Head Lightning")
    hl.zone = p0.hand
    hl.fast = True

    oldHandSize = len(p0.hand)
    p0.playFaceup(hl)
    assert len(p0.hand) == oldHandSize + 2  # Play 1, draw 3
    p0.replace(p0.hand[0], p0.hand[1])
    assert len(p0.hand) == oldHandSize


def test_head_lightning_weird_targets():
    game, p0, p1 = newGame(thieves.Thief)

    hl = next(c for c in p0.deck if c.name == "Head Lightning")
    hl.zone = p0.hand
    hl.fast = True

    scs = [c for c in p1.deck if c.name == "Spectral Crab"][:2]
    for sc in scs:
        sc.zone = p1.faceups

    p0.playFaceup(hl)
    try:
        p0.replace(p1.faceups[0], p1.faceups[1])
    except InvalidTargetError:
        pass
    else:
        assert False


def testEmblem():
    game, p0, p1 = newGame([thieves.roseEmblem() for i in range(2)])

    emblem = p0.deck[0]
    emblem.zone = p0.hand
    emblem.zone = p0.graveyard
    assert len(p0.hand) == 1


def testHeavyLightning():
    game, p0, p1 = newGame([thieves.heavyLightning()],
            [thieves.fog() for i in range(5)])
    game.start()

    p0.deck[:] = [thieves.fog() for i in range(5)]
    for c in p0.deck:
        c.owner = p0
        c._zone = p0.deck

    for c in p1.hand[:2]:
        c.zone = p1.faceups

    for c in p1.hand[:]:
        c.zone = p1.facedowns

    ltng = p0.hand[0]
    p0.mana = 11
    ltng.fast = True
    p0.playFaceup(ltng)

    assert len(p1.faceups) == 0
    assert len(p1.facedowns) == 0
    assert len(p0.hand) == 3


def test_time_being():
    game, p0, p1 = newGame()

    tb = thieves.timeBeing(owner=p0, game=game, zone=p0.facedowns)
    p0.mana = tb.cost
    p0.revealFacedown(tb)

    p0.endTurn()

    assert p0.active
    assert p0.mana == p0.manaCap
