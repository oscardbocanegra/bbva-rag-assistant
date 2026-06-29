# BBVA RAG Assistant

Sistema RAG en Python para consultar contenido institucional de BBVA Colombia mediante recuperación semántica, embeddings locales, base vectorial, memoria conversacional persistente y una interfaz web.

> Prueba técnica para rol de Machine Learning Engineer / AI Engineer.

---

## Características principales

* Extracción y procesamiento de contenido de `https://www.bbva.com.co/`.
* Persistencia de datos crudos y limpios.
* Chunking con overlap configurable.
* Embeddings locales con `intfloat/multilingual-e5-small`.
* Base vectorial Qdrant.
* Generación de respuestas con Ollama y `qwen2.5:3b`.
* Respuestas grounded con fuentes consultadas.
* Historial conversacional persistente mediante `session_id`.
* Memoria configurable de los últimos N mensajes.
* API REST con FastAPI.
* Interfaz conversacional y dashboard analítico con Streamlit.
* Métricas de sesiones, preguntas, respuestas, latencia y chunks recuperados.
* Pruebas unitarias.
* Ejecución completa con Docker Compose.

---

## Arquitectura

```text
                  ┌──────────────────────────────┐
                  │     Sitio web BBVA Colombia  │
                  │   https://www.bbva.com.co/   │
                  └──────────────┬───────────────┘
                                 │
                     Scraper / Snapshots HTML
                                 │
                 ┌───────────────▼───────────────┐
                 │         Content Cleaner        │
                 │  Raw HTML → JSON procesado     │
                 └───────────────┬───────────────┘
                                 │
                 ┌───────────────▼───────────────┐
                 │ Chunking + Embeddings locales  │
                 │ multilingual-e5-small          │
                 └───────────────┬───────────────┘
                                 │
                         ┌───────▼────────┐
                         │     Qdrant     │
                         │ Vector Database│
                         └───────┬────────┘
                                 │
Usuario ──► Streamlit ──► FastAPI ──► Retriever ──► Ollama
                                 │                    │
                                 │                    ▼
                                 │             Respuesta RAG
                                 │             con fuentes
                                 │
                         ┌───────▼────────┐
                         │   PostgreSQL    │
                         │ sesiones, chat, │
                         │ métricas        │
                         └────────────────┘
```

---

## Stack tecnológico

| Componente      | Tecnología                       | Justificación                                                                       |
| --------------- | -------------------------------- | ----------------------------------------------------------------------------------- |
| Backend API     | FastAPI                          | API ligera, tipada, rápida y con documentación Swagger automática.                  |
| Interfaz        | Streamlit                        | Permite construir una interfaz conversacional y dashboard analítico en poco tiempo. |
| Base vectorial  | Qdrant                           | Open source, self-hosted, compatible con Docker y búsqueda vectorial eficiente.     |
| Base relacional | PostgreSQL 16                    | Persistencia de sesiones, mensajes y métricas conversacionales.                     |
| Embeddings      | `intfloat/multilingual-e5-small` | Modelo gratuito, local y adecuado para recuperación semántica en español.           |
| LLM             | Ollama + `qwen2.5:3b`            | Modelo local, gratuito y ejecutable mediante Docker.                                |
| Scraping        | `httpx` + BeautifulSoup          | Stack simple para descarga, parsing y limpieza de HTML.                             |
| ORM             | SQLAlchemy                       | Persistencia desacoplada y controlada para PostgreSQL.                              |
| Contenedores    | Docker Compose                   | Permite levantar todos los servicios con un único comando.                          |
| Testing         | Pytest                           | Pruebas unitarias rápidas y reproducibles.                                          |

---

## Patrones de diseño utilizados

### 1. Repository Pattern

**Ubicación:** `app/database/repositories.py`

La clase `ConversationRepository` encapsula el acceso a PostgreSQL para sesiones y mensajes.

Beneficios:

* Separa la lógica de persistencia de la lógica de negocio.
* Facilita pruebas unitarias y futuros cambios de almacenamiento.
* Evita consultas SQL dispersas en endpoints o servicios.

---

### 2. Service Layer

**Ubicación:** `app/conversation/conversation_service.py`, `app/rag/rag_service.py`, `app/analytics/analytics_service.py`

Los servicios concentran la lógica de negocio:

