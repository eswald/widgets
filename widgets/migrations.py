migrations = []

def migration(f):
    migrations.append(f)
    return f

@migration
async def create_accounts_table(db):
    await db.execute(r"""
        CREATE TABLE accounts (
            id INTEGER NOT NULL PRIMARY KEY,
            name TEXT NOT NULL,
            created TEXT NOT NULL,
            updated TEXT NOT NULL
        )
    """)

@migration
async def create_tokens_table(db):
    await db.execute(r"""
        CREATE TABLE tokens (
            id INTEGER NOT NULL PRIMARY KEY,
            account_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            created TEXT NOT NULL,
            updated TEXT NOT NULL
        )
    """)

@migration
async def create_widgets_table(db):
    await db.execute(r"""
        CREATE TABLE widgets (
            id INTEGER NOT NULL PRIMARY KEY,
            account_id INTEGER NOT NULL,
            name VARCHAR(64) NOT NULL,
            parts INTEGER NOT NULL,
            created TEXT NOT NULL,
            updated TEXT NOT NULL,
            description TEXT
        )
    """)

@migration
async def soft_delete_widgets(db):
    await db.execute(r"""
        ALTER TABLE widgets ADD COLUMN deleted TEXT DEFAULT NULL
    """)

@migration
async def create_alphabets_table(db):
    await db.execute(r"""
        CREATE TABLE alphabets (
            id INTEGER NOT NULL PRIMARY KEY,
            prefix TEXT UNIQUE NOT NULL,
            alphabet TEXT NOT NULL
        )
    """)

async def run_migrations(dbmanager):
    async with dbmanager.connect() as db:
        await db.execute(r"""
            CREATE TABLE IF NOT EXISTS migrations (
                name TEXT PRIMARY KEY,
                migrated TEXT NOT NULL
            )
        """)
        
        async with db.execute("SELECT name FROM migrations") as cursor:
            migrated = set(row[0] for row in await cursor.fetchall())
        print(f"Checking migrations: {len(migrated)} / {len(migrations)} ...")
        
        updated = []
        for migration in migrations:
            name = migration.__name__
            if name not in migrated:
                print(f"Running migration {name}...")
                updated.append(name)
                await migration(db)
                await db.execute(r"""
                    INSERT INTO migrations (name, migrated) VALUES (?, ?)
                """, (name, str(dbmanager.now())))
                await db.commit()
        
        print("Migrations complete.")
        return updated
