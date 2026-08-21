# File: app/routers/chat.py
import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from groq import AsyncGroq
from app.services.rag import search_context
from app.db.postgres import get_pool
from app.core.config import settings
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])
groq = AsyncGroq(api_key=settings.groq_api_key)

# NOTA: el repo tiene "openai/gpt-oss-120b" como modelo actual. Si en tu rama
# local lo cambiaste a otro (p. ej. un Qwen), ajusta esta constante — el resto
# del archivo no depende del modelo específico.
MODEL_NAME = "openai/gpt-oss-120b"
MAX_HISTORY_MESSAGES = 16
MAX_RESPONSE_TOKENS = 2048
CALENDLY_URL = "https://calendly.com/d/cv8d-jjp-nhd"


# Schema compatible con Vercel AI SDK useChat
class Message(BaseModel):
    role: str
    content: str


class PageContext(BaseModel):
    url: Optional[str] = None
    path: Optional[str] = None
    referrer: Optional[str] = None
    visited: Optional[List[str]] = None


class UserContext(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None


class Attachment(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    # Data URL en base64 (imagen/PDF). No se manda al modelo todavía — ver
    # build_extra_context(): openai/gpt-oss-120b vía Groq no lee imágenes,
    # así que solo avisamos al modelo que hay un adjunto que no puede ver.
    data_url: Optional[str] = None


class ChatRequest(BaseModel):
    messages: List[Message]
    lang: Optional[str] = "es"
    page_context: Optional[PageContext] = None
    user: Optional[UserContext] = None
    attachments: Optional[List[Attachment]] = None


class FeedbackRequest(BaseModel):
    message_id: str
    rating: str  # "up" | "down"
    lang: Optional[str] = "es"
    user_message: Optional[str] = None
    assistant_message: Optional[str] = None


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

ACTIONS_COPY = {
    "es": {
        "pricing": {
            "title": "Precios a la medida",
            "body": "Cada proyecto es distinto — agenda una llamada rápida y te armamos una propuesta con números reales.",
            "button": "Agendar llamada",
        },
        "demo": {
            "title": "Agenda una demo",
            "body": "Coordinemos 20 minutos para mostrarte cómo encaja Datheón en tu operación.",
            "button": "Ver disponibilidad",
        },
    },
    "en": {
        "pricing": {
            "title": "Pricing, tailored",
            "body": "Every project is different — book a quick call and we'll put together real numbers.",
            "button": "Book a call",
        },
        "demo": {
            "title": "Book a demo",
            "body": "Let's grab 20 minutes to show you how Datheón fits your operation.",
            "button": "Check availability",
        },
    },
    "fr": {
        "pricing": {
            "title": "Tarifs sur mesure",
            "body": "Chaque projet est différent — réservez un appel rapide et on vous prépare une proposition concrète.",
            "button": "Réserver un appel",
        },
        "demo": {
            "title": "Réservez une démo",
            "body": "Prenons 20 minutes pour vous montrer comment Datheón s'intègre à votre activité.",
            "button": "Voir les disponibilités",
        },
    },
}

SUGGESTIONS_COPY = {
    "es": {
        "pricing": ["¿Puedo agendar una llamada?", "¿Qué incluye el servicio?", "Prefiero que me escriban por correo"],
        "demo": ["¿Cuánto cuesta?", "¿Qué necesito preparar?", "Prefiero que me escriban por correo"],
        "default": ["Cuéntame más", "¿Cómo empezamos?", "Quiero hablar con alguien del equipo"],
    },
    "en": {
        "pricing": ["Can I book a call?", "What's included?", "I'd rather get an email"],
        "demo": ["How much does it cost?", "What should I prepare?", "I'd rather get an email"],
        "default": ["Tell me more", "How do we start?", "I'd like to talk to someone on the team"],
    },
    "fr": {
        "pricing": ["Puis-je réserver un appel ?", "Qu'est-ce qui est inclus ?", "Je préfère recevoir un e-mail"],
        "demo": ["Combien ça coûte ?", "Que dois-je préparer ?", "Je préfère recevoir un e-mail"],
        "default": ["Dites-m'en plus", "Comment commence-t-on ?", "Je veux parler à quelqu'un de l'équipe"],
    },
}

PRICING_KEYWORDS = [
    "precio", "precios", "costo", "cuesta", "cotiz", "presupuesto",
    "price", "pricing", "cost", "quote", "budget",
    "prix", "tarif", "devis", "coûte",
]
DEMO_KEYWORDS = [
    "demo", "agendar", "reunión", "reunion", "llamada", "cita", "hablar con",
    "schedule", "book a call", "meeting", "talk to someone", "call me",
    "rendez-vous", "rendezvous", "réunion", "appel",
]


def detect_action(text: str) -> Optional[str]:
    t = (text or "").lower()
    if any(k in t for k in DEMO_KEYWORDS):
        return "demo"
    if any(k in t for k in PRICING_KEYWORDS):
        return "pricing"
    return None


def build_action_payload(lang: str, action_key: Optional[str]) -> Optional[Dict[str, Any]]:
    if not action_key:
        return None
    copy = ACTIONS_COPY.get(lang, ACTIONS_COPY["es"]).get(action_key)
    if not copy:
        return None
    return {
        "type": "calendly_cta",
        "title": copy["title"],
        "body": copy["body"],
        "buttonLabel": copy["button"],
        "url": CALENDLY_URL,
    }


def build_suggestions(lang: str, action_key: Optional[str]) -> List[str]:
    table = SUGGESTIONS_COPY.get(lang, SUGGESTIONS_COPY["es"])
    return table.get(action_key or "default", table["default"])


def build_extra_context(lang: str, req: ChatRequest) -> str:
    """Convierte contexto de navegación / usuario / adjuntos en líneas que el
    modelo puede usar para sonar consciente de la situación del visitante."""
    lines: List[str] = []

    if req.user and req.user.name:
        who = req.user.name
        if req.user.company:
            who += f" ({req.user.company})" if lang != "en" else f" from {req.user.company}"
        lines.append(
            f"El usuario autenticado se llama {who}. Puedes saludarlo por su nombre."
            if lang == "es" else
            f"The authenticated user is {who}. You may greet them by name."
        )

    if req.page_context and req.page_context.path:
        lines.append(
            f"El usuario está actualmente en la página: {req.page_context.path}."
            if lang == "es" else
            f"The user is currently on the page: {req.page_context.path}."
        )

    if req.attachments:
        names = ", ".join(a.name for a in req.attachments if a.name) or "un archivo"
        lines.append(
            f"El usuario adjuntó: {names}. Todavía no puedes leer imágenes o PDFs directamente "
            "— pide que describan el contenido relevante en texto."
            if lang == "es" else
            f"The user attached: {names}. You cannot read image/PDF contents yet "
            "— ask them to describe the relevant content in text."
        )

    return "\n".join(lines)


@router.post("")
@router.post("/")
async def chat(req: ChatRequest, request: Request):
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

    extra_context = build_extra_context(lang, req)
    if extra_context:
        system = f"{system}\n\n{extra_context}"

    # Recortar el historial a los últimos N mensajes para no acercarnos al
    # límite de contexto del modelo en conversaciones largas (el widget ahora
    # persiste la conversación en localStorage, así que puede crecer bastante).
    trimmed = req.messages[-MAX_HISTORY_MESSAGES:]
    messages = [{"role": m.role, "content": m.content} for m in trimmed]

    action_key = detect_action(last_user_msg)
    data_payload = {
        "action": build_action_payload(lang, action_key),
        "suggestions": build_suggestions(lang, action_key),
    }

    async def stream():
        try:
            # Antes del texto: el widget puede mostrar la tarjeta/sugerencias
            # apenas responde, sin esperar a que termine el streaming.
            yield f"2:{json.dumps([data_payload])}\n"

            response = await groq.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "system", "content": system}, *messages],
                max_tokens=MAX_RESPONSE_TOKENS,
                temperature=0.7,
                stream=True,
            )

            finish_reason = "stop"
            async for chunk in response:
                # El cliente pudo haber cerrado la conexión (botón "detener"
                # del widget, o cerró la pestaña) — sin este check seguiríamos
                # consumiendo tokens de Groq en segundo plano igual.
                if await request.is_disconnected():
                    finish_reason = "stop"
                    logger.info("Cliente desconectado, deteniendo generación (lang=%s)", lang)
                    try:
                        await response.response.aclose()
                    except Exception:  # noqa: BLE001
                        pass
                    break

                choice = chunk.choices[0]
                delta = choice.delta.content
                if delta:
                    yield f"0:{json.dumps(delta)}\n"
                if choice.finish_reason:
                    finish_reason = choice.finish_reason

            if finish_reason == "length":
                logger.warning("Respuesta truncada por max_tokens (lang=%s)", lang)

            yield f'd:{json.dumps({"finishReason": finish_reason})}\n'

        except Exception as exc:  # noqa: BLE001
            logger.exception("Fallo al generar respuesta de chat")
            # Parte de error del protocolo de Vercel AI SDK: useChat la
            # levanta como `error` y el widget puede mostrar "Reintentar".
            yield f"3:{json.dumps(str(exc))}\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"X-Vercel-AI-Data-Stream": "v1"},
    )


@router.post("/feedback")
@router.post("/feedback/")
async def feedback(payload: FeedbackRequest):
    """Guarda el feedback (👍/👎) en Postgres, en la misma DB de pgvector.

    Reutiliza chat_messages/chat_sessions ya definidas en app/db/postgres.py
    (existían en el schema pero el router de chat nunca las usaba)."""
    pool = await get_pool()
    try:
        async with pool.connection() as conn:
            await conn.execute(
                """
                INSERT INTO chat_feedback (id, message_id, rating, lang, user_message, assistant_message)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid.uuid4()),
                    payload.message_id,
                    payload.rating,
                    payload.lang,
                    payload.user_message,
                    payload.assistant_message,
                ),
            )
    except Exception:
        logger.exception("No se pudo guardar el feedback en la base de datos")
        return {"ok": False}

    return {"ok": True}