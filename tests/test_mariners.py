from .util import newGame
from core.player import IllegalMoveError
import factions.mariners as mariners


def testFish():
    game, p0, p1 = newGame(mariners.Mariner)
    game.start()

    p0.endTurn()

    p1.endPhase(fish=True)
    toReplace = p1.hand[:3]
    p1.fishReplace(toReplace)

    # Make sure cards are bottomdecked
    assert p1.deck[:3] == toReplace

    # Can't put back cards unless we're fishing
    try:
        p1.fishReplace(p1.hand[:3])
    except IllegalMoveError:
        pass
    else:
        assert False

    p1.endTurn()

    p0.endPhase(fish=True)

    # Have to decide what to put back
    try:
        p0.endTurn()
    except IllegalMoveError:
        pass
    else:
        assert False

    # Must put back 3
    try:
        p0.fishReplace(p1.hand[:2])
    except IllegalMoveError:
        pass
    else:
        assert False


def testAquatic():
    game, p0, p1 = newGame([mariners.nuisanceFlooding(),
                           mariners.kraken()])

    for i in range(2):
        p0.drawCard()
        p1.drawCard()

    game.start()
    p0.manaCap = 7  # Make sure we have enough to play our stuff

    p0.endPhase()
    p0.play(0)
    p0.endTurn()

    p1.endTurn()

    # We can't reveal aquatic cards
    try:
        p0.revealFacedown(0)
    except IllegalMoveError:
        pass
    else:
        assert False

    # Cheat Nuisance Flooding into play
    p0.hand[0].playsFaceUp = True
    p0.hand[0].cost = 0
    p0.playFaceup(0)

    # Try revealing the kraken again
    p0.revealFacedown(0)
