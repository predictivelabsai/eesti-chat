import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

log = logging.getLogger(__name__)

DB_URL = os.environ.get("DB_URL", "").strip()
SCHEMA = os.environ.get("DB_SCHEMA", "eesti").strip() or "eesti"
LEGACY_SCHEMA = "carhero"

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
    _migrate_legacy_schema()


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


def _migrate_legacy_schema():
    """Copy legacy chat data out of the old schema, if present.

    The migration is deliberately best-effort.  It runs in its own transaction
    so a legacy schema mismatch can never prevent the application from starting.
    """
    if not DB_ENABLED or SCHEMA == LEGACY_SCHEMA:
        return

    try:
        with engine.begin() as conn:
            legacy_tables = set(conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = :schema
                  AND table_name IN ('chat_users', 'chat_sessions', 'chat_messages')
            """), {"schema": LEGACY_SCHEMA}).scalars().all())
            required_tables = {"chat_users", "chat_sessions", "chat_messages"}
            if not required_tables.issubset(legacy_tables):
                if legacy_tables:
                    log.warning(
                        "Legacy %s schema found without all chat tables; skipping migration",
                        LEGACY_SCHEMA,
                    )
                return

            users = conn.execute(text(f"""
                INSERT INTO {SCHEMA}.chat_users (
                    email, password_hash, name, is_verified, verify_token,
                    reset_token, reset_token_expires, role, created_at
                )
                SELECT
                    email, password_hash, name, is_verified, verify_token,
                    reset_token, reset_token_expires, role, created_at
                FROM {LEGACY_SCHEMA}.chat_users
                WHERE id <> 0 AND email IS NOT NULL
                ON CONFLICT (email) DO NOTHING
            """)).rowcount

            # A user's email is the stable key across the two schemas.  The
            # guest account is the one intentional exception: its old email
            # changed during the rebrand, but both schemas use id=0.
            conn.execute(text(f"""
                CREATE TEMP TABLE _legacy_session_map (
                    legacy_id INTEGER PRIMARY KEY,
                    current_id INTEGER NOT NULL
                ) ON COMMIT DROP
            """))

            sessions = conn.execute(text(f"""
                INSERT INTO {SCHEMA}.chat_sessions (
                    user_id, title, agent_slug, share_token, created_at, updated_at
                )
                SELECT
                    current_user.id, legacy.title, legacy.agent_slug,
                    legacy.share_token, legacy.created_at, legacy.updated_at
                FROM {LEGACY_SCHEMA}.chat_sessions AS legacy
                JOIN {LEGACY_SCHEMA}.chat_users AS legacy_user
                    ON legacy_user.id = legacy.user_id
                JOIN {SCHEMA}.chat_users AS current_user
                    ON current_user.email = legacy_user.email
                    OR (legacy_user.id = 0 AND current_user.id = 0)
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM {SCHEMA}.chat_sessions AS current_session
                    WHERE current_session.user_id = current_user.id
                      AND current_session.created_at IS NOT DISTINCT FROM legacy.created_at
                )
                ON CONFLICT DO NOTHING
            """)).rowcount

            # Build a source-id to destination-id map after the insert so
            # message foreign keys remain correct even when serial IDs differ.
            conn.execute(text(f"""
                INSERT INTO _legacy_session_map (legacy_id, current_id)
                SELECT legacy.id, current_session.id
                FROM {LEGACY_SCHEMA}.chat_sessions AS legacy
                JOIN {LEGACY_SCHEMA}.chat_users AS legacy_user
                    ON legacy_user.id = legacy.user_id
                JOIN {SCHEMA}.chat_users AS current_user
                    ON current_user.email = legacy_user.email
                    OR (legacy_user.id = 0 AND current_user.id = 0)
                JOIN {SCHEMA}.chat_sessions AS current_session
                    ON current_session.user_id = current_user.id
                   AND (
                        current_session.id = legacy.id
                        OR current_session.created_at IS NOT DISTINCT FROM legacy.created_at
                   )
                ON CONFLICT (legacy_id) DO NOTHING
            """))

            messages = conn.execute(text(f"""
                INSERT INTO {SCHEMA}.chat_messages (
                    session_id, role, content, agent_slug, tool_calls, created_at
                )
                SELECT
                    session_map.current_id, legacy.role, legacy.content,
                    legacy.agent_slug, legacy.tool_calls, legacy.created_at
                FROM {LEGACY_SCHEMA}.chat_messages AS legacy
                JOIN _legacy_session_map AS session_map
                    ON session_map.legacy_id = legacy.session_id
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM {SCHEMA}.chat_messages AS current_message
                    WHERE current_message.session_id = session_map.current_id
                      AND current_message.role IS NOT DISTINCT FROM legacy.role
                      AND current_message.content IS NOT DISTINCT FROM legacy.content
                      AND current_message.created_at IS NOT DISTINCT FROM legacy.created_at
                )
                ON CONFLICT DO NOTHING
            """)).rowcount

            for table in ("chat_users", "chat_sessions", "chat_messages"):
                conn.execute(text(f"""
                    SELECT setval(
                        pg_get_serial_sequence(:qualified_table, 'id'),
                        GREATEST(
                            COALESCE((SELECT MAX(id) FROM {SCHEMA}.{table}), 1),
                            COALESCE((
                                SELECT last_value
                                FROM pg_sequences
                                WHERE schemaname = :schema
                                  AND sequencename = :sequence_name
                            ), 1)
                        ),
                        TRUE
                    )
                """), {
                    "qualified_table": f"{SCHEMA}.{table}",
                    "schema": SCHEMA,
                    "sequence_name": f"{table}_id_seq",
                })

            log.info(
                "Migrated legacy %s chat data into %s: users=%s, sessions=%s, messages=%s",
                LEGACY_SCHEMA,
                SCHEMA,
                users,
                sessions,
                messages,
            )
    except Exception:
        log.exception(
            "Legacy %s chat-data migration failed; continuing startup",
            LEGACY_SCHEMA,
        )


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
