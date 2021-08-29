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
