

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
        return '{nick} [{id}]'.format(nick=getattr(self, self.NICKNAME), id=getattr(self, self.REG_ID))
