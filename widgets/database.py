import datetime

import aiosqlite


def now():
    return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)


class ConnectionManager:
    def __init__(self, database, loop):
        self.dbfilename = database
        self.loop = None

    def connect(self):
        return aiosqlite.connect(self.dbfilename, loop=self.loop)
