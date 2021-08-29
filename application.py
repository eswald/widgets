import click
import tornado.ioloop
import tornado.web

import widgets.auth
import widgets.database
import widgets.migrations
import widgets.widgets


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
    params = {'dbmanager': dbmanager}
    app = tornado.web.Application([
        (r"/", widgets.auth.AccountHandler, params),
        (r"/widgets/", widgets.widgets.WidgetHandler, params),
    ])
    app.listen(8888)
    print("Listening...")
    loop.start()


if __name__ == "__main__":
    run()
