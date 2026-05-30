class RiskManager:

    def __init__(self):
        self.max_daily_loss = 0.05
        self.current_loss = 0
        self.exposure = 0

    def validate(self, signal, balance):

        if self.current_loss > self.max_daily_loss * balance:
            return "BLOCKED"

        if self.exposure > balance * 0.3:
            return "BLOCKED"

        return "OK"