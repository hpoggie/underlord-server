def getCard(player, card):
    """
    Convert card to index
    """
    def isVisible(c):
        return (c.zone not in (c.controller.hand, c.controller.facedowns)
                or c.visible or c.controller is player)

    return ((card.cardId if isVisible(card) else -1), card.owner is not player)


def getZone(player, zone):
    return [i for c in zone for i in getCard(player, c)]


def ZIEToCard(pl, targetZone, targetIndex, targetsEnemy):
    if targetZone == -1:
        return None

    if targetsEnemy:
        target = pl.opponent.zones[targetZone][targetIndex]
    else:
        target = pl.zones[targetZone][targetIndex]

    return target
