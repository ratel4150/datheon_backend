# Datheón API — FastAPI + Groq + pgvector

Backend de IA para la landing de Datheón. Corre en Railway conectado a Neon PostgreSQL.

## Stack

- **FastAPI** — framework Python async
- **Groq** — LLM ultrarrápido (Llama 3.3 70B)
- **OpenAI** — embeddings (text-embedding-3-small)
- **pgvector** — búsqueda vectorial en PostgreSQL
- **Neon** — PostgreSQL serverless
- **Railway** — hosting

---

## Setup local

### 1. Clonar y crear entorno virtual

```bash
git clone <repo>
cd datheon-api
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

### 2. Variables de entorno

```bash
cp .env.example .env
# Editar .env con tus keys reales
```

### 3. Crear base de datos en Neon

1. Ir a neon.tech → crear proyecto "datheon"
2. Copiar la connection string a `DATABASE_URL` en `.env`
3. La extensión `vector` se activa automáticamente con el script

### 4. Indexar documentos de Datheón

```bash
python scripts/index_documents.py
```

Esto crea las tablas, activa pgvector e indexa los 11 documentos base sobre servicios,
proceso, equipo y precios de Datheón.

### 5. Correr el servidor

```bash
uvicorn main:app --reload --port 8000
```

Documentación interactiva: http://localhost:8000/docs

---

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/chat` | Chat RAG con streaming (Groq) |
| POST | `/api/v1/documents/index` | Indexar un documento |
| POST | `/api/v1/documents/index-batch` | Indexar varios documentos |
| GET  | `/api/v1/documents/search?q=...` | Buscar contexto (debug) |
| POST | `/api/v1/contact` | Formulario de contacto (Resend) |
| GET  | `/health` | Health check para Railway |

---

## Deploy en Railway

### 1. Instalar Railway CLI

```bash
npm install -g @railway/cli
railway login
```

### 2. Crear proyecto

```bash
railway init
# Seleccionar "Empty project"
railway up
```

### 3. Agregar variables de entorno en Railway

En el dashboard de Railway → tu proyecto → Variables:

```
GROQ_API_KEY        = gsk_...
OPENAI_API_KEY      = sk-...
DATABASE_URL        = postgresql://... (de Neon)
INTERNAL_API_KEY    = string_aleatorio_seguro
ENVIRONMENT         = production
ALLOWED_ORIGINS     = https://datheon.com,https://www.datheon.com
RESEND_API_KEY      = re_... (opcional, para formulario de contacto)
```

### 4. Deploy

```bash
railway up
```

Railway detecta el `Dockerfile` automáticamente. El primer deploy tarda ~3 minutos.

---

## Conectar con Next.js

En `.env.local` del proyecto Next.js:

```
FASTAPI_URL=https://tu-proyecto.railway.app
INTERNAL_API_KEY=mismo_string_que_en_railway
```

En `src/app/api/chat/route.ts`:

```ts
export async function POST(req: Request) {
  const body = await req.json()
  const response = await fetch(`${process.env.FASTAPI_URL}/api/v1/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Internal-Key': process.env.INTERNAL_API_KEY ?? '',
    },
    body: JSON.stringify(body),
  })
  return new Response(response.body, {
    headers: { 'Content-Type': 'text/event-stream' },
  })
}
```

---

## Agregar más documentos al RAG

Editar `scripts/index_documents.py` — agregar objetos al array `DOCUMENTS`:

```python
{
    "id": "caso-exito-ecommerce",
    "title": "Caso de éxito: E-commerce con IA",
    "category": "casos",
    "content": "Implementamos un motor de recomendaciones para...",
},
```

Luego correr:

```bash
python scripts/index_documents.py
```

Los documentos existentes se actualizan automáticamente (upsert).

---

## Estructura del proyecto

```
datheon-api/
├── main.py                    # App FastAPI + lifespan
├── requirements.txt
├── Dockerfile
├── railway.toml
├── .env.example
├── scripts/
│   └── index_documents.py     # Indexación RAG
└── app/
    ├── core/
    │   └── config.py          # Settings con pydantic
    ├── db/
    │   └── postgres.py        # Pool asyncpg + init SQL
    ├── models/
    │   └── schemas.py         # Pydantic schemas
    ├── services/
    │   ├── rag.py             # Embeddings + búsqueda pgvector
    │   └── leads.py           # Lead scoring por reglas
    └── routers/
        ├── chat.py            # POST /chat con streaming Groq
        ├── documents.py       # Indexación de documentos
        └── contact.py         # Formulario de contacto
```
# datheon_backend
