import json
import uuid

import tornado.web


class AuthorizedRequestHandler(tornado.web.RequestHandler):
    def initialize(self, dbmanager):
        self.dbmanager = dbmanager
    
    async def prepare(self):
        self.organization_id = None
        self.organization_code = None
        auth = self.request.headers.get('Authorization')
        if auth and auth.startswith('Bearer '):
            token = auth.split(" ", 1)[1]
            async with self.dbmanager.connect() as db:
                query = """
                    SELECT organization_id
                    FROM tokens
                    WHERE token = ?
                    LIMIT 1
                """
                async with db.execute(query, (token,)) as cursor:
                    async for row in cursor:
                        self.organization_id = row[0]
            if self.organization_id is not None:
                self.organization_code = await self.dbmanager.encode_id(
                    "organization",
                    self.organization_id,
                )
    
    def write_error(self, status_code, **kwargs):
        self.write({'error': 'Internal Error'})


class OrganizationHandler(AuthorizedRequestHandler):
    async def get(self):
        if not self.organization_id:
            self.set_status(401)
            self.write({'error': 'Not Authorized'})
            return
        
        fields = ["name", "created", "updated"]
        
        organizations = []
        async with self.dbmanager.connect() as db:
            query = f"""
                SELECT {', '.join(fields)}
                FROM organizations
                WHERE id = ?
            """
            async with db.execute(query, (self.organization_id,)) as cursor:
                async for row in cursor:
                    organizations.append(dict(zip(fields, row)))
        
        for organization in organizations:
            organization['id'] = self.organization_code
        
        self.write({
            'organization': organizations,
        })

    async def post(self):
        # Create a new organization, with a new random auth token.
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
                INSERT INTO organizations (name, created, updated)
                VALUES (?, ?, ?)
            """
            cursor = await db.execute(query, (name, now, now))
            organization_id = cursor.lastrowid
            
            token = str(uuid.uuid4())
            query = """
                INSERT INTO tokens (organization_id, token, created, updated)
                VALUES (?, ?, ?, ?)
            """
            params = (organization_id, token, now, now)
            cursor = await db.execute(query, params)
            
            await db.commit()
        
        organization_code = await self.dbmanager.encode_id(
            "organization",
            organization_id,
        )
        self.write({
            'organization': organization_code,
            'token': token,
        })
