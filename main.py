import sys
import selectors
import asyncio

# Fix para Windows — psycopg3 no es compatible con ProactorEventLoop
if sys.platform == "win32":
    selector = selectors.SelectSelector()
    loop = asyncio.SelectorEventLoop(selector)
    asyncio.set_event_loop(loop)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db.postgres import init_db, close_pool
from app.routers import chat, documents, contact
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print(f"Datheon API iniciada — entorno: {settings.environment}")
    yield
    await close_pool()
    print("Pool de DB cerrado")

app = FastAPI(
    title="Datheon API",
    description="Backend IA para la plataforma Datheón",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(chat.router,      prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(contact.router,   prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}