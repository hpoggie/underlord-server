from factions.templars import *
from core.core import Game
from core.decision import Decision
from factions import base
from tests.dummyFaction import dummyFactionPlayer
from core.enums import *
from core.player import IllegalMoveError


def testEquus():
    dfp = dummyFactionPlayer([equus()])
    game = Game(dfp, dfp)
    game.players[0].deck[0].zone = game.players[0].faceups
    game.players[0].manaCap = 3
    assert game.players[0].faceups[0].rank == 5
    game.players[0].manaCap = 4
    assert game.players[0].faceups[0].rank == 2


def testHolyHandGrenade():
    dfp1 = dummyFactionPlayer([base.one(), base.one()])
    dfp2 = dummyFactionPlayer([holyHandGrenade(), holyHandGrenade()])
    game = Game(dfp1, dfp2)
    game.players[0].mana = 5
    game.players[0].drawCard()
    game.players[0].hand[0].playsFaceUp = True
    game.players[0].playFaceup(game.players[0].hand[0])
    game.players[0].endPhase()
    game.players[0].play(game.players[0].hand[0])
    game.players[0].endTurn()
    game.players[1].mana = 8
    game.players[1].drawCard()
    game.players[1].drawCard()

    try:
        game.players[1].playFaceup(game.players[1].hand[0])
    except Decision as d:
        d.execute(game.players[0].facedowns[0])

    assert len(game.players[0].facedowns) == 0

    try:
        game.players[1].playFaceup(game.players[1].hand[0])
    except Decision as d:
        d.execute(game.players[0].faceups[0])

    assert len(game.players[0].facedowns) == 0


def testWrathOfGod():
    dfp1 = dummyFactionPlayer([base.one(), base.one()])
    dfp2 = dummyFactionPlayer([wrathOfGod()])
    game = Game(dfp1, dfp2)
    game.players[0].drawCard()
    game.players[0].drawCard()
    game.players[0].hand[0].playsFaceUp = True
    game.players[0].hand[0].cost = 0
    game.players[0].hand[1].playsFaceUp = True
    game.players[0].hand[1].cost = 0
    game.players[0].playFaceup(game.players[0].hand[0])
    game.players[0].playFaceup(game.players[0].hand[0])
    game.players[0].endTurn()
    game.players[1].drawCard()
    game.players[1].hand[0].cost = 0
    game.players[1].playFaceup(game.players[1].hand[0])
    assert len(game.players[0].faceups) == 0


def testMiracle():
    # TODO: be able to do something like [base.one()] * 10
    # doesn't currently work because base.one() only evaluates once
    dfp1 = dummyFactionPlayer([
        base.one(),
        base.one(),
        base.one(),
        base.one(),
        base.one(),
        base.one(),
        miracle()
    ])
    dfp2 = dummyFactionPlayer([])
    game = Game(dfp1, dfp2)
    game.players[0].drawCard()
    assert len(game.players[0].hand) == 1
    game.players[0].hand[0].playsFaceUp = True
    game.players[0].hand[0].cost = 0
    game.players[0].playFaceup(game.players[0].hand[0])
    assert len(game.players[0].hand) == 5


def testMiracleNotEnoughCards():
    dfp1 = dummyFactionPlayer([
        base.one(),
        base.one(),
        miracle()
    ])
    dfp2 = dummyFactionPlayer([])
    game = Game(dfp1, dfp2)
    game.players[0].drawCard()
    assert len(game.players[0].hand) == 1
    game.players[0].hand[0].playsFaceUp = True
    game.players[0].hand[0].cost = 0
    game.players[0].playFaceup(game.players[0].hand[0])
    assert len(game.players[0].hand) == 2


def testGrail():
    dfp1 = dummyFactionPlayer([])
    dfp2 = dummyFactionPlayer([])
    game = Game(dfp1, dfp2)
    p1 = game.players[0]
    p2 = game.players[1]
    c = leftGrail()
    c.owner = p1
    c.zone = p1.faceups
    c = base.one()
    c.owner = p2
    c.zone = p2.faceups
    p2.faceups[0].hasAttacked = False
    game.turn = Turn.p2
    game.phase = Phase.play
    p1.manaCap = 3
    # Should fail if attack works
    try:
        p2.attack(p2.faceups[0], p1.face)
        assert False
    except IllegalMoveError:
        pass
    p1.manaCap = 2
    # Should fail if attack doesn't work
    p2.attack(p2.faceups[0], p1.face)
