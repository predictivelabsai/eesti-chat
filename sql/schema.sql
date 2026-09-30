-- eesti.chat database schema
-- Target: PostgreSQL 14+

CREATE SCHEMA IF NOT EXISTS eesti;

CREATE TABLE IF NOT EXISTS eesti.chat_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    name VARCHAR(200),
    is_verified BOOLEAN DEFAULT FALSE,
    verify_token VARCHAR(64),
    reset_token VARCHAR(64),
    reset_token_expires TIMESTAMPTZ,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS eesti.chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES eesti.chat_users(id),
    title VARCHAR(255) DEFAULT 'New chat',
    agent_slug VARCHAR(100),
    share_token VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS eesti.chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES eesti.chat_sessions(id),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    agent_slug VARCHAR(100),
    tool_calls JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS eesti.user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES eesti.chat_users(id) ON DELETE CASCADE UNIQUE,
    avatar_url VARCHAR(500),
    phone VARCHAR(30),
    country VARCHAR(5),
    city VARCHAR(100),
    currency VARCHAR(3) DEFAULT 'EUR',
    language VARCHAR(5) DEFAULT 'en',
    notify_new_listings BOOLEAN DEFAULT TRUE,
    notify_weekly_digest BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS eesti.invitations (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    token VARCHAR(64) UNIQUE NOT NULL,
    invited_by INTEGER REFERENCES eesti.chat_users(id),
    role VARCHAR(20) DEFAULT 'user',
    message TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    accepted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON eesti.chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON eesti.chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_user ON eesti.user_profiles(user_id);
