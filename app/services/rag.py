from sentence_transformers import SentenceTransformer
from app.db.postgres import get_pool

# Modelo local, no necesita API key, se descarga una vez (~90MB)
_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

async def get_embedding(text: str) -> list:
    """Genera embedding local sin API key."""
    model = get_model()
    return model.encode(text).tolist()

async def search_context(query: str, limit: int = 4, threshold: float = 0.4) -> str:
    """Busca fragmentos relevantes en pgvector y devuelve contexto."""
    embedding = await get_embedding(query)
    pool = await get_pool()

    async with pool.connection() as conn:
        cursor = await conn.execute(
            """
            SELECT title, content, category,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM documents
            WHERE 1 - (embedding <=> %s::vector) > %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (str(embedding), str(embedding), threshold, str(embedding), limit),
        )
        results = await cursor.fetchall()
        cols = [d[0] for d in cursor.description]

    if not results:
        return ""

    chunks = []
    for row in results:
        r = dict(zip(cols, row))
        chunks.append(f"[{r['category'].upper()}] {r['title']}\n{r['content']}")

    return "\n\n---\n\n".join(chunks)

async def index_document(doc_id: str, title: str, content: str, category: str = "general") -> dict:
    """Indexa un documento generando su embedding y guardándolo en pgvector."""
    embedding = await get_embedding(content)
    pool = await get_pool()

    async with pool.connection() as conn:
        await conn.execute(
            """
            INSERT INTO documents (id, title, content, category, embedding)
            VALUES (%s, %s, %s, %s, %s::vector)
            ON CONFLICT (id) DO UPDATE
            SET title = EXCLUDED.title,
                content = EXCLUDED.content,
                category = EXCLUDED.category,
                embedding = EXCLUDED.embedding
            """,
            (doc_id, title, content, category, str(embedding)),
        )

    return {"id": doc_id, "status": "indexed"}