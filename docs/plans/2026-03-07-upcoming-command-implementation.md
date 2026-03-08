# Comando /upcoming - Plan de Implementación

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Implementar comando `/upcoming` que muestra películas, series y actores con estrenos en los próximos 60 días.

**Architecture:** Agregar método helper en Notifier para lógica de rango de fechas, luego agregar handler en CommandHandler que utiliza ese método. Integrar en bot.py como nuevo comando.

**Tech Stack:** Python 3.9+, datetime para cálculos, TMDb API (existente), HTML formatting (como otros comandos).

---

## Task 1: Agregar tests para `get_releases_in_range()` en notifier.py

**Files:**
- Modify: `tests/test_notifier.py`

**Step 1: Agregar tests para get_releases_in_range**

Agregar al final de `tests/test_notifier.py`:

```python
@patch('backend.notifier.TMDbClient')
@patch('backend.notifier.Storage')
def test_get_releases_in_range_60_days(mock_storage, mock_tmdb):
    """Test obtener releases en rango de 60 días"""
    from datetime import datetime, timedelta

    mock_storage_instance = MagicMock()
    mock_storage.return_value = mock_storage_instance
    mock_storage_instance.get_movies.return_value = [
        {"id": 1, "title": "Movie1"}
    ]
    mock_storage_instance.get_actors.return_value = [
        {"id": 500, "name": "Actor1"}
    ]

    mock_tmdb_instance = MagicMock()
    mock_tmdb.return_value = mock_tmdb_instance
    mock_tmdb_instance.search_movie.return_value = {
        "id": 1,
        "title": "Movie1",
        "release_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    }
    mock_tmdb_instance.get_actor_filmography.return_value = []
    mock_tmdb_instance.get_actor_tv_credits.return_value = []

    notifier = Notifier("fake_key", "fake_storage.json")
    releases = notifier.get_releases_in_range(60)

    assert "movies" in releases
    assert len(releases["movies"]) > 0


@patch('backend.notifier.TMDbClient')
@patch('backend.notifier.Storage')
def test_get_releases_in_range_empty(mock_storage, mock_tmdb):
    """Test cuando no hay releases en rango"""
    mock_storage_instance = MagicMock()
    mock_storage.return_value = mock_storage_instance
    mock_storage_instance.get_movies.return_value = []
    mock_storage_instance.get_actors.return_value = []

    mock_tmdb_instance = MagicMock()
    mock_tmdb.return_value = mock_tmdb_instance

    notifier = Notifier("fake_key", "fake_storage.json")
    releases = notifier.get_releases_in_range(60)

    assert releases["movies"] == []
    assert releases["series"] == []
    assert releases["actors"] == []


@patch('backend.notifier.TMDbClient')
@patch('backend.notifier.Storage')
def test_get_releases_in_range_filter_movies(mock_storage, mock_tmdb):
    """Test filtro de solo películas"""
    from datetime import datetime, timedelta

    mock_storage_instance = MagicMock()
    mock_storage.return_value = mock_storage_instance
    mock_storage_instance.get_movies.return_value = [
        {"id": 1, "title": "Movie1"}
    ]
    mock_storage_instance.get_actors.return_value = [
        {"id": 500, "name": "Actor1"}
    ]

    mock_tmdb_instance = MagicMock()
    mock_tmdb.return_value = mock_tmdb_instance
    mock_tmdb_instance.search_movie.return_value = {
        "id": 1,
        "title": "Movie1",
        "release_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    }

    notifier = Notifier("fake_key", "fake_storage.json")
    releases = notifier.get_releases_in_range(60, filter_type="movies")

    assert "movies" in releases
    assert releases["movies"]  # No vacío
    assert releases.get("series", []) == []
```

**Step 2: Ejecutar tests (deben fallar)**

```bash
cd /home/ivan/projects/movies_series_notifier
source venv/bin/activate
pytest tests/test_notifier.py::test_get_releases_in_range_60_days -v
```

Expected: FAIL - `AttributeError: 'Notifier' object has no attribute 'get_releases_in_range'`

**Step 3: Implementar `get_releases_in_range()` en notifier.py**

Agregar al final de la clase `Notifier` en `backend/notifier.py`:

