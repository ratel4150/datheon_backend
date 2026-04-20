from fastapi import APIRouter, Header, HTTPException
from app.models.schemas import DocumentIn
from app.services.rag import index_document, search_context
from app.core.config import settings

router = APIRouter(prefix="/documents", tags=["documents"])

def verify_key(x_internal_key: str = Header(default="")):
    if x_internal_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.post("/index")
async def index(doc: DocumentIn, x_internal_key: str = Header(default="")):
    """Indexa un documento generando su embedding y guardando en pgvector."""
    verify_key(x_internal_key)
    result = await index_document(
        doc_id=doc.id,
        title=doc.title,
        content=doc.content,
        category=doc.category,
    )
    return result

@router.post("/index-batch")
async def index_batch(docs: list[DocumentIn], x_internal_key: str = Header(default="")):
    """Indexa múltiples documentos de una vez."""
    verify_key(x_internal_key)
    results = []
    for doc in docs:
        result = await index_document(
            doc_id=doc.id,
            title=doc.title,
            content=doc.content,
            category=doc.category,
        )
        results.append(result)
    return {"indexed": len(results), "results": results}

@router.get("/search")
async def search(q: str, limit: int = 4):
    """Busca documentos relevantes — útil para debug."""
    context = await search_context(q, limit=limit)
    return {"query": q, "context": context}