* `ConversationService`: administra sesión, memoria, persistencia y ejecución RAG.
* `RAGService`: coordina retrieval, contexto, prompting y generación.
* `AnalyticsService`: calcula métricas del histórico conversacional.

Beneficios:

* Endpoints más simples.
* Responsabilidades claramente separadas.
* Mayor mantenibilidad.

---

### 3. Adapter Pattern

**Ubicación:** `app/rag/ollama_client.py`, `app/ingestion/qdrant_indexer.py`

Los adaptadores encapsulan integración con herramientas externas:

* `OllamaClient` abstrae la API de Ollama.
* `QdrantIndexer` abstrae creación de colecciones y carga de vectores.

Beneficios:

* Menor acoplamiento con APIs externas.
* Facilita reemplazar Ollama o Qdrant en el futuro.
* Centraliza detalles de integración.

---

### 4. Factory / Singleton mediante caché

**Ubicación:** `app/ingestion/embedding_service.py`, `app/database/connection.py`

Se reutilizan recursos costosos mediante `lru_cache`:

* Modelo de embeddings.
* Engine de SQLAlchemy.
* Fábrica de sesiones de PostgreSQL.

Beneficios:

* Evita cargar el modelo de embeddings repetidamente.
* Reduce sobrecarga de conexiones.
* Mejora rendimiento y estabilidad.

---

### 5. Strategy implícita de adquisición de contenido

**Ubicación:** `app/scraping/`

El proyecto soporta dos mecanismos de adquisición:

* Scraping HTTP mediante sitemap.
* Procesamiento de snapshots HTML guardados localmente.

Beneficios:

* El pipeline sigue funcionando aunque la fuente aplique controles anti-bot.
* Permite reproducibilidad y pruebas controladas.
* Mantiene la misma estructura de salida para ambas estrategias.

---

## Estructura del proyecto

```text
bbva-rag-assistant/
│
├── app/
│   ├── analytics/
│   │   ├── analytics_service.py
│   │   └── routes_analytics.py
│   │
│   ├── api/
│   │   ├── routes_chat.py
│   │   └── schemas.py
│   │
│   ├── conversation/
│   │   ├── conversation_service.py
│   │   └── memory_manager.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   ├── models.py
│   │   └── repositories.py
│   │
│   ├── ingestion/
│   │   ├── chunker.py
│   │   ├── document_processor.py
│   │   ├── embedding_service.py
│   │   └── qdrant_indexer.py
│   │
│   ├── rag/
│   │   ├── ollama_client.py
│   │   ├── rag_service.py
│   │   └── retriever.py
│   │
│   ├── scraping/
│   │   ├── bbva_scraper.py
│   │   ├── content_cleaner.py
│   │   ├── local_snapshot_loader.py
│   │   └── sitemap_reader.py
│   │
│   └── main.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── source_snapshots/
│
├── docker/
│   ├── Dockerfile.api
│   └── Dockerfile.ui
│
├── scripts/
│   ├── init_database.py
│   ├── run_ingestion.py
│   ├── run_local_snapshot_loader.py
│   └── run_scraper.py
│
├── tests/
│   ├── test_chunker.py
│   ├── test_content_cleaner.py
│   └── test_memory_manager.py
│
├── ui/
│   └── streamlit_app.py
│
├── docker-compose.yml
├── requirements.txt
├── requirements-ui.txt
├── .env.example
└── README.md
```

---

## Requisitos previos

* Docker Desktop instalado y en ejecución.
* Docker Compose disponible.
* Git.
* Mínimo 8 GB de RAM recomendados.
* Espacio libre aproximado de 6 GB para imágenes, dependencias y modelo local.

---

## Configuración inicial

Clona el repositorio:

```bash
git clone <URL_DEL_REPOSITORIO>
cd bbva-rag-assistant
```

Crea tu archivo de variables de entorno:

```powershell
Copy-Item .env.example .env
```

Variables principales:

```env
APP_NAME=BBVA RAG Assistant
APP_ENV=development
APP_PORT=8000

POSTGRES_DB=rag_db
POSTGRES_USER=rag_user
POSTGRES_PASSWORD=rag_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION=bbva_content

EMBEDDING_MODEL=intfloat/multilingual-e5-small
CHUNK_SIZE=700
CHUNK_OVERLAP=120

OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_TIMEOUT_SECONDS=120

CONVERSATION_MEMORY_MESSAGES=6
```

