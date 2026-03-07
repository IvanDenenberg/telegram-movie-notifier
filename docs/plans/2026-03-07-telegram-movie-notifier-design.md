# Diseño: Agente de Notificaciones de Estrenos - Telegram Bot

## Visión General
Bot de Telegram que notifica estrenos de películas y series en Argentina. Permite agregar títulos manualmente o monitorear actores/directores. Diseñado para ser simple, gratuito y preparado para integración de IA en el futuro.

## Requisitos
- **Notificaciones:** Estrenos en cines argentinos
- **Frecuencia:** Chequeos semanales
- **Entrada:** Comandos simples vía Telegram + futura capacidad conversacional
- **Almacenamiento:** JSON ligero (sin BD)
- **Costo:** Máximo gratuito
- **Ejecución:** Local (migración a servidor después)

## Arquitectura

```
┌─────────────────┐
│  Telegram Bot   │ ← Usuario escribe comandos
└────────┬────────┘
         │
    ┌────▼──────┐
    │  Parser   │ ← Detecta: comando vs. texto libre
    └────┬──────┘
         │
    ┌────▼──────────────────┐
    │ Modo Comando (ahora)  │
    │ Modo IA (futuro)      │
    └────┬──────────────────┘
         │
    ┌────▼────────────┐
    │  Backend Python │
    │  - notifier.py  │
    │  - storage.py   │
    │  - tmdb_api.py  │
    └────┬────────────┘
         │
         ├─→ TMDb API (chequeos semanales)
         └─→ JSON Storage (películas, actores)
```

## Componentes

### 1. Bot Telegram (`bot.py`)
- Librería: `python-telegram-bot`
- Comandos:
  - `/add "título"` - Agrega película/serie a monitorear
  - `/add_actor "nombre"` - Monitorea todos los estrenos del actor
  - `/list` - Muestra películas/actores monitoreados
  - `/remove "título"` - Elimina de la lista
  - `/help` - Muestra comandos disponibles
- Parser: Detecta comandos vs. texto libre (preparado para IA futura)

### 2. Backend (`backend/`)
- **notifier.py**:
  - APScheduler ejecuta chequeo semanal
  - Consulta TMDb por estrenos
  - Compara con lista monitoreada
  - Envía notificaciones

- **storage.py**:
  - Lee/escribe `data/movies.json`
  - Estructura: `{movies: [], actors: [], notified: []}`

- **tmdb_client.py**:
  - Wrapper de API TMDb
  - Métodos: `search_movie()`, `get_actor_id()`, `get_upcoming_releases()`

### 3. Storage (`data/movies.json`)
```json
{
  "movies": [
    {"title": "Dune", "id": 438632, "added_date": "2026-03-07"}
  ],
  "actors": [
    {"name": "Tom Cruise", "id": 500, "added_date": "2026-03-07"}
  ],
  "notified": ["dune-2024", "top-gun-2025"]
}
```

### 4. Capa IA (Preparada, no activa)
```python
class AIProcessor:
    def process(self, message: str) -> Optional[str]:
        # Ahora: retorna None (modo desactivado)
        # Futuro: integrar Claude API o modelo local
        pass
```

## Flujo de Notificación

1. **APScheduler** dispara cada 7 días
2. **notifier.py** obtiene lista de actores/películas
3. Consulta TMDb: `https://api.themoviedb.org/3/search/movie?query=title`
4. Filtra por fecha de estreno en Argentina
5. Compara con `notified[]` en JSON
6. Si hay nuevos: genera mensaje y envía vía Telegram
7. Actualiza `notified[]`

## Flujo de Usuario

### Ejemplo 1: Agregar película
```
Usuario: /add "Oppenheimer"
Bot: ✓ "Oppenheimer" agregada a tu lista
Bot: (notificará cuando estrene)
```

### Ejemplo 2: Monitorear actor
```
Usuario: /add_actor "Tom Cruise"
Bot: ✓ Monitoreando a "Tom Cruise"
Bot: (te notificaré de sus estrenos)
```

### Ejemplo 3: Futura IA (plantilla)
```
Usuario: "Quiero ver películas de Spielberg"
Parser: Detecta texto libre → envía a AIProcessor
AI: Interpreta → "/add_director Spielberg"
Bot: Ejecuta comando
Bot: ✓ Monitoreando a "Steven Spielberg"
```

## Tecnologías

- **Lenguaje:** Python 3.9+
- **Bot:** `python-telegram-bot` v20+
- **Scheduler:** `apscheduler` v3+
- **HTTP:** `requests`
- **API:** TMDb (gratuita, 1000 req/día)
- **Storage:** JSON vanilla (sin dependencias extra)
- **Futuro IA:** Claude API o modelo local (Mistral, Phi)

## Dependencias (Gratuitas)

- `python-telegram-bot` - Bot de Telegram
- `requests` - HTTP client
- `apscheduler` - Task scheduling
- `python-dotenv` - Variables de entorno

**Costo mensual:** $0 (TMDb y Telegram son gratuitas)

## Estructura de Carpetas

```
movies_series_notifier/
├── bot.py              # Punto de entrada
├── backend/
│   ├── notifier.py
│   ├── storage.py
│   └── tmdb_client.py
├── data/
│   └── movies.json
├── docs/
│   └── plans/
│       └── 2026-03-07-telegram-movie-notifier-design.md
├── requirements.txt
├── .env.example
└── .gitignore
```

## Preparación para IA Futura

El diseño incluye:
1. **Parser agnóstico:** Detecta comando vs. texto libre
2. **Capa AIProcessor:** Abstracta, lista para integración
3. **Separación de concerns:** Procesamiento de lenguaje ≠ ejecución

Cuando se integre IA:
- Solo activa `AIProcessor.process()`
- No requiere cambios en resto del código
- Compatible con Claude API o modelos locales

## Consideraciones

- **Filtrado geográfico:** TMDb requiere chequeo manual de "released in Argentina"
- **Límites API:** 1000 req/día de TMDb (suficiente para 1-2 chequeos semanales)
- **Persistencia:** JSON es suficiente ahora; DB SQL si crece a servidor
- **Timezone:** Usar UTC; usuario puede ajustar horario de notificación

## Aprobación

- [x] Arquitectura revisada
- [x] Flujo de usuario validado
- [x] Preparado para IA futura
- [x] Costos confirmados: $0

