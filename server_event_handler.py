from ul_core.core.event_handler import EventHandler
from ul_core.net.network import ClientNetworkManager
from ul_core.net.zie import gameEntityToZie

from conversions import getCard


def playAnimation(conn, name, *args):
    conn.playAnimation(getattr(ClientNetworkManager.Animations, name), *args)


def expandTargets(pl, targets):
    return (i for t in targets for i in gameEntityToZie(pl, t))


class ServerEventHandler(EventHandler):
    def __init__(self, connections):
        super().__init__()
        self.connections = connections

    def on_spawn(self, card):
        for c in self.connections:
            playAnimation(c, 'on_spawn', card.zone.index(card))

    def on_fight(self, c1, c2):
        for conn in self.connections:
            pl = conn.player
            playAnimation(conn, 'on_fight', *(gameEntityToZie(pl, c1) + gameEntityToZie(pl, c2)))

    def on_die(self, card):
        for c in self.connections:
            playAnimation(c, 'on_die', card.zone.index(card))

    # TODO
    def on_change_controller(self, card, original, new):
        #for conn in self.connections:
            #playAnimation(conn, 'on_change_controller', card.cardId,
                          #self.players.index(original), self.players.index(new))
        pass

    def on_reveal_facedown(self, card, targets):
        for c in self.connections:
            pl = c.player
            playAnimation(c, 'on_reveal_facedown', card.zone.index(card),
                          *expandTargets(pl, targets))

    def on_play_faceup(self, card, targets):
        for c in self.connections:
            pl = c.player
            playAnimation(c, 'on_play_faceup', card.zone.index(card),
                          *expandTargets(pl, targets))

    def on_play_facedown(self, card):
        # TODO: do this for both players
        playAnimation(card.owner.connection, 'on_play_facedown', *getCard(card.owner, card))
        #playAnimation(self.connections[card.owner], 'on_play_facedown_invisible')
        pass

    def on_draw(self, card):
        #playAnimation(self.connections[card.owner], 'on_draw_visible', card.cardId)
        #playAnimation(self.connections[card.owner], 'on_draw_invisible', card.cardId)
        pass

    def on_end_turn(self, game):
        for c in self.connections:
            playAnimation(c, 'on_end_turn')
