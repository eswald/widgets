import datetime

import aiosqlite

import widgets.idencoder


class ConnectionManager:
    def __init__(self, database, loop):
        self.dbfilename = database
        self.loop = None
        self.alphabets = {}

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

    async def get_alphabet(self, prefix, store=True):
        if prefix in self.alphabets:
            return self.alphabets[prefix]
        
        async with self.connect() as db:
            alphabet = None
            query = "SELECT alphabet FROM alphabets WHERE prefix = ? LIMIT 1"
            async with db.execute(query, (prefix,)) as cursor:
                async for row in cursor:
                    alphabet = row[0]
            
            if alphabet is None:
                alphabet = widgets.idencoder.random_alphabet()
                if not store:
                    return alphabet
                
                query = f"""
                    INSERT INTO alphabets (prefix, alphabet)
                    VALUES (?, ?)
                """
                cursor = await db.execute(query, (prefix, alphabet))
                await db.commit()
        
        self.alphabets[prefix] = alphabet
        return alphabet
    
    async def encode_id(self, prefix, item_id):
        alphabet = await self.get_alphabet(prefix)
        code = widgets.idencoder.encode(item_id, alphabet)
        return f"{prefix}-{code}"
    
    async def decode_id(self, code, default=None):
        if "-" in code:
            prefix, encoded = code.split("-", 1)
            alphabet = await self.get_alphabet(prefix, store=False)
            item_id = widgets.idencoder.decode(encoded, alphabet, default)
        else:
            prefix = None
            item_id = default
        return prefix, item_id
