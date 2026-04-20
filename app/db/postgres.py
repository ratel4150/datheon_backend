import psycopg
from psycopg_pool import AsyncConnectionPool
from app.core.config import settings

_pool = None

async def get_pool():
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(
            conninfo=settings.database_url,
            min_size=2,
            max_size=10,
            open=False,
        )
        await _pool.open()
    return _pool

async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None

INIT_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    category    TEXT DEFAULT 'general',
    embedding   vector(384),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS documents_embedding_idx
ON documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lang       TEXT DEFAULT 'es',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id),
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

async def init_db():
    pool = await get_pool()
    async with pool.connection() as conn:
        await conn.execute(INIT_SQL)
    print("Base de datos inicializada")