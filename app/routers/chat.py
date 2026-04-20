from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from groq import AsyncGroq
from app.services.rag import search_context
from app.core.config import settings
from pydantic import BaseModel
from typing import List, Optional
import json

router = APIRouter(prefix="/chat", tags=["chat"])
groq = AsyncGroq(api_key=settings.groq_api_key)

# Schema compatible con Vercel AI SDK useChat
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    lang: Optional[str] = "es"

SYSTEM_PROMPTS = {
    "es": """Eres el asistente virtual de Datheón, consultora tecnológica especializada en:
- AI SaaS y agentes autónomos (LangGraph, RAG, Groq)
- Desarrollo web y móvil (Next.js, Flutter, FastAPI)
- IoT: conectar hardware al software (MQTT, ESP32, dashboards)
- Cloud y DevOps (AWS, Kubernetes, Terraform)
- Odoo ERP personalizado

Reglas:
1. Responde siempre en español si el usuario escribe en español
2. Sé conciso, máximo 3-4 oraciones por respuesta
3. Si preguntan por precios di que depende del proyecto y sugiere agendar: calendly.com/d/cv8d-jjp-nhd
4. Si no sabes algo específico, di que el equipo puede ayudar
5. Nunca inventes datos

Contexto de Datheón:
{context}""",

    "en": """You are the virtual assistant of Datheón, a tech consultancy specialized in:
- AI SaaS and autonomous agents (LangGraph, RAG, Groq)
- Web and mobile development (Next.js, Flutter, FastAPI)
- IoT: connecting hardware to software (MQTT, ESP32, dashboards)
- Cloud and DevOps (AWS, Kubernetes, Terraform)
- Custom Odoo ERP

Rules:
1. Always respond in English
2. Be concise, max 3-4 sentences
3. For pricing suggest booking: calendly.com/d/cv8d-jjp-nhd
4. Never invent data

Datheón context:
{context}""",

    "fr": """Vous êtes l'assistant de Datheón, société de conseil technologique.

Règles:
1. Répondez toujours en français
2. Soyez concis, max 3-4 phrases
3. Pour les prix: calendly.com/d/cv8d-jjp-nhd

Contexte:
{context}""",
}

@router.post("")
async def chat(req: ChatRequest):
    # Tomar el último mensaje del usuario para buscar contexto
    last_user_msg = next(
        (m.content for m in reversed(req.messages) if m.role == "user"),
        ""
    )

    context = await search_context(last_user_msg)
    lang = req.lang if req.lang in SYSTEM_PROMPTS else "es"
    system = SYSTEM_PROMPTS[lang].format(
        context=context or "Sin contexto específico disponible."
    )

    # Construir historial compatible con Groq
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    async def stream():
        response = await groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system}, *messages],
            max_tokens=600,
            temperature=0.7,
            stream=True,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield f"0:{json.dumps(delta)}\n"
        yield "d:{}\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"X-Vercel-AI-Data-Stream": "v1"},
    )