import click
import tornado.ioloop
import tornado.web

import widgets.database
import widgets.migrations

class MainHandler(tornado.web.RequestHandler):
    def initialize(self, dbmanager):
        self.dbmanager = dbmanager
    
    async def get(self):
        self.write({
            'migrations': [f.__name__ for f in widgets.migrations.migrations],
        })


@click.command()
@click.option('--port', default=8888, type=int)
@click.option('--database',
              default="database.sqlite",
              type=click.Path(dir_okay=False,
                              resolve_path=True,
                              writable=True))
def run(port: int, database: str):
    loop = tornado.ioloop.IOLoop.current()
    dbmanager = widgets.database.ConnectionManager(database, loop)
    loop.add_callback(widgets.migrations.run_migrations, dbmanager)
    app = tornado.web.Application([
        (r"/", MainHandler, {'dbmanager': dbmanager}),
    ])
    app.listen(8888)
    print("Listening...")
    loop.start()


if __name__ == "__main__":
    run()
