from core.player import Player
from factions import base
from factions.templars import Templars
from .util import newGame


def deckContainsDuplicates(deck):
    for i, card in enumerate(deck):
        for card2 in deck[i + 1:]:
            if card == card2:
                return True
    return False


def testForDuplicates():
    player = Player(Templars)
    assert not deckContainsDuplicates(player.deck)


def testForDuplicatesBetweenPlayers():
    player1 = Player(Templars)
    player2 = Player(Templars)

    for card1 in player1.deck:
        for card2 in player2.deck:
            assert card1 != card2


def testReveal():
    game, player, p1 = newGame(base.one())
    player.endPhase()  # draw the card
    newCard = player.hand[0]
    player.play(newCard)
    player.endPhase()
    p1.endTurn()
    player.revealFacedown(newCard)
    assert newCard.zone == player.faceups


def testPlay():
    game, player, _ = newGame(base.one())
    player.endPhase()
    newCard = player.hand[0]
    player.play(newCard)
    assert newCard.zone == player.facedowns


def testPlayFaceup():
    newCard = base.one()
    newCard.playsFaceUp = True
    newCard.cost = 0
    game, player, _ = newGame(newCard)
    player.drawCard()
    instance = player.hand[0]
    player.playFaceup(instance)
    assert instance.zone == player.faceups


def testAttackFace():
    newCard = base.one()
    newCard.playsFaceUp = True
    newCard.cost = 0
    game, player, _ = newGame(newCard)
    player.drawCard()
    player.playFaceup(player.hand[0])
    player.endPhase()
    player.attackFace(player.faceups[0])
    assert game.players[1].manaCap == 2


def testAttackFacedown():
    newCard = base.one()
    newCard.playsFaceUp = True
    newCard.cost = 0
    game, p0, p1 = newGame(newCard)
    game.start()
    # 1st player plays a facedown
    p0.endPhase()
    p0.play(game.players[0].hand[0])
    p0.endTurn()
    # 2nd player attacks it
    p1.playFaceup(p1.hand[0])
    p1.endPhase()
    p1.attack(p1.faceups[0], p0.facedowns[0])
    assert len(p0.facedowns) == 0
    assert len(p1.faceups) == 0


def testAttackFaceup():
    newCard = base.one()
    newCard.playsFaceUp = True
    newCard.cost = 0
    game, p0, p1 = newGame(newCard)
    game.start()
    # 1st player plays a faceup
    p0.playFaceup(p0.hand[0])
    p0.endTurn()
    # 2nd player attacks it
    p1.playFaceup(p1.hand[0])
    p1.endPhase()
    p1.attack(p1.faceups[0], p0.faceups[0])
    assert len(p0.facedowns) == 0
    assert len(p1.faceups) == 0
