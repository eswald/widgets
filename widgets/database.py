import datetime

import aiosqlite


class ConnectionManager:
    def __init__(self, database, loop):
        self.dbfilename = database
        self.loop = None

    def connect(self):
        return aiosqlite.connect(self.dbfilename, loop=self.loop)

    @staticmethod
    def now():
        return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    
    async def insert_row(self, table, **fields):
        keys, values = zip(*fields.items())
        query = f"""
            INSERT INTO {table} ({', '.join(keys)})
            VALUES ({', '.join('?' for key in keys)})
        """
        async with self.connect() as db:
            cursor = await db.execute(query, values)
            item_id = cursor.lastrowid
            await db.commit()
        
        return item_id
