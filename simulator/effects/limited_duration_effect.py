from simulator.effects.effect import Effect
class LimitedDurationEffect(Effect):
    def __init__(self, rounds):
       self.rounds = rounds


    def new_round(self):
        self.rounds -= 1
        if self.rounds <= 0:
            self.deactivate()