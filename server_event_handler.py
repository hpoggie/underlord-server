from ul_core.core.event_handler import EventHandler


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

    def on_fizzle(self, card):
        for c in self.connections:
            c.playAnimation('on_fizzle', card)

    def on_change_controller(self, card, original, new):
        for conn in self.connections:
            conn.playAnimation('on_change_controller', card)

    def on_reveal_facedown(self, card, targets):
        for c in self.connections:
            if c.player == card.controller:
                c.updatePlayerFacedowns(card.controller.facedowns)
            else:
                c.updateEnemyFacedowns(card.controller.facedowns)

            pl = c.player
            c.playAnimation('on_reveal_facedown', card, *targets, player=pl)

    def on_play_faceup(self, card, targets):
        for c in self.connections:
            pl = c.player
            c.playAnimation('on_play_faceup', card, *targets, player=pl)

    def on_play_facedown(self, card):
        for conn in self.connections:
            conn.playAnimation('on_play_facedown', card)

    def on_draw(self, card):
        for conn in self.connections:
            conn.playAnimation('on_draw', card)

    def on_end_turn(self, game):
        for c in self.connections:
            c.playAnimation('on_end_turn')
