from ul_core.core.event_handler import EventHandler
from ul_core.net.network import ClientNetworkManager


def playAnimation(conn, name, *args):
    conn.playAnimation(getattr(ClientNetworkManager.Animations, name), *args)


class ServerEventHandler(EventHandler):
    def __init__(self, connections):
        super().__init__()
        self.connections = connections

    def on_spawn(self, card):
        for c in self.connections:
            playAnimation(c, 'on_spawn', card.zone.index(card))

    def on_fight(self, c1, c2):
        for conn in self.connections:
            playAnimation(conn, 'on_fight', *(getCard(c1) + getCard(c2)))

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
        #for c in self.connections:
        #    playAnimation(c, 'on_reveal_facedown', card.cardId, MUNGE(targets))  # TODO
        pass

    def on_play_faceup(self, card, targets):
        #for c in self.connections:
            #playAnimation(c, 'on_play_faceup', card.cardId, MUNGE(targets))  # TODO
        pass

    def on_play_facedown(self, card):
        #playAnimation(self.connections[card.owner], 'on_play_facedown_visible', card.cardId)
        #playAnimation(self.connections[card.owner], 'on_play_facedown_invisible')
        pass

    def on_draw(self, card):
        #playAnimation(self.connections[card.owner], 'on_draw_visible', card.cardId)
        #playAnimation(self.connections[card.owner], 'on_draw_invisible', card.cardId)
        pass

    def on_end_turn(self, game):
        for c in self.connections:
            playAnimation(c, 'on_end_turn')