---

## Levantar la solución

Construye y levanta todos los servicios:

```powershell
docker compose up --build -d
```

Verifica el estado:

```powershell
docker compose ps
```

Servicios esperados:

| Servicio         | URL / Puerto                      |
| ---------------- | --------------------------------- |
| Streamlit UI     | `http://localhost:8501`           |
| FastAPI Swagger  | `http://localhost:8000/docs`      |
| FastAPI Health   | `http://localhost:8000/health`    |
| Qdrant Dashboard | `http://localhost:6333/dashboard` |
| PostgreSQL       | `localhost:5432`                  |
| Ollama           | `localhost:11434`                 |

---

## Descargar el modelo local

La primera vez, descarga el modelo de Ollama:

```powershell
docker compose exec ollama ollama pull qwen2.5:3b
```

Verifica que esté disponible:

```powershell
docker compose exec ollama ollama list
```

---

## Inicializar PostgreSQL

Crea las tablas de sesiones y mensajes:

```powershell
docker compose exec api python scripts/init_database.py
```

Tablas esperadas:

```text
conversation_sessions
conversation_messages
```

---

## Ingestión de contenido BBVA

### Limitación de scraping

BBVA Colombia puede responder `HTTP 403` a solicitudes automatizadas provenientes de algunos entornos Docker o IPs. Por esta razón, el proyecto incluye dos mecanismos:

1. Scraping mediante sitemap cuando el servidor lo permite.
2. Procesamiento de snapshots HTML locales como mecanismo reproducible de contingencia.

El contenido sigue siendo exclusivamente de `https://www.bbva.com.co/`.

---

### Opción recomendada: snapshots HTML locales

1. Abre una página institucional de BBVA en un navegador.
2. Guarda la página completa como HTML.
3. Ubica el archivo en:

```text
data/source_snapshots/
```

Ejemplos de nombres:

```text
home.html
tarjeta_credito.html
uso_tarjeta_credito.html
diferencia_credito_debito.html
```

Procesa snapshots:

```powershell
docker compose exec api python scripts/run_local_snapshot_loader.py
```

Esto genera:

```text
data/raw/
data/processed/
```

Luego genera embeddings e indexa en Qdrant:

```powershell
docker compose exec api python scripts/run_ingestion.py
```

Verifica puntos indexados:

```powershell
docker compose exec api python -c "from qdrant_client import QdrantClient; c=QdrantClient(host='qdrant', port=6333); print(c.get_collection('bbva_content').points_count)"
```

---

### Opción alternativa: scraper HTTP

Si BBVA permite acceso desde el entorno:

```powershell
docker compose exec api python scripts/run_scraper.py
```

---

## Uso de la interfaz

Abre:

```text
http://localhost:8501
```

Funciones disponibles:

* Preguntas sobre el contenido indexado de BBVA.
* Sesión persistente por `session_id`.
* Memoria de los últimos N mensajes.
* Fuentes utilizadas en cada respuesta.
* Latencia de cada interacción.
* Nueva conversación.
* Dashboard de analítica conversacional.

Ejemplos de preguntas:

```text
¿Qué información ofrece BBVA sobre ahorro?
¿Qué es una tarjeta de crédito?
¿Cuál es la diferencia entre tarjeta débito y tarjeta crédito?
¿Cómo puedo usar responsablemente una tarjeta de crédito?
¿Y cómo puedo aprender más sobre ese tema?
```

---

## API REST

### Crear o continuar conversación

```http
POST /api/v1/chat
```

Ejemplo de solicitud:

```json
{
  "message": "¿Qué información ofrece BBVA sobre ahorro?"
}
```

Ejemplo de respuesta:

```json
{
  "session_id": "UUID",
  "answer": "Respuesta generada con base en el contenido recuperado.",
  "sources": [
    {
      "title": "BBVA Colombia",
      "url": "https://www.bbva.com.co/",
      "score": 0.84
    }
  ],
  "retrieved_chunks": 3,
  "latency_ms": 23000
}
```

Para continuar la misma conversación:

```json
{
  "session_id": "UUID_DE_LA_SESION",
  "message": "¿Y cómo puedo aprender más sobre ese tema?"
}
```