```python
from datetime import datetime, timedelta

def get_releases_in_range(self, days: int = 60, filter_type: str = "all") -> Dict[str, List]:
    """
    Get releases for movies/actors within N days, grouped by type.

    Args:
        days: Number of days to look ahead (default 60)
        filter_type: "all", "movies", "series", or "actors"

    Returns:
        Dict with keys: "movies", "series", "actors", each containing list of releases
    """
    result = {"movies": [], "series": [], "actors": []}

    today = datetime.now().date()
    end_date = today + timedelta(days=days)

    # Process movies
    if filter_type in ["all", "movies"]:
        for movie in self.storage.get_movies():
            movie_data = self.tmdb.search_movie(movie["title"])
            if movie_data and movie_data.get("release_date"):
                release_date = datetime.strptime(
                    movie_data["release_date"], "%Y-%m-%d"
                ).date()
                if today <= release_date <= end_date:
                    result["movies"].append({
                        "title": movie_data.get("title", movie["title"]),
                        "release_date": movie_data["release_date"],
                        "type": "movie"
                    })

    # Process actors
    if filter_type in ["all", "movies", "series", "actors"]:
        for actor in self.storage.get_actors():
            # Get filmography (movies)
            if filter_type in ["all", "movies", "actors"]:
                filmography = self.tmdb.get_actor_filmography(actor["id"])
                for movie in filmography:
                    if movie.get("release_date"):
                        release_date = datetime.strptime(
                            movie["release_date"], "%Y-%m-%d"
                        ).date()
                        if today <= release_date <= end_date:
                            result["movies"].append({
                                "title": movie.get("title", "Unknown"),
                                "release_date": movie["release_date"],
                                "type": "movie",
                                "actor": actor["name"]
                            })

            # Get TV credits (series)
            if filter_type in ["all", "series", "actors"]:
                tv_credits = self.tmdb.get_actor_tv_credits(actor["id"])
                for show in tv_credits:
                    if show.get("first_air_date"):
                        release_date = datetime.strptime(
                            show["first_air_date"], "%Y-%m-%d"
                        ).date()
                        if today <= release_date <= end_date:
                            result["series"].append({
                                "title": show.get("name", "Unknown"),
                                "release_date": show["first_air_date"],
                                "type": "tv",
                                "actor": actor["name"]
                            })

    # Sort each list by release_date
    for key in result:
        result[key].sort(key=lambda x: x["release_date"])

    return result
```

**Step 4: Ejecutar tests (deben pasar)**

```bash
cd /home/ivan/projects/movies_series_notifier
source venv/bin/activate
pytest tests/test_notifier.py::test_get_releases_in_range_60_days -v
pytest tests/test_notifier.py::test_get_releases_in_range_empty -v
pytest tests/test_notifier.py::test_get_releases_in_range_filter_movies -v
```

Expected: PASS (3/3)

**Step 5: Commit**

```bash
cd /home/ivan/projects/movies_series_notifier
git add backend/notifier.py tests/test_notifier.py
git commit -m "feat: add get_releases_in_range method to Notifier"
```

---

## Task 2: Agregar tests para `handle_upcoming()` en handlers.py

**Files:**
- Modify: `tests/test_handlers.py`

**Step 1: Agregar tests para handle_upcoming**

Agregar al final de `tests/test_handlers.py`:

