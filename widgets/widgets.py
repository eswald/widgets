import json

import widgets.auth


class WidgetHandler(widgets.auth.AuthorizedRequestHandler):
    async def get(self):
        if not self.account_id:
            self.set_status(401)
            self.write({'error': 'Not Authorized'})
            return

        fields = ["id", "name", "parts", "created", "updated", "description"]

        widgets = []
        async with self.dbmanager.connect() as db:
            query = f"""
                SELECT {', '.join(fields)}
                FROM widgets
                WHERE account_id = ? AND deleted IS NULL
            """
            async with db.execute(query, (self.account_id,)) as cursor:
                async for row in cursor:
                    widgets.append(dict(zip(fields, row)))

        encoder = self.dbmanager.encode_id
        for widget in widgets:
            widget["id"] = await encoder("widget", widget["id"])

        self.write({
            'account': self.account_code,
            'widgets': widgets,
        })

    async def post(self):
        if not self.account_id:
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
                                                    account_id=self.account_id,
                                                    **fields)

        fields["id"] = await self.dbmanager.encode_id("widget", widget_id)

        self.write({
            'account': self.account_code,
            'widget': fields,
        })

    async def put(self):
        if not self.account_id:
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

        widget_code = post.get("id")
        if not widget_code:
            errors['id'] = 'id is required'
        else:
            prefix, widget_id = await self.dbmanager.decode_id(widget_code)
            current = None
            async with self.dbmanager.connect() as db:
                fields = ["name", "parts", "description", "created"]
                query = f"""
                    SELECT {', '.join(fields)}
                    FROM widgets
                    WHERE id = ? AND account_id = ? AND deleted IS NULL
                    LIMIT 1
                """
                params = (widget_id, self.account_id)
                async with db.execute(query, params) as cursor:
                    async for row in cursor:
                        current = dict(zip(fields, row))
            if current is None or prefix != "widget":
                errors['id'] = 'id must be an existing widget id'
            else:
                current['id'] = widget_code

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
                WHERE id = ? AND account_id = ?
            """
            params = values + (widget_id, self.account_id)
            async with self.dbmanager.connect() as db:
                cursor = await db.execute(query, params)
                await db.commit()
            current.update(changes)

        self.write({
            'account': self.account_code,
            'widget': current,
        })

    async def delete(self):
        if not self.account_id:
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

        widget_code = post.get("id")
        if not widget_code:
            errors['id'] = 'id is required'
        else:
            # This could just go ahead with the delete and check for changes,
            # but querying first is just a little easier in many systems.
            prefix, widget_id = await self.dbmanager.decode_id(widget_code)
            current = None
            async with self.dbmanager.connect() as db:
                fields = ["name", "parts", "description", "created", "updated"]
                query = f"""
                    SELECT {', '.join(fields)}
                    FROM widgets
                    WHERE id = ? AND account_id = ? AND deleted IS NULL
                    LIMIT 1
                """
                params = (widget_id, self.account_id)
                async with db.execute(query, params) as cursor:
                    async for row in cursor:
                        current = dict(zip(fields, row))
            if current is None or prefix != "widget":
                errors['id'] = 'id must be an existing widget id'
            else:
                current['id'] = widget_code

        if errors:
            self.set_status(400)
            self.write({'error': errors})
            return

        now = self.dbmanager.now()
        query = """
            UPDATE widgets SET deleted = ?
            WHERE id = ? AND account_id = ? AND deleted IS NULL
        """
        params = (now, widget_id, self.account_id)
        async with self.dbmanager.connect() as db:
            cursor = await db.execute(query, params)
            await db.commit()
            changes = db.total_changes
        current['deleted'] = str(now)

        if not changes:
            self.set_status(409)
            self.write({'error': 'No changes made'})
            return

        self.write({
            'account': self.account_code,
            'widget': current,
        })

    async def patch(self):
        if not self.account_id:
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

        widget_code = post.get("id")
        if not widget_code:
            errors['id'] = 'id is required'
        else:
            # This could just go ahead with the delete and check for changes,
            # but querying first is just a little easier in many systems.
            prefix, widget_id = await self.dbmanager.decode_id(widget_code)
            current = None
            async with self.dbmanager.connect() as db:
                fields = ["name", "parts", "description", "created"]
                query = f"""
                    SELECT {', '.join(fields)}
                    FROM widgets
                    WHERE id = ? AND account_id = ?
                    AND deleted IS NOT NULL
                    LIMIT 1
                """
                params = (widget_id, self.account_id)
                async with db.execute(query, params) as cursor:
                    async for row in cursor:
                        current = dict(zip(fields, row))
            if current is None or prefix != "widget":
                errors['id'] = 'id must be a deleted widget id'
            else:
                current['id'] = widget_code

        if errors:
            self.set_status(400)
            self.write({'error': errors})
            return

        now = self.dbmanager.now()
        query = """
            UPDATE widgets SET deleted = NULL, updated = ?
            WHERE id = ? AND account_id = ? AND deleted IS NOT NULL
        """
        params = (now, widget_id, self.account_id)
        async with self.dbmanager.connect() as db:
            cursor = await db.execute(query, params)
            await db.commit()
            changes = db.total_changes
        current['deleted'] = None
        current['updated'] = str(now)

        if not changes:
            self.set_status(409)
            self.write({'error': 'No changes made'})
            return

        self.write({
            'account': self.account_code,
            'widget': current,
        })
