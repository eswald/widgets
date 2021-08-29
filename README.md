Widget Factory
==============

The REST API you never needed, to keep track of widgets you never wanted.

It's designed to run from a directory on a Linux machine, but just might work
on other types of systems.  To use it, first set up a Python virtual
environment for it:

    $ git clone https://github.com/eswald/widgets.git
    Cloning into 'widgets'...
    remote: Enumerating objects: 68, done.
    remote: Counting objects: 100% (68/68), done.
    remote: Compressing objects: 100% (27/27), done.
    remote: Total 68 (delta 39), reused 67 (delta 38), pack-reused 0
    Unpacking objects: 100% (68/68), done.
    $ cd widgets
    $ python3 -m venv .env
    $ . .env/bin/activate
    $ pip install -U pip
    Collecting pip
      ...
    Successfully installed pip-21.2.4
    $ pip install -r requirements.txt -c package-constraints.txt
    Collecting aiosqlite
      ...
    Installing collected packages: zipp, typing-extensions, importlib-metadata, tornado, click, aiosqlite
    Successfully installed aiosqlite-0.17.0 click-8.0.1 importlib-metadata-4.7.1 tornado-6.1 typing-extensions-3.10.0.0 zipp-3.5.0

Your output will vary, of course.  With that in place, run the Tornado web
server:

    $ python application.py
    Listening...
    Checking migrations: 0 / 5 ...
    Running migration create_accounts_table...
    Running migration create_tokens_table...
    Running migration create_widgets_table...
    Running migration soft_delete_widgets...
    Running migration create_alphabets_table...
    Migrations complete.

Those migration lines mean that it has set up a brand-new SQLite3 database
with empty tables.  By default, that will use a file named `database.sqlite`
in the current directory, but you can change it with the `--database`
command-line option.

By default, the server listens on port 8888.  If you already have something
running on that port, you can use the `--port` option to select a new one.

