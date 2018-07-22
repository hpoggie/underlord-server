from core.card import Card
import factions.fae as fae
from .util import newGame
from . import dummyCards


def test_fae_ability():
    game, p0, p1 = newGame(fae.Faerie)
    game.start()
    p0.hand[0].zone = p0.facedowns
    p0.hand[0].zone = p0.facedowns
    p0.endPhase(p0.facedowns[0])
    assert len(p0.facedowns) == 1


def test_illusions():
    game, p0, p1 = newGame()

    class DummyIllusion(Card):
        name = "Dummy Illusion"
        cost = 1
        rank = 'il'

    one = dummyCards.one(owner=p0, game=game)
    one.zone = p0.faceups
    di = DummyIllusion(owner=p1, game=game)
    assert di.illusion
    di.zone = p1.facedowns

    p0.endPhase()
    p0.attack(one, di)

    assert di.zone == p1.graveyard
