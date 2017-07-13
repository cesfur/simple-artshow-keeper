
class Attendee:
    REG_ID = 'RegId'
    NICKNAME = 'Nickname'

    ALL_PERSISTENT = sorted([REG_ID, NICKNAME])

    @classmethod
    def load(cls, d):
        new = cls()
        new.__dict__.update(d)
        return new

    def __repr__(self):
        nick = getattr(self, self.NICKNAME)
        if nick is not None and len(nick) > 0:
            return '{id} ({nick})'.format(nick=nick, id=getattr(self, self.REG_ID))
        else:
            return str(getattr(self, self.REG_ID))