The server will run until it gets interrupted, such as with Ctrl-C. While it's
running, you can make HTTP requests to it.  There are many ways to do so, but
the following commands will use [HTTPie](https://httpie.io/) in a separate
command terminal:

    $ pip install httpie
    Collecting httpie
      ...
    Installing collected packages: urllib3, idna, charset-normalizer, certifi, requests, PySocks, requests-toolbelt, Pygments, httpie
    Successfully installed PySocks-1.7.1 Pygments-2.10.0 certifi-2021.5.30 charset-normalizer-2.0.4 httpie-2.4.0 idna-3.2 requests-2.26.0 requests-toolbelt-0.9.1 urllib3-1.26.6
    $ http localhost:8888/
    HTTP/1.1 401 Unauthorized
    Content-Length: 27
    Content-Type: application/json; charset=UTF-8
    Date: Sun, 29 Aug 2021 14:12:17 GMT
    Server: TornadoServer/6.1

    {
        "error": "Not Authorized"
    }

Right.  You wouldn't want just anyone meddling with your widgets, so this
application requires an authorization token.  Create one by asking it to
create a new account for you:

    $ http POST localhost:8888/ "name=<Your account name here>"
    HTTP/1.1 200 OK
    Content-Length: 79
    Content-Type: application/json; charset=UTF-8
    Date: Sun, 29 Aug 2021 14:12:59 GMT
    Server: TornadoServer/6.1

    {
        "account": "account-bjzwrdg",
        "token": "05367170-a27b-4559-ac97-5fa6e817ec75"
    }

In case you're using another way to test the API, that `name=` parameter tells
HTTPie to send a JSON request with `{"name": "<Your account name here>"}` in
the body.

Now that you have an authorization token, you can use it to make requests.
For example, getting your account information:

    $ http localhost:8888/ "Authorization:Bearer 05367170-a27b-4559-ac97-5fa6e817ec75"
    HTTP/1.1 200 OK
    Content-Length: 170
    Content-Type: application/json; charset=UTF-8
    Date: Sun, 29 Aug 2021 14:18:55 GMT
    Etag: "c0e047b4e5cee75b353e2a02b2d7b80d2524e85b"
    Server: TornadoServer/6.1

    {
        "account": [
            {
                "created": "2021-08-29 14:12:59.726177+00:00",
                "id": "account-bjzwrdg",
                "name": "<Your account name here>",
                "updated": "2021-08-29 14:12:59.726177+00:00"
            }
        ]
    }

Or the widgets in your account:

    $ http localhost:8888/widgets/ "Authorization:Bearer 05367170-a27b-4559-ac97-5fa6e817ec75"
    HTTP/1.1 200 OK
    Content-Length: 45
    Content-Type: application/json; charset=UTF-8
    Date: Sun, 29 Aug 2021 14:19:37 GMT
    Etag: "70e814764369cc4b5750dcf92932778a16577a55"
    Server: TornadoServer/6.1

    {
        "account": "account-bjzwrdg",
        "widgets": []
    }

But, of course, there aren't any.  Yet.  Use POST requests to make them:

    $ http POST localhost:8888/widgets/ "Authorization:Bearer 05367170-a27b-4559-ac97-5fa6e817ec75" "name=Frame" "parts:=1"
    HTTP/1.1 200 OK
    Content-Length: 210
    Content-Type: application/json; charset=UTF-8
    Date: Sun, 29 Aug 2021 14:20:40 GMT
    Server: TornadoServer/6.1

    {
        "account": "account-bjzwrdg",
        "widget": {
            "created": "2021-08-29 14:20:40.848936+00:00",
            "description": null,
            "id": "widget-tdvswpg",
            "name": "Frame",
            "parts": 1,
            "updated": "2021-08-29 14:20:40.848936+00:00"
        }
    }

That `:=` in the `parts` field tells `http` to send that field as an integer,
instead of a string.  Essentially, it sends `{"name": "Frame", "parts": 1}` to
the server, barring variations in field order and whitespace.  Widget creation
also accepts an optional description field:

    $ http POST localhost:8888/widgets/ "Authorization:Bearer 05367170-a27b-4559-ac97-5fa6e817ec75" "name=Front Brake System" "parts:=10" "description=Lever, cables, brake pads, and mountings"
    HTTP/1.1 200 OK
    Content-Length: 262
    Content-Type: application/json; charset=UTF-8
    Date: Sun, 29 Aug 2021 14:26:13 GMT
    Server: TornadoServer/6.1

    {
        "account": "account-bjzwrdg",
        "widget": {
            "created": "2021-08-29 14:26:13.654168+00:00",
            "description": "Lever, cables, brake pads, and mountings",
            "id": "widget-rmzvqjw",
            "name": "Front Brake System",
            "parts": 10,
            "updated": "2021-08-29 14:26:13.654168+00:00"
        }
    }
    $ http POST localhost:8888/widgets/ "Authorization:Bearer 05367170-a27b-4559-ac97-5fa6e817ec75" "name=Handlebar Assembly" "parts:=14" "description=Including the mount point for the frame."
    HTTP/1.1 200 OK
    Content-Length: 262
    Content-Type: application/json; charset=UTF-8
    Date: Sun, 29 Aug 2021 14:26:41 GMT
    Server: TornadoServer/6.1

    {
        "account": "account-bjzwrdg",
        "widget": {
            "created": "2021-08-29 14:26:41.721508+00:00",
            "description": "Including the mount point for the frame.",
            "id": "widget-ppgtxnz",
            "name": "Handlebar Assembly",
            "parts": 14,
            "updated": "2021-08-29 14:26:41.721508+00:00"
        }
    }

Listing the widgets will now give us a bit more data:

    $ http localhost:8888/widgets/ "Authorization:Bearer 05367170-a27b-4559-ac97-5fa6e817ec75"
    HTTP/1.1 200 OK
    Content-Length: 657
    Content-Type: application/json; charset=UTF-8
    Date: Sun, 29 Aug 2021 14:28:43 GMT
    Etag: "bdd6baad435f84701169524d3d87cb76817509c2"
    Server: TornadoServer/6.1

    {
        "account": "account-bjzwrdg",
        "widgets": [
            {
                "created": "2021-08-29 14:20:40.848936+00:00",
                "description": null,
                "id": "widget-tdvswpg",
                "name": "Frame",
                "parts": 1,
                "updated": "2021-08-29 14:20:40.848936+00:00"
            },
            {
                "created": "2021-08-29 14:26:13.654168+00:00",
                "description": "Lever, cables, brake pads, and mountings",
                "id": "widget-rmzvqjw",
                "name": "Front Brake System",
                "parts": 10,
                "updated": "2021-08-29 14:26:13.654168+00:00"
            },
            {
                "created": "2021-08-29 14:26:41.721508+00:00",
                "description": "Including the mount point for the frame.",
                "id": "widget-ppgtxnz",
                "name": "Handlebar Assembly",
                "parts": 14,
                "updated": "2021-08-29 14:26:41.721508+00:00"
            }
        ]
    }

Come to think of it, that part count for the brake system seems a little low.
Lets add all the nuts, bolts, washers, and springs to it, with the `PUT` API:

    $ http PUT localhost:8888/widgets/ "Authorization:Bearer 05367170-a27b-4559-ac97-5fa6e817ec75" id=widget-rmzvqjw parts:=24
    HTTP/1.1 200 OK
    Content-Length: 262
    Content-Type: application/json; charset=UTF-8
    Date: Sun, 29 Aug 2021 14:34:47 GMT
    Server: TornadoServer/6.1

    {
        "account": "account-bjzwrdg",
        "widget": {
            "created": "2021-08-29 14:26:13.654168+00:00",
            "description": "Lever, cables, brake pads, and mountings",
            "id": "widget-rmzvqjw",
            "name": "Front Brake System",
            "parts": 24,
            "updated": "2021-08-29 14:34:47.067746+00:00"
        }
    }

Or perhaps we want a trike instead, which doesn't need a handlebar assembly.
So let's go ahead and delete that:

    $ http DELETE localhost:8888/widgets/ "Authorization:Bearer 05367170-a27b-4559-ac97-5fa6e817ec75" id=widget-rmzvqjw
    HTTP/1.1 200 OK
    Content-Length: 309
    Content-Type: application/json; charset=UTF-8
    Date: Sun, 29 Aug 2021 14:38:01 GMT
    Server: TornadoServer/6.1

    {
        "account": "account-bjzwrdg",
        "widget": {
            "created": "2021-08-29 14:26:13.654168+00:00",
            "deleted": "2021-08-29 14:38:01.306165+00:00",
            "description": "Lever, cables, brake pads, and mountings",
            "id": "widget-rmzvqjw",
            "name": "Front Brake System",
            "parts": 24,
            "updated": "2021-08-29 14:34:47.067746+00:00"
        }
    }

And we see that it's no longer in the list:

    $ http localhost:8888/widgets/ "Authorization:Bearer 05367170-a27b-4559-ac97-5fa6e817ec75"
    HTTP/1.1 200 OK
    Content-Length: 435
    Content-Type: application/json; charset=UTF-8
    Date: Sun, 29 Aug 2021 14:38:27 GMT
    Etag: "07ec7a8f0b74dc98c2620998c822a61d03a22077"
    Server: TornadoServer/6.1

    {
        "account": "account-bjzwrdg",
        "widgets": [
            {
                "created": "2021-08-29 14:20:40.848936+00:00",
                "description": null,
                "id": "widget-tdvswpg",
                "name": "Frame",
                "parts": 1,
                "updated": "2021-08-29 14:20:40.848936+00:00"
            },
            {
                "created": "2021-08-29 14:26:41.721508+00:00",
                "description": "Including the mount point for the frame.",
                "id": "widget-ppgtxnz",
                "name": "Handlebar Assembly",
                "parts": 14,
                "updated": "2021-08-29 14:26:41.721508+00:00"
            }
        ]
    }

Wait, that wasn't the handlebar assembly; that was the brakes!  Quick, undo
before you forget the id, and delete the right record:

    $ http PATCH localhost:8888/widgets/ "Authorization:Bearer 05367170-a27b-4559-ac97-5fa6e817ec75" id=widget-rmzvqjw
    HTTP/1.1 200 OK
    Content-Length: 279
    Content-Type: application/json; charset=UTF-8
    Date: Sun, 29 Aug 2021 14:38:55 GMT
    Server: TornadoServer/6.1

    {
        "account": "account-bjzwrdg",
        "widget": {
            "created": "2021-08-29 14:26:13.654168+00:00",
            "deleted": null,
            "description": "Lever, cables, brake pads, and mountings",
            "id": "widget-rmzvqjw",
            "name": "Front Brake System",
            "parts": 24,
            "updated": "2021-08-29 14:38:55.346884+00:00"
        }
    }
    $ http DELETE localhost:8888/widgets/ "Authorization:Bearer 05367170-a27b-4559-ac97-5fa6e817ec75" id=widget-ppgtxnz
    HTTP/1.1 200 OK
    Content-Length: 309
    Content-Type: application/json; charset=UTF-8
    Date: Sun, 29 Aug 2021 14:39:17 GMT
    Server: TornadoServer/6.1

    {
        "account": "account-bjzwrdg",
        "widget": {
            "created": "2021-08-29 14:26:41.721508+00:00",
            "deleted": "2021-08-29 14:39:17.845582+00:00",
            "description": "Including the mount point for the frame.",
            "id": "widget-ppgtxnz",
            "name": "Handlebar Assembly",
            "parts": 14,
            "updated": "2021-08-29 14:26:41.721508+00:00"
        }
    }

So how, you might ask, did we manage to restore a deleted record?  By
cheating, in a way; it was never really deleted, just marked as hidden from
the API methods.  This can be helpful when going over old logs, or tracking
down bugs, particularly since SQLite has a habit of re-using deleted id
numbers in certain situations.

Speaking of hiding, we can verify that other accounts don't see our widgets by
creating a new account and using its auth token:

    $ http POST localhost:8888/ name=Spyware
    HTTP/1.1 200 OK
    Content-Length: 79
    Content-Type: application/json; charset=UTF-8
    Date: Sun, 29 Aug 2021 14:41:58 GMT
    Server: TornadoServer/6.1

    {
        "account": "account-nvfzmpr",
        "token": "b439369c-31a7-4a32-bb87-5074601dfdec"
    }
    $ http GET localhost:8888/widgets/ "Authorization:Bearer b439369c-31a7-4a32-bb87-5074601dfdec"
    HTTP/1.1 200 OK
    Content-Length: 45
    Content-Type: application/json; charset=UTF-8
    Date: Sun, 29 Aug 2021 14:43:11 GMT
    Etag: "88534c499ede97d713ba9cc8d21d036ca4c3bcf2"
    Server: TornadoServer/6.1

    {
        "account": "account-nvfzmpr",
        "widgets": []
    }

But using the original auth token will still bring up the widgets we've
created:

    $ http localhost:8888/widgets/ "Authorization:Bearer 05367170-a27b-4559-ac97-5fa6e817ec75"
    HTTP/1.1 200 OK
    Content-Length: 435
    Content-Type: application/json; charset=UTF-8
    Date: Sun, 29 Aug 2021 14:44:33 GMT
    Etag: "b3e92615d2fa1b3aa77638d8e5a9300e1de67e09"
    Server: TornadoServer/6.1

    {
        "account": "account-bjzwrdg",
        "widgets": [
            {
                "created": "2021-08-29 14:20:40.848936+00:00",
                "description": null,
                "id": "widget-tdvswpg",
                "name": "Frame",
                "parts": 1,
                "updated": "2021-08-29 14:20:40.848936+00:00"
            },
            {
                "created": "2021-08-29 14:26:13.654168+00:00",
                "description": "Lever, cables, brake pads, and mountings",
                "id": "widget-rmzvqjw",
                "name": "Front Brake System",
                "parts": 24,
                "updated": "2021-08-29 14:38:55.346884+00:00"
            }
        ]
    }
