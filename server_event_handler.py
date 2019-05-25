from ul_core.core.event_handler import EventHandler
from ul_core.net.network import ClientNetworkManager


class ServerEventHandler(EventHandler):
    def __init__(self, connections):
        super().__init__()
        self.connections = connections

    def on_spawn(self, card):
        for c in self.connections:
            c.playAnimation('on_spawn', card)

    def on_fight(self, c1, c2):
        for conn in self.connections:
            pl = conn.player
            conn.playAnimation('on_fight', c1, c2)

    def on_die(self, card):
        for c in self.connections:
            c.playAnimation('on_die', card)

    # TODO
    def on_change_controller(self, card, original, new):
        #for conn in self.connections:
            #playAnimation(conn, 'on_change_controller', card.cardId,
                          #self.players.index(original), self.players.index(new))
        pass

    def on_reveal_facedown(self, card, targets):
        for c in self.connections:
            pl = c.player
            c.playAnimation('on_reveal_facedown', card, targets)

    def on_play_faceup(self, card, targets):
        for c in self.connections:
            pl = c.player
            c.playAnimation('on_play_faceup', card, targets)

    def on_play_facedown(self, card):
        # TODO: do this for both players
        card.owner.connection.playAnimation('on_play_facedown', card)
        #playAnimation(self.connections[card.owner], 'on_play_facedown_invisible')
        pass

    def on_draw(self, card):
        #playAnimation(self.connections[card.owner], 'on_draw_visible', card.cardId)
        #playAnimation(self.connections[card.owner], 'on_draw_invisible', card.cardId)
        pass

    def on_end_turn(self, game):
        for c in self.connections:
            c.playAnimation('on_end_turn')
