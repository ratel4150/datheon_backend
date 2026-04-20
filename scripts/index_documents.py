import asyncio
import selectors
import sys
import os

# Fix para Windows — ProactorEventLoop no es compatible con psycopg3
if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.DefaultEventLoopPolicy()
    )
    selector = selectors.SelectSelector()
    loop = asyncio.SelectorEventLoop(selector)
    asyncio.set_event_loop(loop)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag import index_document
from app.db.postgres import init_db, close_pool

DOCUMENTS = [
    {
        "id": "servicios-ai-agentes",
        "title": "AI SaaS y Agentes Autónomos",
        "category": "servicios",
        "content": """Datheón desarrolla productos SaaS potenciados por IA y agentes autónomos 
que ejecutan tareas completas sin intervención humana.
Tecnologías: LangGraph, CrewAI, RAG con pgvector y Pinecone.
Casos de uso: asistentes entrenados sobre documentos propios, agentes que navegan sistemas,
automatización de flujos complejos multi-step.
Tiempo estimado: 4-8 semanas para agente básico, 3-6 meses para producto completo.
Precio referencial: desde $8,000 USD para agentes básicos.""",
    },
    {
        "id": "servicios-automatizacion",
        "title": "Automatización y Lead Systems",
        "category": "servicios",
        "content": """Sistemas que capturan, califican y convierten leads automáticamente.
Herramientas: n8n, Make, RPA con Python y OpenCV para procesar documentos sin API.
Chatbots de ventas en WhatsApp, web y email con NLP que convierten 24/7.
CRM con lead scoring con ML y notificaciones en tiempo real.
Reducción promedio de trabajo manual: 60-80% en procesos repetitivos.""",
    },
    {
        "id": "servicios-saas-web",
        "title": "SaaS, Web Apps y E-commerce",
        "category": "servicios",
        "content": """Desarrollo fullstack de aplicaciones web de alto rendimiento.
Stack: Next.js 15, NestJS, FastAPI, PostgreSQL, Redis.
Desde MVPs hasta plataformas multi-tenant con millones de usuarios.
E-commerce con Stripe/MercadoPago, inventario y panel admin.
Tiempo para MVP funcional: 6-10 semanas.""",
    },
    {
        "id": "servicios-mobile",
        "title": "Aplicaciones Móviles y Backend",
        "category": "servicios",
        "content": """Apps iOS y Android con Flutter (una sola base de código) o nativas Swift/Kotlin.
Backend con NestJS o FastAPI, APIs REST y GraphQL.
Push notifications, WebSockets, sincronización offline.
Deploy automático a App Store y Play Store con CI/CD.""",
    },
    {
        "id": "servicios-cloud-devops",
        "title": "Cloud, DevOps e Infraestructura",
        "category": "servicios",
        "content": """Infraestructura cloud escalable en AWS y GCP con Terraform como código.
Kubernetes, Docker, CI/CD con GitHub Actions y ArgoCD.
Observabilidad con OpenTelemetry, Grafana y Sentry.
Seguridad: OWASP, ISO 27001, gestión de secretos con Vault.
Uptime garantizado del 99.9% con monitoreo 24/7.""",
    },
    {
        "id": "servicios-iot",
        "title": "IoT: Hardware + Software + SaaS",
        "category": "servicios",
        "content": """Conectamos dispositivos físicos al mundo digital, desde el firmware hasta el dashboard.
Protocolos: MQTT, CoAP, Modbus sobre ESP32, Raspberry Pi y PLCs industriales.
Edge computing para operar sin conexión estable.
Plataforma SaaS de monitoreo en tiempo real con alertas y control remoto.
Integración directa con ERP/CRM para que los datos del sensor alimenten tus sistemas.""",
    },
    {
        "id": "servicios-odoo",
        "title": "Odoo ERP y Transformación Digital",
        "category": "servicios",
        "content": """Implementación completa de Odoo: ventas, compras, inventario, contabilidad, RRHH.
Módulos custom en Python/XML para necesidades específicas que Odoo estándar no cubre.
Integración de IA sobre Odoo: asistente que responde preguntas sobre el ERP.
Migración desde SAP/Dynamics con auditoría y mapeo de datos.
Conexión con e-commerce, POS, pasarelas de pago y marketplaces.""",
    },
    {
        "id": "proceso-trabajo",
        "title": "Proceso de Trabajo",
        "category": "proceso",
        "content": """El proceso de Datheón tiene 6 fases:
1. Descubrimiento (1 semana): entrevistas, documentación de requisitos, propuesta técnica y económica.
2. Diseño (1 semana): prototipos UI/UX en Figma, arquitectura técnica.
3. Desarrollo iterativo: sprints de 2 semanas con revisión semanal con el cliente.
4. QA: tests automatizados unitarios, integración y e2e. Demos cada 2 semanas.
5. Despliegue: release planificado, rollout gradual, soporte 48h post-launch.
6. Mantenimiento: SLA definido, mejoras basadas en métricas reales.""",
    },
    {
        "id": "equipo",
        "title": "Equipo Datheón",
        "category": "empresa",
        "content": """Datheón fue fundada en 2023 y tiene 2 especialistas técnicos senior:
- Angel Clavellina: Sr. Data Analyst y AI. Especialista en pipelines de datos, modelos predictivos y RAG.
- Arturo Chavez: Sr. Full Stack Developer. Arquitecto de software, SaaS, APIs y cloud.
17 proyectos completados, 50 clientes satisfechos en múltiples industrias.
Idiomas de servicio: Español, Inglés y Francés.""",
    },
    {
        "id": "contacto-precios",
        "title": "Contacto y Precios",
        "category": "empresa",
        "content": """Los precios dependen del alcance y complejidad del proyecto.
Rangos referenciales:
- Proyectos pequeños (MVP, landing con IA, automatización simple): $3,000 - $8,000 USD
- Proyectos medianos (SaaS completo, agente IA avanzado, app móvil): $8,000 - $30,000 USD
- Proyectos grandes (plataforma enterprise, IoT, transformación digital): $30,000+ USD
Para obtener una propuesta personalizada y gratuita: calendly.com/d/cv8d-jjp-nhd
Email: hola@datheon.com""",
    },
    {
        "id": "tecnologias",
        "title": "Stack Tecnológico 2025-2026",
        "category": "tecnologia",
        "content": """Datheón trabaja con tecnologías de vanguardia:
Frontend: Next.js 15, React 19, Tailwind CSS, Framer Motion.
Backend: FastAPI (Python), NestJS (TypeScript), Node.js.
IA: Groq (Llama 3.3), OpenAI GPT-4o, Anthropic Claude, LangGraph, RAG con pgvector.
Mobile: Flutter, Swift, Kotlin.
Cloud: AWS (Lambda, ECS, RDS), GCP, Terraform, Kubernetes, Docker.
Bases de datos: PostgreSQL + pgvector, MongoDB, Redis.
IoT: MQTT, ESP32, Raspberry Pi, Node-RED.
ERP: Odoo 17/18.""",
    },
]

async def main():
    print(f"Indexando {len(DOCUMENTS)} documentos...")
    await init_db()
    for doc in DOCUMENTS:
        result = await index_document(
            doc_id=doc["id"],
            title=doc["title"],
            content=doc["content"],
            category=doc["category"],
        )
        print(f"  OK {doc['id']}")
    await close_pool()
    print(f"\nIndexacion completa: {len(DOCUMENTS)} documentos listos.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(main(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
    else:
        asyncio.run(main())