```python
@patch('backend.handlers.Storage')
@patch('backend.handlers.TMDbClient')
def test_handle_upcoming_all(mock_tmdb, mock_storage):
    """Test /upcoming sin filtro muestra todo"""
    from datetime import datetime, timedelta

    mock_storage_instance = MagicMock()
    mock_storage.return_value = mock_storage_instance
    mock_storage_instance.get_movies.return_value = [
        {"id": 1, "title": "Movie1"}
    ]
    mock_storage_instance.get_actors.return_value = []

    mock_tmdb_instance = MagicMock()
    mock_tmdb.return_value = mock_tmdb_instance
    mock_tmdb_instance.search_movie.return_value = {
        "id": 1,
        "title": "Movie1",
        "release_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    }

    handler = CommandHandler("fake_key", "fake_storage.json")
    response = handler.handle_upcoming([])

    assert "🎬" in response or "Movie1" in response
    assert "película" in response.lower() or "películas" in response.lower()


@patch('backend.handlers.Storage')
@patch('backend.handlers.TMDbClient')
def test_handle_upcoming_empty(mock_tmdb, mock_storage):
    """Test /upcoming sin resultados"""
    mock_storage_instance = MagicMock()
    mock_storage.return_value = mock_storage_instance
    mock_storage_instance.get_movies.return_value = []
    mock_storage_instance.get_actors.return_value = []

    mock_tmdb_instance = MagicMock()
    mock_tmdb.return_value = mock_tmdb_instance

    handler = CommandHandler("fake_key", "fake_storage.json")
    response = handler.handle_upcoming([])

    assert "No hay estrenos" in response or "próximos 60 días" in response


@patch('backend.handlers.Storage')
@patch('backend.handlers.TMDbClient')
def test_handle_upcoming_filter_movies(mock_tmdb, mock_storage):
    """Test /upcoming movies filtra solo películas"""
    from datetime import datetime, timedelta

    mock_storage_instance = MagicMock()
    mock_storage.return_value = mock_storage_instance
    mock_storage_instance.get_movies.return_value = [
        {"id": 1, "title": "Movie1"}
    ]
    mock_storage_instance.get_actors.return_value = [
        {"id": 500, "name": "Actor1"}
    ]

    mock_tmdb_instance = MagicMock()
    mock_tmdb.return_value = mock_tmdb_instance
    mock_tmdb_instance.search_movie.return_value = {
        "id": 1,
        "title": "Movie1",
        "release_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    }
    mock_tmdb_instance.get_actor_filmography.return_value = []
    mock_tmdb_instance.get_actor_tv_credits.return_value = []

    handler = CommandHandler("fake_key", "fake_storage.json")
    response = handler.handle_upcoming(["movies"])

    assert "Movie1" in response or "película" in response.lower()
```

**Step 2: Ejecutar tests (deben fallar)**

```bash
cd /home/ivan/projects/movies_series_notifier
source venv/bin/activate
pytest tests/test_handlers.py::test_handle_upcoming_all -v
```

Expected: FAIL - `AttributeError: 'CommandHandler' object has no attribute 'handle_upcoming'`

**Step 3: Implementar `handle_upcoming()` en handlers.py**

Agregar al final de la clase `CommandHandler` en `backend/handlers.py`:

```python
def handle_upcoming(self, args: List[str]) -> str:
    """Handle /upcoming command with optional filter (movies, series, actors)"""
    # Determine filter
    filter_type = "all"
    if args and len(args) > 0:
        filter_arg = args[0].lower()
        if filter_arg in ["movies", "series", "actors"]:
            filter_type = filter_arg

    # Get releases in range
    releases = self.storage._read()  # Get all data for notifier compatibility
    notifier = Notifier(self.tmdb.api_key, self.storage.path)
    releases_by_type = notifier.get_releases_in_range(days=60, filter_type=filter_type)

    # Check if there are any results
    total_releases = sum(len(v) for v in releases_by_type.values())
    if total_releases == 0:
        return "No hay estrenos en los próximos 60 días"

    # Format response
    response = ""

    if filter_type in ["all", "movies"] and releases_by_type["movies"]:
        response += "<b>🎬 Películas (próximos 60 días):</b>\n"
        for release in releases_by_type["movies"]:
            response += f"  • {release['title']} - {release['release_date']}\n"
        response += "\n"

    if filter_type in ["all", "series"] and releases_by_type["series"]:
        response += "<b>📺 Series (próximos 60 días):</b>\n"
        for release in releases_by_type["series"]:
            response += f"  • {release['title']} - {release['release_date']}\n"
        response += "\n"

    if filter_type == "all" and releases_by_type["actors"]:
        response += "<b>👤 Actores (próximos 60 días):</b>\n"
        for release in releases_by_type["actors"]:
            actor_name = release.get("actor", "Unknown")
            response += f"  • {actor_name} - {release['title']} ({release['release_date']})\n"
        response += "\n"

    return response.rstrip()
```

**Step 4: Ejecutar tests (deben pasar)**