---

### Consultar historial

```http
GET /api/v1/conversations/{session_id}
```

---

### Métricas conversacionales

```http
GET /api/v1/analytics/summary
GET /api/v1/analytics/daily-activity
GET /api/v1/analytics/recent-sessions
GET /api/v1/analytics/recent-questions
```

---

## Analítica disponible

El dashboard y API analítica calculan:

* Número total de sesiones.
* Número total de mensajes.
* Preguntas y respuestas generadas.
* Promedio de mensajes por sesión.
* Latencia promedio.
* Promedio de chunks recuperados.
* Actividad diaria.
* Sesiones recientes.
* Preguntas recientes.

Estas métricas permiten analizar adopción, comportamiento conversacional, desempeño técnico y trazabilidad de uso.

---

## Ejecución de pruebas

Ejecuta la suite de pruebas unitarias:

```powershell
docker compose exec api pytest -v tests
```

Pruebas incluidas:

* Limpieza de contenido HTML.
* Eliminación de navegación y scripts.
* Chunking con overlap.
* Manejo de texto vacío.
* Conversión de historial a formato compatible con Ollama.

Resultado esperado:

```text
4 passed
```

---

## Observabilidad

La API registra solicitudes con:

* `request_id`
* método HTTP;
* ruta;
* código de estado;
* latencia.

Para visualizar logs:

```powershell
docker compose logs -f api
```

Ejemplo:

```text
request_id=... method=POST path=/api/v1/chat status=200 latency_ms=24000
```

---

## Decisiones de diseño relevantes

### Modelo local

Se eligió `qwen2.5:3b` porque permite ejecutar el flujo sin depender de APIs pagas. La contrapartida es una latencia mayor que servicios cloud, especialmente en CPU.

### Embeddings locales

Se eligió `multilingual-e5-small` por su balance entre calidad, tamaño y soporte para español.

### Persistencia separada

* Qdrant almacena vectores y metadata recuperable.
* PostgreSQL almacena sesiones, mensajes y métricas.
* Archivos JSON mantienen trazabilidad raw y processed.

### Memoria limitada

La memoria se limita mediante:

```env
CONVERSATION_MEMORY_MESSAGES=6
```

Esto reduce crecimiento del prompt y mantiene conversaciones manejables.

### Fuentes visibles

Cada respuesta incluye fuentes para facilitar trazabilidad y reducir riesgo de alucinaciones.

---

## Limitaciones conocidas

* BBVA puede bloquear scraping automatizado con `HTTP 403`.
* La calidad depende de las páginas HTML disponibles e indexadas.
* Con pocos documentos, algunas consultas pueden recuperar contexto poco específico.
* El modelo local puede tardar entre 15 y 40 segundos dependiendo del hardware.
* No se implementó autenticación de usuarios.
* La solución está pensada como prueba técnica y no como sistema productivo completo.
* No se incluye reranker; se priorizó funcionalidad end-to-end, persistencia, analítica, pruebas y reproducibilidad.

---

## Mejoras futuras

* Implementar reranker CrossEncoder.
* Agregar evaluación automática RAG con dataset de preguntas y respuestas esperadas.
* Integrar feedback explícito de usuario positivo/negativo.
* Agregar autenticación y autorización.
* Implementar carga incremental basada en `content_hash`.
* Agregar scheduler para re-ingestión periódica.
* Añadir métricas con Prometheus y dashboard Grafana.
* Incorporar búsqueda híbrida BM25 + embeddings.
* Implementar streaming de tokens en la UI.
* Añadir filtros por categoría, URL o fecha de extracción.

---

## Comandos útiles

Detener servicios:

```powershell
docker compose down
```

Detener y borrar volúmenes:

```powershell
docker compose down -v
```

Reconstruir servicios:

```powershell
docker compose up --build -d
```

Ver logs de API:

```powershell
docker compose logs -f api
```

Ver logs de UI:

```powershell
docker compose logs -f ui
```

Ver colección Qdrant:

```powershell
docker compose exec api python -c "from qdrant_client import QdrantClient; c=QdrantClient(host='qdrant', port=6333); print(c.get_collection('bbva_content'))"
```

---

## Autor

Prueba técnica desarrollada como una solución RAG dockerizada sobre contenido institucional de BBVA Colombia.
