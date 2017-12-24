from direct.showbase.DirectObject import DirectObject
from panda3d.core import TextNode
from direct.gui.DirectGui import DirectButton
from direct.gui.OnscreenText import OnscreenText
from core.enums import Phase


class Hud(DirectObject):
    def __init__(self):
        pass

    def makeFactionSelectUI(self):
        self.factionSelectLabel = OnscreenText(
            text="faction select",
            pos=(0, -0.7, 0),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)

        self.factionButtons = []

        for i, faction in enumerate(base.availableFactions):
            self.factionButtons.append(DirectButton(
                image=faction.iconPath + '/' + faction.cardBack,
                pos=(i * 0.2, 0, 0),
                scale=(0.1, 0.1, 0.1),
                relief=None,
                command=base.pickFaction,
                extraArgs=[i]))

    def makeGameUi(self):
        self.factionSelectLabel.detachNode()
        for button in self.factionButtons:
            button.destroy()
        del self.factionButtons

        self.turnLabel = OnscreenText(
            text="",
            pos=(0, -0.9, 0),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)

        self.playerManaCapLabel = OnscreenText(
            text=str(base.player.manaCap),
            pos=(-0.4, -0.44, 0),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)
        self.enemyManaCapLabel = OnscreenText(
            text=str(base.enemy.manaCap),
            pos=(-0.5, 0.77),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)
        self.cardNameLabel = OnscreenText(
            text="",
            pos=(-0.7, -0.6, 0),
            scale=0.07,
            mayChange=True)
        self.tooltipLabel = OnscreenText(
            text="",
            pos=(-0.9, -0.8, 0),
            scale=0.05,
            align=TextNode.ALeft,
            wordwrap=10,
            mayChange=True)
        self.cardStatsLabel = OnscreenText(
            text="",
            pos=(-0.7, -0.7, 0),
            scale=0.07,
            mayChange=True)
        self.endPhaseLabel = OnscreenText(
            text="",
            pos=(0.7, -0.7, 0),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)
        self.endPhaseButton = DirectButton(
            image="./end_phase.png",
            pos=(0.7, 0, -0.85),
            scale=(0.1, 0.1, 0.1),
            relief=None,
            command=base.endPhase)

    def showBigMessage(self, message):
        """
        Put huge text on the screen that obscures stuff
        """
        self.winLabel = OnscreenText(
            text=message,
            scale=(0.5, 0.5, 0.5))

    def redrawTooltips(self):
        if hasattr(self, 'cardNameLabel'):
            self.cardNameLabel.setText("")

        if hasattr(self, 'cardStatsLabel'):
            self.cardStatsLabel.setText("")

        if hasattr(self, 'tooltipLabel'):
            if hasattr(self, 'phase') and self.active:
                self.tooltipLabel.setText(
                    "Reveal face-down cards" if self.phase == Phase.reveal
                    else "Play face-down cards and attack")
            else:
                self.tooltipLabel.setText("")

    def updateCardTooltip(self, card):
        self.cardNameLabel.setText(card.name)
        label = str(card.cost) + " " + str(card.rank)
        self.cardStatsLabel.setText(label)
        self.tooltipLabel.setText(
            ("Instant. " if card.playsFaceUp else "") + card.desc)

    def redraw(self):
        if base.active:
            self.endPhaseButton.show()
        else:
            self.endPhaseButton.hide()

        if base.phase == Phase.reveal and base.active:
            self.playerManaCapLabel.setText(
                str(base.player.mana) + " / " + str(base.player.manaCap))
        else:
            self.playerManaCapLabel.setText(str(base.player.manaCap))
        self.enemyManaCapLabel.setText(str(base.enemy.manaCap))
        self.endPhaseLabel.setText(str(Phase.keys[base.phase]))
        self.turnLabel.setText("Your Turn" if base.active else "Enemy Turn")