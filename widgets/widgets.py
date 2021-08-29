import json

import widgets.auth


class WidgetHandler(widgets.auth.AuthorizedRequestHandler):
    async def get(self):
        if not self.organization_id:
            self.set_status(401)
            self.write({'error': 'Not Authorized'})
            return
        
        fields = ["id", "name", "parts", "created", "updated", "description"]
        
        widgets = []
        async with self.dbmanager.connect() as db:
            query = f"""
                SELECT {', '.join(fields)}
                FROM widgets
                WHERE organization_id = ?
            """
            async with db.execute(query, (self.organization_id,)) as cursor:
                async for row in cursor:
                    widgets.append(dict(zip(fields, row)))
        
        self.write({
            'organization': self.organization_id,
            'widgets': widgets,
        })
    
    async def post(self):
        if not self.organization_id:
            self.set_status(401)
            self.write({'error': 'Not Authorized'})
            return
        
        try:
            post = json.loads(self.request.body)
            assert isinstance(post, dict)
        except Exception:
            self.set_status(400)
            self.write({'error': 'Invalid json request'})
            return
        
        errors = {}
        
        name = post.get("name")
        if not name:
            errors['name'] = 'name is required'
        elif not isinstance(name, str):
            errors['name'] = 'name must be a string'
        elif 64 < len(name):
            errors['name'] = 'name must not be longer than 64 characters'
        
        parts = post.get("parts")
        if not parts:
            errors['parts'] = 'parts is required'
        elif not isinstance(parts, int):
            errors['parts'] = 'parts must be an integer'
        elif parts < 0:
            errors['parts'] = 'parts must not be negative'
        elif (1 << 31) < parts:
            errors['parts'] = 'parts must not be excessively large'
        
        description = post.get("description")
        if description is not None and not isinstance(description, str):
            errors['description'] = 'description must be a string'
        
        if errors:
            self.set_status(400)
            self.write({'error': errors})
            return
        
        now = self.dbmanager.now()
        fields = {
            "name": name,
            "parts": parts,
            "description": description,
            "created": str(now),
            "updated": str(now),
        }
        
        widget_id = await self.dbmanager.insert_row("widgets",
            organization_id=self.organization_id, **fields)
        fields["id"] = widget_id
        
        self.write({
            'organization': self.organization_id,
            'widget': fields,
        })
