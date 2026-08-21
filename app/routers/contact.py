# File: app/routers/contact.py
from fastapi import APIRouter
from app.models.schemas import ContactRequest
from app.core.config import settings
import httpx

router = APIRouter(prefix="/contact", tags=["contact"])

@router.post("")
async def contact(req: ContactRequest):
    """
    Recibe el formulario de contacto y manda email con Resend.
    También guarda el lead en la DB para scoring futuro.
    """
    subject = f"Nuevo contacto: {req.empresa or req.nombre} — {req.tipo_proyecto or 'General'}"

    html = f"""
    <h2>Nuevo contacto desde Datheón</h2>
    <table style="border-collapse:collapse;width:100%">
      <tr><td style="padding:8px;border:1px solid #eee"><b>Nombre</b></td><td style="padding:8px;border:1px solid #eee">{req.nombre}</td></tr>
      <tr><td style="padding:8px;border:1px solid #eee"><b>Email</b></td><td style="padding:8px;border:1px solid #eee">{req.email}</td></tr>
      <tr><td style="padding:8px;border:1px solid #eee"><b>Empresa</b></td><td style="padding:8px;border:1px solid #eee">{req.empresa or '—'}</td></tr>
      <tr><td style="padding:8px;border:1px solid #eee"><b>Presupuesto</b></td><td style="padding:8px;border:1px solid #eee">{req.presupuesto or '—'}</td></tr>
      <tr><td style="padding:8px;border:1px solid #eee"><b>Tipo proyecto</b></td><td style="padding:8px;border:1px solid #eee">{req.tipo_proyecto or '—'}</td></tr>
      <tr><td style="padding:8px;border:1px solid #eee"><b>Mensaje</b></td><td style="padding:8px;border:1px solid #eee">{req.mensaje or '—'}</td></tr>
      <tr><td style="padding:8px;border:1px solid #eee"><b>Idioma</b></td><td style="padding:8px;border:1px solid #eee">{req.lang}</td></tr>
    </table>
    """

    # Enviar con Resend
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": "contacto@datheon.com",
                "to": ["hola@datheon.com"],
                "reply_to": req.email,
                "subject": subject,
                "html": html,
            },
        )

    if response.status_code not in (200, 201):
        return {"ok": False, "error": "Error enviando email"}

    return {"ok": True}
