import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

DB_URL = os.environ.get("DB_URL", "").strip()
SCHEMA = "eesti"

# The portal runs without a database (anonymous chat, no persisted history).
# A DB is only needed for saved chat history, login, and admin.
DB_ENABLED = bool(DB_URL)

if DB_ENABLED:
    engine = create_engine(DB_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)

    @event.listens_for(engine, "connect")
    def set_search_path(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute(f"SET search_path TO {SCHEMA}, public")
        cursor.close()

    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
else:
    engine = None

    def SessionLocal(*args, **kwargs):  # type: ignore[misc]
        raise RuntimeError(
            "No DB_URL configured — database features (login, saved history) are disabled."
        )


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create schema and all tables (no-op when no DB is configured)."""
    if not DB_ENABLED:
        print("INFO:     No DB_URL configured — running without a database "
              "(anonymous chat only, no saved history/login).")
        return
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    _init_chat_tables()


def _init_chat_tables():
    """Create chat, profile, and invitation tables if they don't exist."""
    ddl = [
        f"""CREATE TABLE IF NOT EXISTS {SCHEMA}.chat_users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255),
            name VARCHAR(200),
            is_verified BOOLEAN DEFAULT FALSE,
            verify_token VARCHAR(64),
            reset_token VARCHAR(64),
            reset_token_expires TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )""",
        f"""CREATE TABLE IF NOT EXISTS {SCHEMA}.chat_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES {SCHEMA}.chat_users(id),
            title VARCHAR(255) DEFAULT 'New chat',
            agent_slug VARCHAR(100),
            share_token VARCHAR(64),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )""",
        f"""CREATE TABLE IF NOT EXISTS {SCHEMA}.chat_messages (
            id SERIAL PRIMARY KEY,
            session_id INTEGER REFERENCES {SCHEMA}.chat_sessions(id),
            role VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            agent_slug VARCHAR(100),
            tool_calls JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )""",
        f"""CREATE TABLE IF NOT EXISTS {SCHEMA}.user_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES {SCHEMA}.chat_users(id) ON DELETE CASCADE UNIQUE,
            avatar_url VARCHAR(500),
            phone VARCHAR(30),
            country VARCHAR(5),
            city VARCHAR(100),
            currency VARCHAR(3) DEFAULT 'EUR',
            language VARCHAR(5) DEFAULT 'en',
            notify_new_listings BOOLEAN DEFAULT TRUE,
            notify_weekly_digest BOOLEAN DEFAULT TRUE,
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )""",
    ]
    alters = [
        f"ALTER TABLE {SCHEMA}.chat_users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)",
        f"ALTER TABLE {SCHEMA}.chat_users ADD COLUMN IF NOT EXISTS name VARCHAR(200)",
        f"ALTER TABLE {SCHEMA}.chat_users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE",
        f"ALTER TABLE {SCHEMA}.chat_users ADD COLUMN IF NOT EXISTS verify_token VARCHAR(64)",
        f"ALTER TABLE {SCHEMA}.chat_users ADD COLUMN IF NOT EXISTS reset_token VARCHAR(64)",
        f"ALTER TABLE {SCHEMA}.chat_users ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMPTZ",
        f"ALTER TABLE {SCHEMA}.chat_users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user'",
    ]
    invitations_ddl = f"""CREATE TABLE IF NOT EXISTS {SCHEMA}.invitations (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        token VARCHAR(64) UNIQUE NOT NULL,
        invited_by INTEGER REFERENCES {SCHEMA}.chat_users(id),
        role VARCHAR(20) DEFAULT 'user',
        message TEXT,
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        expires_at TIMESTAMPTZ,
        accepted_at TIMESTAMPTZ
    )"""
    with engine.connect() as conn:
        for stmt in ddl:
            conn.execute(text(stmt))
        conn.execute(text(invitations_ddl))
        for stmt in alters:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass
        # Ensure guest user (id=0) exists for unauthenticated API access.
        exists = conn.execute(text(f"SELECT 1 FROM {SCHEMA}.chat_users WHERE id = 0")).fetchone()
        if not exists:
            conn.execute(text(
                f"INSERT INTO {SCHEMA}.chat_users (id, email, name, password_hash) "
                f"VALUES (0, 'guest@eesti.chat', 'Guest', 'nologin')"
            ))
        # Seed admin user
        _seed_admin(conn)
        conn.commit()


def _seed_admin(conn):
    """Create the default admin user if it doesn't exist."""
    import bcrypt
    admin_email = "carehero.admin@predictivelabs.co.uk"
    admin_pw = "Autod2$2"
    exists = conn.execute(
        text(f"SELECT 1 FROM {SCHEMA}.chat_users WHERE email = :email"),
        {"email": admin_email},
    ).fetchone()
    if not exists:
        pw_hash = bcrypt.hashpw(admin_pw.encode(), bcrypt.gensalt()).decode()
        conn.execute(text(f"""
            INSERT INTO {SCHEMA}.chat_users (email, password_hash, name, is_verified, role)
            VALUES (:email, :pw, :name, TRUE, 'admin')
        """), {"email": admin_email, "pw": pw_hash, "name": "eesti.chat Admin"})
    else:
        conn.execute(
            text(f"UPDATE {SCHEMA}.chat_users SET role = 'admin' WHERE email = :email"),
            {"email": admin_email},
        )
