# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

**Idioma:** Responde en español. Sé breve y directo. No expliques de más.

---

## Desarrollo Rápido 🚀

### Comando para ejecutar el bot
```bash
python bot.py
```

### Ejecutar tests
```bash
pytest tests/ -v
```

### Ejecutar test específico
```bash
pytest tests/test_handlers.py::test_add_movie -v
```

### Tests con cobertura
```bash
pytest --cov=backend tests/
```

### Limpiar caché de tests
```bash
rm -rf __pycache__ .pytest_cache
pytest tests/ -v
```

---

## Arquitectura del Proyecto 🏗️

### Flujo Principal
```
Usuario envía mensaje a Telegram
    ↓
bot.py (entry point)
    ↓
MessageParser (identifica comando/texto)
    ↓
¿IA habilitada? → AIProcessor (opcional)
    ↓
CommandHandler (ejecuta lógica)
    ↓
TMDbClient (búsqueda en TMDb)
    ↓
Storage (persistencia en JSON)
    ↓
Respuesta al usuario
```

### Componentes Principales

**bot.py** - Entry point del bot
- Inicializa la aplicación Telegram (python-telegram-bot)
- Configura handlers de comandos y mensajes
- Gestiona scheduler de notificaciones (APScheduler)
- Integra SecurityManager para sanitización de logs

**backend/parser.py** - Análisis de mensajes
- Detecta comandos (/add, /remove, /list, etc.)
- Extrae parámetros y argumentos
- Identifica modo conversacional vs. comandos

**backend/handlers.py** - Lógica de comandos
- `/add "Título"` - Agregar película/serie
- `/add_actor "Nombre"` - Monitorear actor
- `/remove "Título"` - Remover película/serie
- `/list` - Listar películas monitoreadas
- Retorna respuestas con botones de deshacer

**backend/tmdb_client.py** - Cliente de TMDb API
- Búsqueda de películas/series por título
- Búsqueda de actores/directores
- Extrae datos: TMDB ID, género, año, etc.
- Headers seguros con API key en Authorization header

**backend/storage.py** - Persistencia JSON
- Lee/escribe en `data/movies.json`
- Estructura: películas, actores, historial de notificaciones
- Método para evitar duplicados

**backend/notifier.py** - Notificaciones automáticas
- Tarea semanal (APScheduler) que verifica estrenos
- Compara fecha de estreno con últimas notificaciones
- Envía notificaciones solo una vez por película

**backend/ai_processor.py** - Procesamiento IA (opcional)
- Integración con Claude API
- Convierte lenguaje natural a comandos
- Activable con CLAUDE_API_KEY en .env

**backend/security.py** - Seguridad
- Sanitización de logs (reemplaza keys con ***REDACTED***)
- Recolector de claves sensibles
- Previene exposición de secrets en outputs

**backend/http_client.py** - Cliente HTTP
- Wrapper para requests con timeouts
- Reintentos en fallos transitorios

### Estructura de Datos

**data/movies.json**
```json
{
  "movies": {
    "12345": {  // TMDB ID
      "title": "Avatar: La forma del agua",
      "year": 2022,
      "genre": ["Sci-Fi", "Adventure"],
      "last_notified": "2026-03-07T00:00:00",
      "added_at": "2026-03-01T12:30:00"
    }
  },
  "actors": {
    "67890": {  // TMDB Actor ID
      "name": "Leonardo DiCaprio",
      "last_notified": "2026-03-07T00:00:00"
    }
  },
  "notification_history": [...]  // Para evitar duplicados
}
```

---

## Flujo de Desarrollo 📋

### 1. Hacer cambios
- Modifica archivos en `backend/` (lógica) o `tests/` (tests)
- Los tests deben pasar ANTES de hacer commit

### 2. Ejecutar tests
```bash
pytest tests/ -v
```

### 3. Verificar cobertura
```bash
pytest --cov=backend tests/
```

### 4. Testing manual del bot
```bash
python bot.py
# Enviar mensajes en Telegram al bot
```

### 5. Commit y push
```bash
git add .
git commit -m "feat/fix: descripción breve"
git push origin main
```

---

## Variables de Entorno 🔐

**Requeridas:**
- `TELEGRAM_BOT_TOKEN` - Token del bot (de BotFather)
- `TMDB_API_KEY` - API key de TMDb
- `TELEGRAM_USER_ID` - Tu ID en Telegram

**Opcionales:**
- `CLAUDE_API_KEY` - Para activar integración IA

**Desarrollo:**
```bash
cp .env.example .env
# Editar con valores TEST (no secrets reales)
```

Ver `SECURITY.md` para mejores prácticas.

---

## Decisiones Arquitectónicas 🎯

### Async/Await en todo
- `bot.py` usa `python-telegram-bot` con Application (async)
- Los handlers son async functions
- APScheduler corre con AsyncIOScheduler

### JSON en lugar de base de datos
- Simplicidad para proyecto inicial
- Escalable hasta ~10k películas
- Migración a SQLite posible en futuro

### Modularización por responsabilidad
- Cada módulo tiene UN propósito claro
- TMDbClient solo habla con API
- Storage solo maneja persistencia
- Handlers solo ejecutan lógica

### Sanitización de logs obligatoria
- Todas las claves sensibles pasan por SecurityManager
- Los logs nunca exponen tokens/API keys
- Importante para debugging en producción

---

## Patrones Comunes 🔄

### Agregar un nuevo comando
1. Crear método en `CommandHandler` (backend/handlers.py)
2. Crear test en `tests/test_handlers.py`
3. Registrar en `bot.py` con `CommandHandler`
4. Documentar en README.md

### Agregar nueva búsqueda en TMDb
1. Implementar en `TMDbClient` (backend/tmdb_client.py)
2. Crear test en `tests/test_tmdb_client.py`
3. Usar desde `CommandHandler`

### Agregar test
```bash
pytest tests/test_nombre.py::test_funcion -v
```

---

## Debugging 🐛

### Ver logs
- Los logs salen en stdout durante ejecución
- Logs sanitizados: claves reales → `***REDACTED***`
- Nivel DEBUG por defecto en `logging.basicConfig(level=logging.DEBUG)`

### Ejecutar test con prints
```bash
pytest tests/test_file.py -v -s
```

### Chequear qué se almacena
```bash
cat data/movies.json | python -m json.tool
```

### Probar TMDb connection
```python
from backend.tmdb_client import TMDbClient
client = TMDbClient("TU_API_KEY")
result = client.search_movie("Avatar")
print(result)
```

---

## Dependencias Principales 📦

| Librería | Uso |
|----------|-----|
| `python-telegram-bot` | API de Telegram (async) |
| `requests` | HTTP requests |
| `apscheduler` | Tareas programadas (scheduler) |
| `python-dotenv` | Variables de entorno |
| `pytest` | Tests |
| `pytest-cov` | Cobertura de tests |
| `cryptography` | Para encripción futura |

---

## Consideraciones de Seguridad 🔒

- **Nunca commitear .env** (está en .gitignore)
- **Rotar keys regularmente** - Ver SECURITY.md
- **Logs sanitizados** - APIkeys nunca en output
- **Headers seguros** - API keys en Authorization, no en URL
- **Timeouts en requests** - Prevenir cuelgues

---

## Roadmap 🗺️

- [ ] Integración Claude API (procesamiento IA)
- [ ] Soporte más países
- [ ] Base de datos SQLite
- [ ] Desplegar en servidor (VPS/Railway)
- [ ] Notificaciones con imágenes (pósters)
- [ ] Filtros por género

---
