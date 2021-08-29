import json
import uuid

import tornado.web


class AuthorizedRequestHandler(tornado.web.RequestHandler):
    def initialize(self, dbmanager):
        self.dbmanager = dbmanager
    
    async def prepare(self):
        self.account_id = None
        self.account_code = None
        auth = self.request.headers.get('Authorization')
        if auth and auth.startswith('Bearer '):
            token = auth.split(" ", 1)[1]
            async with self.dbmanager.connect() as db:
                query = """
                    SELECT account_id
                    FROM tokens
                    WHERE token = ?
                    LIMIT 1
                """
                async with db.execute(query, (token,)) as cursor:
                    async for row in cursor:
                        self.account_id = row[0]
            if self.account_id is not None:
                encoder = self.dbmanager.encode_id
                self.account_code = await encoder("account", self.account_id)
    
    def write_error(self, status_code, **kwargs):
        self.write({'error': 'Internal Error'})


class AccountHandler(AuthorizedRequestHandler):
    async def get(self):
        if not self.account_id:
            self.set_status(401)
            self.write({'error': 'Not Authorized'})
            return
        
        fields = ["name", "created", "updated"]
        
        accounts = []
        async with self.dbmanager.connect() as db:
            query = f"""
                SELECT {', '.join(fields)}
                FROM accounts
                WHERE id = ?
            """
            async with db.execute(query, (self.account_id,)) as cursor:
                async for row in cursor:
                    accounts.append(dict(zip(fields, row)))
        
        for account in accounts:
            account['id'] = self.account_code
        
        self.write({
            'account': accounts,
        })

    async def post(self):
        # Create a new account, with a new random auth token.
        try:
            post = json.loads(self.request.body)
            assert isinstance(post, dict)
        except Exception:
            self.set_status(400)
            self.write({'error': 'Invalid json request'})
            return
        
        name = post.get("name")
        if not name:
            self.set_status(400)
            self.write({'error': 'name is required'})
            return
        
        async with self.dbmanager.connect() as db:
            now = self.dbmanager.now()
            query = """
                INSERT INTO accounts (name, created, updated)
                VALUES (?, ?, ?)
            """
            cursor = await db.execute(query, (name, now, now))
            account_id = cursor.lastrowid
            
            token = str(uuid.uuid4())
            query = """
                INSERT INTO tokens (account_id, token, created, updated)
                VALUES (?, ?, ?, ?)
            """
            params = (account_id, token, now, now)
            cursor = await db.execute(query, params)
            
            await db.commit()
        
        account_code = await self.dbmanager.encode_id("account", account_id)
        self.write({
            'account': account_code,
            'token': token,
        })
