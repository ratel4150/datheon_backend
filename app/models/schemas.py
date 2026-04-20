from pydantic import BaseModel, EmailStr
from typing import List, Optional

# ─── Chat ────────────────────────────────────────────────────
class Message(BaseModel):
    role: str   # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    messages: List[Message] = []
    lang: str = "es"
    session_id: Optional[str] = None

# ─── Documentos ───────────────────────────────────────────────
class DocumentIn(BaseModel):
    id: str
    title: str
    content: str
    category: str = "general"

class DocumentOut(BaseModel):
    id: str
    title: str
    category: str
    similarity: Optional[float] = None

# ─── Contacto ─────────────────────────────────────────────────
class ContactRequest(BaseModel):
    nombre: str
    email: str
    empresa: Optional[str] = None
    presupuesto: Optional[str] = None   # "<5k" | "5k-15k" | "15k-50k" | ">50k"
    tipo_proyecto: Optional[str] = None
    mensaje: Optional[str] = None
    lang: str = "es"

# ─── Leads ────────────────────────────────────────────────────
class LeadScore(BaseModel):
    email: str
    score: float          # 0.0 - 1.0
    tier: str             # "hot" | "warm" | "cold"
    recommended_action: str