```bash
cd /home/ivan/projects/movies_series_notifier
source venv/bin/activate
pytest tests/test_handlers.py::test_handle_upcoming_all -v
pytest tests/test_handlers.py::test_handle_upcoming_empty -v
pytest tests/test_handlers.py::test_handle_upcoming_filter_movies -v
```

Expected: PASS (3/3)

**Step 5: Commit**

```bash
cd /home/ivan/projects/movies_series_notifier
git add backend/handlers.py tests/test_handlers.py
git commit -m "feat: add handle_upcoming command handler"
```

---

## Task 3: Registrar comando `/upcoming` en bot.py

**Files:**
- Modify: `bot.py:180-190`

**Step 1: Agregar handler de comando en setup_handlers()**

En `bot.py`, buscar el método `setup_handlers()` (alrededor de línea 174) y agregar después de la línea para `/help`:

```python
# Handler para /upcoming
self.app.add_handler(CommandHandler("upcoming", self._command_wrapper("upcoming")))
```

La sección debe quedar:

```python
# Handlers para comandos de control
self.app.add_handler(CommandHandler("add", self._command_wrapper("add")))
self.app.add_handler(CommandHandler("add_actor", self._command_wrapper("add_actor")))
self.app.add_handler(CommandHandler("list", self._command_wrapper("list")))
self.app.add_handler(CommandHandler("remove", self._command_wrapper("remove")))
self.app.add_handler(CommandHandler("help", self._command_wrapper("help")))
self.app.add_handler(CommandHandler("upcoming", self._command_wrapper("upcoming")))
```

**Step 2: Agregar case en _handle_command()**

En `bot.py`, buscar el método `_handle_command()` (alrededor de línea 101) y agregar después del caso `help`:

```python
elif command == "upcoming":
    return self.command_handler.handle_upcoming(args)
```

La sección elif debe quedar:

```python
elif command == "add":
    return self.command_handler.handle_add(args)
elif command == "add_actor":
    return self.command_handler.handle_add_actor(args)
elif command == "list":
    return self.command_handler.handle_list(args)
elif command == "remove":
    return self.command_handler.handle_remove(args)
elif command == "help":
    return self.command_handler.handle_help()
elif command == "upcoming":
    return self.command_handler.handle_upcoming(args)
```

**Step 3: Verificar sintaxis**

```bash
python3 -c "
import sys
sys.path.insert(0, '/home/ivan/projects/movies_series_notifier')
with open('bot.py', 'r') as f:
    compile(f.read(), 'bot.py', 'exec')
print('✅ bot.py sin errores de sintaxis')
"
```

Expected: `✅ bot.py sin errores de sintaxis`

**Step 4: Commit**

```bash
cd /home/ivan/projects/movies_series_notifier
git add bot.py
git commit -m "feat: register /upcoming command in bot"
```

---

## Task 4: Ejecutar tests y validar

**Files:**
- Test: `tests/test_handlers.py`
- Test: `tests/test_notifier.py`

**Step 1: Ejecutar todos los tests**

```bash
cd /home/ivan/projects/movies_series_notifier
source venv/bin/activate
pytest tests/ -v --tb=short
```

Expected: Todos pasan (incluyendo los 3 nuevos tests de /upcoming)

**Step 2: Ejecutar tests con cobertura**

```bash
cd /home/ivan/projects/movies_series_notifier
source venv/bin/activate
pytest tests/ --cov=backend --cov-report=term-missing | grep -E "^backend|^TOTAL|^---"
```

Expected: Cobertura >= 85%

**Step 3: Commit final**

```bash
cd /home/ivan/projects/movies_series_notifier
git log --oneline -5
```

Expected: Últimos 3 commits deben ser:
1. `feat: register /upcoming command in bot`
2. `feat: add handle_upcoming command handler`
3. `feat: add get_releases_in_range method to Notifier`

---

## Verificación de Completitud

- ✅ Método `get_releases_in_range()` implementado en Notifier
- ✅ Tests de `get_releases_in_range()` pasando
- ✅ Método `handle_upcoming()` implementado en CommandHandler
- ✅ Tests de `handle_upcoming()` pasando
- ✅ Comando `/upcoming` registrado en bot.py
- ✅ Todos los tests pasan (58+ tests)
- ✅ Cobertura >= 85%
- ✅ 3 commits nuevos

---

Plan complete and saved. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
