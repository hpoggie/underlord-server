"""
This is the client script. It takes game data and draws it on the screen.
It also takes user input and turns it into game actions.
"""

from direct.showbase.ShowBase import ShowBase
from panda3d.core import CollisionTraverser, CollisionHandlerQueue

from network import ClientNetworkManager, ServerNetworkManager
from server import Zone
from core.enums import Phase

from panda3d.core import loadPrcFileData
from direct.task import Task
from factions import templars

import sys
from client.mouse import MouseHandler
from client.zoneMaker import ZoneMaker
from client.hud import Hud
from client.connectionManager import ConnectionManager
import client.networkInstructions

loadPrcFileData(
    "",
    """
    win-size 500 500
    window-title Overlord
    fullscreen 0
    """)


class IllegalMoveError (Exception):
    pass


class App (ShowBase):
    def __init__(self, argv):
        ShowBase.__init__(self)

        self.scene = self.render.attachNewNode('empty')
        self.scene.reparentTo(self.render)

        base.cTrav = CollisionTraverser()
        self.handler = CollisionHandlerQueue()
        self.mouseHandler = MouseHandler()

        self.taskMgr.add(self.mouseHandler.mouseOverTask, "MouseOverTask")

        self._active = False
        self._started = False

        self.availableFactions = [templars.Templars]

        self.hud = Hud()

        # Connect to the default server if no argument provided
        ip = argv[1] if len(argv) > 1 else "174.138.119.84"
        port = 9099
        self.serverAddr = (ip, port)

        instr = client.networkInstructions.NetworkInstructions()

        self.networkManager = ClientNetworkManager(instr, ip)

        self.connectionManager = ConnectionManager(self.serverAddr, instr)
        self.connectionManager.tryConnect()
        self.taskMgr.add(self.networkUpdateTask, "NetworkUpdateTask")

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, value):
        self._active = value
        if not self._started:
            self.startGame()
            self._started = True

    def pickFaction(self, index):
        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.selectFaction,
            index)

        self.faction = self.availableFactions[index]

    def startGame(self):
        self.player = self.faction.player(self.faction)
        self.enemy = self.enemyFaction.player(self.enemyFaction)
        self.phase = Phase.reveal

        self.playerIconPath = self.faction.iconPath
        self.enemyIconPath = self.enemyFaction.iconPath
        self.playerCardBack = self.faction.cardBack
        self.enemyCardBack = self.enemyFaction.cardBack

        self.hud.makeGameUi()
        self.zoneMaker = ZoneMaker()

    def findCard(self, card):
        enemy = True
        index = -1
        zone = -1
        try:
            if card.getTag('zone') == 'face-down':
                index = self.playerFacedownNodes.index(card)
                zone = Zone.facedown
                enemy = False
            elif card.getTag('zone') == 'enemy face-down':
                index = self.enemyFacedownNodes.index(card)
                zone = Zone.facedown
            elif card.getTag('zone') == 'face-up':
                # TODO: hack
                # Search player faceup nodes to see if we own the card
                if card in self.playerFaceupNodes:
                    index = self.playerFaceupNodes.index(card)
                    enemy = False
                else:
                    index = self.enemyFaceupNodes.index(card)
                zone = Zone.faceup
            elif card.getTag('zone') == 'hand':
                index = self.playerHandNodes.index(card)
                zone = Zone.hand
                enemy = False
            elif card.getTag('zone') == 'face':
                zone = Zone.face
                if card is self.playerFaceNode:  # TODO: hack
                    enemy = False
        except ValueError as e:
            print(e)

        return (zone, index, enemy)

    def acceptTarget(self, target):
        targetZone, targetIndex, targetsEnemy = self.findCard(target)

        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.acceptTarget,
            int(targetsEnemy),
            targetZone,
            targetIndex)

    def playCard(self, handCard):
        if self.phase == Phase.reveal:
            self.networkManager.sendInts(
                self.serverAddr,
                ServerNetworkManager.Opcodes.playFaceup,
                self.playerHandNodes.index(handCard)
            )
        else:
            self.networkManager.sendInts(
                self.serverAddr,
                ServerNetworkManager.Opcodes.play,
                self.playerHandNodes.index(handCard)
            )
        self.zoneMaker.makePlayerHand()
        self.zoneMaker.makeBoard()

    def revealFacedown(self, card):
        if card not in self.playerFacedownNodes:
            raise IllegalMoveError("That card is not one of your facedowns.")
        index = self.playerFacedownNodes.index(card)
        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.revealFacedown,
            index
        )
        self.zoneMaker.makePlayerHand()
        self.zoneMaker.makeBoard()

    def attack(self, card, target):
        if target == self.playerFaceNode:
            print("Can't attack yourself.")
            return
        if target in self.playerFaceupNodes:
            print("Can't attack your own faceups.")
            return

        zone, index, enemy = self.findCard(target)
        targetZone, targetIndex, targetsEnemy = self.findCard(target)

        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.attack,
            index,
            targetIndex,
            targetZone
        )

        self.zoneMaker.makePlayerHand()
        self.zoneMaker.makeBoard()
        self.zoneMaker.makeEnemyBoard()

    def endPhase(self):
        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.endPhase
        )

    def redraw(self):
        self.zoneMaker.redrawAll()
        self.hud.redraw()

    def networkUpdateTask(self, task):
        self.networkManager.recv()
        return Task.cont


app = App(sys.argv)
app.camera.setPosHpr(4, -15, -15, 0, 45, 0)
app.run()
