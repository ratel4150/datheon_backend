import sys
import selectors
import asyncio

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

app = FastAPI(
    title="Datheon API",
    version="1.0.0",
    lifespan=lifespan,
   docs_url="/docs",  # <--- Cámbialo para que quede fijo así
    redirect_slashes=False, # <-- AGREGA ESTA LÍNEA AQUÍ
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_origins(),  # usa el método en lugar del campo directo
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
