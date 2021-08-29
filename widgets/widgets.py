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
                WHERE organization_id = ? AND deleted IS NULL
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
    
    async def put(self):
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
        changes = {}
        
        widget_id = post.get("id")
        if not widget_id:
            errors['id'] = 'id is required'
        else:
            current = None
            async with self.dbmanager.connect() as db:
                fields = ["id", "name", "parts", "description", "created"]
                query = f"""
                    SELECT {', '.join(fields)}
                    FROM widgets
                    WHERE id = ? AND organization_id = ? AND deleted IS NULL
                    LIMIT 1
                """
                params = (widget_id, self.organization_id)
                async with db.execute(query, params) as cursor:
                    async for row in cursor:
                        current = dict(zip(fields, row))
            if current is None:
                errors['id'] = 'id must be an existing widget id'
        
        if 'name' in post:
            name = post["name"]
            if current and name == current['name']:
                pass
            elif not name:
                errors['name'] = 'name is required'
            elif not isinstance(name, str):
                errors['name'] = 'name must be a string'
            elif 64 < len(name):
                errors['name'] = 'name must not be longer than 64 characters'
            else:
                changes['name'] = name
        
        if 'parts' in post:
            parts = post["parts"]
            if current and parts == current['parts']:
                pass
            elif not parts:
                errors['parts'] = 'parts is required'
            elif not isinstance(parts, int):
                errors['parts'] = 'parts must be an integer'
            elif parts < 0:
                errors['parts'] = 'parts must not be negative'
            elif (1 << 31) < parts:
                errors['parts'] = 'parts must not be excessively large'
            else:
                changes['parts'] = parts
        
        if 'description' in post:
            description = post["description"]
            if current and description == current['description']:
                pass
            elif description is not None and not isinstance(description, str):
                errors['description'] = 'description must be a string'
            else:
                changes['description'] = description
        
        if errors:
            self.set_status(400)
            self.write({'error': errors})
            return
        
        if changes:
            now = self.dbmanager.now()
            changes['updated'] = str(now)
            keys, values = zip(*changes.items())
            settings = ', '.join(f'{key} = ?' for key in keys)
            query = f"""
                UPDATE widgets SET {settings}
                WHERE id = ? AND organization_id = ?
            """
            params = values + (widget_id, self.organization_id)
            async with self.dbmanager.connect() as db:
                cursor = await db.execute(query, params)
                await db.commit()
            current.update(changes)
        
        self.write({
            'organization': self.organization_id,
            'widget': current,
        })
    
    async def delete(self):
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
        
        widget_id = post.get("id")
        if not widget_id:
            errors['id'] = 'id is required'
        else:
            # This could just go ahead with the delete and check for changes,
            # but querying first is just a little easier in many systems.
            current = None
            async with self.dbmanager.connect() as db:
                query = f"""
                    SELECT id
                    FROM widgets
                    WHERE id = ? AND organization_id = ? AND deleted IS NULL
                    LIMIT 1
                """
                params = (widget_id, self.organization_id)
                async with db.execute(query, params) as cursor:
                    async for row in cursor:
                        current = row[0]
            if current is None:
                errors['id'] = 'id must be an existing widget id'
        
        if errors:
            self.set_status(400)
            self.write({'error': errors})
            return
        
        now = self.dbmanager.now()
        query = f"""
            UPDATE widgets SET deleted = ?
            WHERE id = ? AND organization_id = ? AND deleted IS NULL
        """
        params = (now, widget_id, self.organization_id)
        async with self.dbmanager.connect() as db:
            cursor = await db.execute(query, params)
            await db.commit()
            changes = db.total_changes
        
        if not changes:
            self.set_status(409)
            self.write({'error': 'No changes made'})
            return
        
        self.write({
            'organization': self.organization_id,
            'widget': current,
        })
    
    async def patch(self):
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
        
        widget_id = post.get("id")
        if not widget_id:
            errors['id'] = 'id is required'
        else:
            # This query specifically looks for deleted widgets to restore.
            current = None
            async with self.dbmanager.connect() as db:
                query = f"""
                    SELECT id
                    FROM widgets
                    WHERE id = ? AND organization_id = ?
                    AND deleted IS NOT NULL
                    LIMIT 1
                """
                params = (widget_id, self.organization_id)
                async with db.execute(query, params) as cursor:
                    async for row in cursor:
                        current = row[0]
            if current is None:
                errors['id'] = 'id must be a deleted widget id'
        
        if errors:
            self.set_status(400)
            self.write({'error': errors})
            return
        
        now = self.dbmanager.now()
        query = f"""
            UPDATE widgets SET deleted = NULL, updated = ?
            WHERE id = ? AND organization_id = ? AND deleted IS NOT NULL
        """
        params = (now, widget_id, self.organization_id)
        async with self.dbmanager.connect() as db:
            cursor = await db.execute(query, params)
            await db.commit()
            changes = db.total_changes
        
        if not changes:
            self.set_status(409)
            self.write({'error': 'No changes made'})
            return
        
        self.write({
            'organization': self.organization_id,
            'widget': current,
        })
