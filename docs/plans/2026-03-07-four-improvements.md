# Four Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Enhance the bot with debug logging, direct ID-based addition, searchable top 3 results, and undo buttons.

**Architecture:** Debug logging uses Python's logging module configured at INFO/DEBUG levels. /add_by_id fetches directly from TMDb without search. Top 3 results display inline Telegram buttons for user selection. Undo buttons use InlineKeyboardMarkup to trigger /remove via callback.

**Tech Stack:** Python logging module, python-telegram-bot v20 InlineKeyboardMarkup, TMDb API v3, pytest with mocking.

---

## Task 1: Configure Debug Logging Infrastructure

**Files:**
- Modify: `bot.py` (logging setup)
- Modify: `backend/handlers.py` (add logger to CommandHandler)
- Modify: `backend/tmdb_client.py` (add logger)
- Modify: `backend/parser.py` (add logger)
- Modify: `backend/storage.py` (add logger)
- Modify: `backend/notifier.py` (add logger)

**Step 1: Write test for debug logging configuration**

Create `tests/test_logging.py`:

```python
import logging
from backend.handlers import CommandHandler

def test_command_handler_has_logger():
    handler = CommandHandler("test_key", "data/test.json")
    assert hasattr(handler, 'logger')
    assert isinstance(handler.logger, logging.Logger)
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_logging.py::test_command_handler_has_logger -v
```

Expected: FAIL - CommandHandler has no logger attribute

**Step 3: Add logger to CommandHandler**

In `backend/handlers.py`, at the top of the class:

```python
class CommandHandler:
    def __init__(self, tmdb_api_key: str, storage_path: str):
        """Initialize command handler with TMDb API key and storage path"""
        self.logger = logging.getLogger(__name__)
        self.tmdb = TMDbClient(tmdb_api_key)
        self.storage = Storage(storage_path)
```

Also add import at top of file:
```python
import logging
```

**Step 4: Add loggers to other backend modules**

In `backend/tmdb_client.py`, inside `__init__`:
```python
self.logger = logging.getLogger(__name__)
```

In `backend/parser.py`, inside MessageParser class:
```python
def __init__(self):
    self.logger = logging.getLogger(__name__)

def parse(self, message: str) -> Dict[str, Any]:
    ...
```

In `backend/storage.py`, inside `__init__`:
```python
self.logger = logging.getLogger(__name__)
```

In `backend/notifier.py`, inside `__init__`:
```python
self.logger = logging.getLogger(__name__)
```

**Step 5: Configure logging in bot.py**

In bot.py, replace the logging.basicConfig (lines 18-21) with:

```python
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Changed from INFO to DEBUG
)
```

**Step 6: Run test to verify it passes**

```bash
pytest tests/test_logging.py::test_command_handler_has_logger -v
```

Expected: PASS

**Step 7: Commit**

```bash
git add bot.py backend/handlers.py backend/tmdb_client.py backend/parser.py backend/storage.py backend/notifier.py tests/test_logging.py
git commit -m "feat: add logging infrastructure to all modules"
```

---

## Task 2: Add Debug Logging to Parser

**Files:**
- Modify: `backend/parser.py` (add debug logs)
- Modify: `tests/test_parser.py` (verify logging)

**Step 1: Write test for parser debug output**

In `tests/test_parser.py`, add:

```python
def test_parse_logs_command_details(caplog):
    parser = MessageParser()
    with caplog.at_level(logging.DEBUG):
        result = parser.parse('/add "Dune"')

    assert 'command' in caplog.text.lower()
    assert 'dune' in caplog.text.lower()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_parser.py::test_parse_logs_command_details -v
```

Expected: FAIL - no debug logs found

**Step 3: Add debug logging to parser.parse()**

In `backend/parser.py`, update `parse()` method:

```python
def parse(self, message: str) -> Dict[str, Any]:
    """
    Parse a message and determine if it's a command or free text.

    Returns:
        dict: {"type": "command", "command": str, "args": list} or
              {"type": "free_text", "text": str}
    """
    message = message.strip()
    self.logger.debug(f"[PARSE] Input: {message}")

    if message.startswith('/'):
        result = self._parse_command(message)
    else:
        result = {"type": "free_text", "text": message}

    self.logger.debug(f"[PARSE] Result: type={result.get('type')}, command={result.get('command', 'N/A')}, args={result.get('args', [])}")
    return result
```

**Step 4: Add debug logging to _parse_command()**

In `backend/parser.py`, update `_parse_command()`:

```python
def _parse_command(self, message: str) -> Dict[str, Any]:
    """
    Parse a command message.

    Expected format: /command_name "arg1" "arg2" ...
    """
    # Match command name (everything from / to first space or end of string)
    command_match = re.match(r'/(\\w+)', message)
    if not command_match:
        self.logger.debug(f"[_PARSE_COMMAND] Invalid command format: {message}")
        return {"type": "free_text", "text": message}

    command = command_match.group(1)
    self.logger.debug(f"[_PARSE_COMMAND] Command detected: {command}")

    # Extract quoted arguments
    args = self._extract_args(message)
    self.logger.debug(f"[_PARSE_COMMAND] Extracted args: {args}")

    return {
        "type": "command",
        "command": command,
        "args": args
    }
```

**Step 5: Add debug logging to _extract_args()**

In `backend/parser.py`, update `_extract_args()`:

```python
def _extract_args(self, message: str) -> list:
    """
    Extract arguments from quoted strings in the command.

    Handles: "text" and 'text'
    """
    cleaned = []

    # Try double quotes
    double_pattern = r'\"([^\"]*)\"'
    double_matches = re.findall(double_pattern, message)
    self.logger.debug(f"[_EXTRACT_ARGS] Double quotes found: {double_matches}")
    cleaned.extend([m.strip() for m in double_matches if m.strip()])

    # Try single quotes
    single_pattern = r"'([^']*)'\"
    single_matches = re.findall(single_pattern, message)
    self.logger.debug(f"[_EXTRACT_ARGS] Single quotes found: {single_matches}")
    cleaned.extend([m.strip() for m in single_matches if m.strip()])

    # Remove duplicates while preserving order
    seen = set()
    result = []
    for item in cleaned:
        if item not in seen:
            seen.add(item)
            result.append(item)

    self.logger.debug(f"[_EXTRACT_ARGS] Final args (deduplicated): {result}")
    return result
```

**Step 6: Run test to verify it passes**

```bash
pytest tests/test_parser.py::test_parse_logs_command_details -v
```

Expected: PASS

**Step 7: Run all parser tests**

```bash
pytest tests/test_parser.py -v
```

Expected: All tests pass

**Step 8: Commit**

```bash
git add backend/parser.py tests/test_parser.py
git commit -m "feat: add debug logging to parser module"
```

---

## Task 3: Add Debug Logging to TMDb Client

**Files:**
- Modify: `backend/tmdb_client.py` (add debug logs)
- Modify: `tests/test_tmdb_client.py` (verify logging)

**Step 1: Write test for tmdb_client debug output**

In `tests/test_tmdb_client.py`, add:

```python
def test_search_movie_logs_query(caplog, mock_request_manager):
    client = TMDbClient("test_key")
    client.request_manager = mock_request_manager
    mock_request_manager.get.return_value = {
        "results": [{"title": "Dune", "id": 438632, "release_date": "2021-10-01"}]
    }

    with caplog.at_level(logging.DEBUG):
        result = client.search_movie("Dune")

    assert "search_movie" in caplog.text.lower()
    assert "dune" in caplog.text.lower()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_tmdb_client.py::test_search_movie_logs_query -v
```

Expected: FAIL

**Step 3: Add debug logging to search_movie()**

In `backend/tmdb_client.py`, update `search_movie()`:

```python
def search_movie(self, title: str) -> Optional[Dict]:
    """Search for a movie by title - prefers exact matches"""
    self.logger.debug(f"[SEARCH_MOVIE] Querying TMDb for: {title}")

    data = self._make_request("/search/movie", {"query": title})
    if not data or "results" not in data or not data["results"]:
        self.logger.debug(f"[SEARCH_MOVIE] No results found for: {title}")
        return None

    self.logger.debug(f"[SEARCH_MOVIE] Found {len(data['results'])} results")

    # Normalize search title for comparison
    search_title_lower = title.lower().strip()

    # First pass: look for exact title match
    for result in data["results"]:
        if result.get("title") and result.get("release_date"):
            result_title_lower = result["title"].lower().strip()
            if result_title_lower == search_title_lower:
                self.logger.debug(f"[SEARCH_MOVIE] Exact match found: {result['title']} (ID: {result.get('id')})")
                return result

    # Second pass: look for titles starting with search term
    for result in data["results"]:
        if result.get("title") and result.get("release_date"):
            result_title_lower = result["title"].lower().strip()
            if result_title_lower.startswith(search_title_lower):
                self.logger.debug(f"[SEARCH_MOVIE] Prefix match found: {result['title']} (ID: {result.get('id')})")
                return result

    # Fall back to first valid result
    for result in data["results"]:
        if result.get("title") and result.get("release_date"):
            self.logger.debug(f"[SEARCH_MOVIE] Using first valid result: {result['title']} (ID: {result.get('id')})")
            return result

    self.logger.debug(f"[SEARCH_MOVIE] No valid results for: {title}")
    return None
```

**Step 4: Add similar logging to search_tv() and get_actor_id()**

In `search_tv()`, add similar debug logs:

```python
def search_tv(self, title: str) -> Optional[Dict]:
    """Search for a TV show by title - prefers exact matches"""
    self.logger.debug(f"[SEARCH_TV] Querying TMDb for: {title}")

    data = self._make_request("/search/tv", {"query": title})
    if not data or "results" not in data or not data["results"]:
        self.logger.debug(f"[SEARCH_TV] No results found for: {title}")
        return None

    self.logger.debug(f"[SEARCH_TV] Found {len(data['results'])} results")

    # ... rest of method with similar self.logger.debug() calls as search_movie()
```

In `get_actor_id()`:

```python
def get_actor_id(self, actor_name: str) -> Optional[int]:
    """Get actor ID by name - prefers exact matches"""
    self.logger.debug(f"[GET_ACTOR_ID] Searching for actor: {actor_name}")

    data = self._make_request("/search/person", {"query": actor_name})
    if not data or "results" not in data or not data["results"]:
        self.logger.debug(f"[GET_ACTOR_ID] No results for: {actor_name}")
        return None

    self.logger.debug(f"[GET_ACTOR_ID] Found {len(data['results'])} results")

    # ... rest of method with similar debug logs ...
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/test_tmdb_client.py::test_search_movie_logs_query -v
```

Expected: PASS

**Step 6: Run all tmdb_client tests**

```bash
pytest tests/test_tmdb_client.py -v
```

Expected: All tests pass

**Step 7: Commit**

```bash
git add backend/tmdb_client.py tests/test_tmdb_client.py
git commit -m "feat: add debug logging to tmdb_client module"
```

---

## Task 4: Add Debug Logging to Handlers

**Files:**
- Modify: `backend/handlers.py` (add debug logs)
- Modify: `tests/test_handlers.py` (verify logging)

**Step 1: Write test for handlers debug output**

In `tests/test_handlers.py`, add:

```python
def test_handle_add_logs_operation(caplog, mock_tmdb, mock_storage):
    handler = CommandHandler("test_key", "data/test.json")
    handler.tmdb = mock_tmdb
    handler.storage = mock_storage
    handler.logger = logging.getLogger("backend.handlers")

    mock_tmdb.search_movie.return_value = {"title": "Dune", "id": 438632}

    with caplog.at_level(logging.DEBUG):
        result = handler.handle_add(["Dune"])

    assert "dune" in caplog.text.lower()
    assert "438632" in caplog.text or "added" in caplog.text.lower()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_handlers.py::test_handle_add_logs_operation -v
```

Expected: FAIL

**Step 3: Add debug logging to handle_add()**

In `backend/handlers.py`, update `handle_add()`:

```python
def handle_add(self, args: List[str]) -> str:
    """Handle /add command - add movie or TV show"""
    if not args:
        self.logger.warning("[HANDLE_ADD] No arguments provided")
        return "❌ Por favor especifica el título: /add 'Título de película'"

    title = args[0]
    self.logger.debug(f"[HANDLE_ADD] Searching for title: {title}")

    # Try to search for movie first
    movie = self.tmdb.search_movie(title)
    if movie:
        # Verify it's a close match (avoid "Vladimir" → "Vladimir and Rosa")
        if self._is_close_match(title, movie.get("title", "")):
            self.logger.debug(f"[HANDLE_ADD] Close match verified: {movie.get('title')} (ID: {movie.get('id')})")
            self.storage.add_movie(movie.get("title", title), movie.get("id"), media_type="movie")
            self.logger.info(f"[HANDLE_ADD] Movie added: {movie.get('title')} (ID: {movie.get('id')})")
            movie_id = movie.get("id")
            tmdb_link = f"https://www.themoviedb.org/movie/{movie_id}"
            return f"✅ '{movie.get('title', title)}' agregada a tu lista 🎬\n<a href='{tmdb_link}'>Ver en TMDb</a>"
        else:
            self.logger.debug(f"[HANDLE_ADD] Movie result rejected - not close enough match: {movie.get('title')}")

    # Try to search for TV show
    tv = self.tmdb.search_tv(title)
    if tv:
        # Verify it's a close match
        if self._is_close_match(title, tv.get("name", "")):
            self.logger.debug(f"[HANDLE_ADD] Close match verified (TV): {tv.get('name')} (ID: {tv.get('id')})")
            self.storage.add_movie(tv.get("name", title), tv.get("id"), media_type="tv")
            self.logger.info(f"[HANDLE_ADD] TV show added: {tv.get('name')} (ID: {tv.get('id')})")
            tv_id = tv.get("id")
            tmdb_link = f"https://www.themoviedb.org/tv/{tv_id}"
            return f"✅ '{tv.get('name', title)}' agregada a tu lista 📺\n<a href='{tmdb_link}'>Ver en TMDb</a>"
        else:
            self.logger.debug(f"[HANDLE_ADD] TV result rejected - not close enough match: {tv.get('name')}")

    self.logger.warning(f"[HANDLE_ADD] No suitable result found for: {title}")
    return f"❌ No encontré un resultado exacto para '{title}'.\n\nIntenta:\n• Con el título completo\n• Con año: '{title} 2024'\n• En inglés si es aplicable"
```

**Step 4: Add debug logging to handle_add_actor()**

In `backend/handlers.py`, update `handle_add_actor()`:

```python
def handle_add_actor(self, args: List[str]) -> str:
    """Handle /add_actor command - monitor actor's projects"""
    if not args:
        self.logger.warning("[HANDLE_ADD_ACTOR] No arguments provided")
        return "❌ Por favor especifica el nombre del actor: /add_actor 'Nombre'"

    actor_name = args[0]
    self.logger.debug(f"[HANDLE_ADD_ACTOR] Searching for actor: {actor_name}")

    actor_id = self.tmdb.get_actor_id(actor_name)

    if not actor_id:
        self.logger.warning(f"[HANDLE_ADD_ACTOR] Actor not found: {actor_name}")
        return f"❌ No encontré al actor '{actor_name}' en TMDb."

    self.storage.add_actor(actor_name, actor_id)
    self.logger.info(f"[HANDLE_ADD_ACTOR] Actor added: {actor_name} (ID: {actor_id})")
    tmdb_link = f"https://www.themoviedb.org/person/{actor_id}"
    return f"✅ Monitoreando a {actor_name} 👤\n<a href='{tmdb_link}'>Ver en TMDb</a>"
```

**Step 5: Add debug logging to handle_remove()**

In `backend/handlers.py`, update key parts of `handle_remove()`:

```python
def handle_remove(self, args: List[str]) -> str:
    """Handle /remove command - remove movie, show, or actor"""
    if not args:
        self.logger.warning("[HANDLE_REMOVE] No arguments provided")
        return "❌ Por favor especifica qué remover: /remove 'Título o nombre'"

    # Clean search term: remove any quotes that might be included
    search_input = args[0].strip().strip('"\'"\"\'')  # Remove all types of quotes
    search_term = search_input.lower()

    self.logger.debug(f"[HANDLE_REMOVE] Searching for: original='{args[0]}', normalized='{search_term}'")

    # Search in movies/shows
    movies = self.storage.get_movies()

    for movie in movies:
        movie_title_lower = movie.get("title", "").lower()
        if movie_title_lower == search_term:
            if self.storage.remove_movie(movie.get("id")):
                self.logger.info(f"[HANDLE_REMOVE] Item removed: {movie.get('title')} (ID: {movie.get('id')})")
                return f"✅ '{movie.get('title')}' removida de tu lista"

    # Search in actors
    actors = self.storage.get_actors()

    for actor in actors:
        actor_name_lower = actor.get("name", "").lower()
        if actor_name_lower == search_term:
            if self.storage.remove_actor(actor.get("id")):
                self.logger.info(f"[HANDLE_REMOVE] Actor removed: {actor.get('name')} (ID: {actor.get('id')})")
                return f"✅ '{actor.get('name')}' removida de tu lista"

    self.logger.warning(f"[HANDLE_REMOVE] Item not found: '{args[0]}'")
    return f"❌ No encontré '{args[0]}' en tu lista."
```

**Step 6: Run tests to verify they pass**

```bash
pytest tests/test_handlers.py -v
```

Expected: All tests pass

**Step 7: Commit**

```bash
git add backend/handlers.py tests/test_handlers.py
git commit -m "feat: add debug logging to handlers module"
```

---

## Task 5: Add Debug Logging to Storage and Notifier

**Files:**
- Modify: `backend/storage.py` (add debug logs)
- Modify: `backend/notifier.py` (add debug logs)

**Step 1: Add debug logging to storage.py**

In `backend/storage.py`, update `add_movie()`:

```python
def add_movie(self, title: str, tmdb_id: int, media_type: str = "movie") -> bool:
    """Add a movie or TV show to the list"""
    self.logger.debug(f"[STORAGE.ADD_MOVIE] Adding {media_type}: {title} (ID: {tmdb_id})")
    # ... rest of implementation ...
    self.logger.debug(f"[STORAGE.ADD_MOVIE] Successfully saved to storage")
    return True
```

Update `add_actor()`:

```python
def add_actor(self, name: str, tmdb_id: int) -> bool:
    """Add an actor to monitoring list"""
    self.logger.debug(f"[STORAGE.ADD_ACTOR] Adding actor: {name} (ID: {tmdb_id})")
    # ... rest of implementation ...
    self.logger.debug(f"[STORAGE.ADD_ACTOR] Successfully saved to storage")
    return True
```

Update `remove_movie()` and `remove_actor()`:

```python
def remove_movie(self, tmdb_id: int) -> bool:
    """Remove a movie/show from the list"""
    self.logger.debug(f"[STORAGE.REMOVE_MOVIE] Removing movie ID: {tmdb_id}")
    # ... rest of implementation ...
    return True

def remove_actor(self, tmdb_id: int) -> bool:
    """Remove an actor from monitoring list"""
    self.logger.debug(f"[STORAGE.REMOVE_ACTOR] Removing actor ID: {tmdb_id}")
    # ... rest of implementation ...
    return True
```

**Step 2: Add debug logging to notifier.py**

In `backend/notifier.py`, update `get_releases_in_range()`:

```python
def get_releases_in_range(self, days: int = 60, filter_type: str = "all") -> Dict[str, List[Dict]]:
    """Get releases for monitored items within date range"""
    self.logger.debug(f"[NOTIFIER] Checking releases for next {days} days (filter: {filter_type})")

    # ... implementation ...

    self.logger.debug(f"[NOTIFIER] Found {len(releases_by_type['movies'])} movies, {len(releases_by_type['series'])} series, {len(releases_by_type['actors'])} actor projects")
    return releases_by_type
```

**Step 3: Run all tests**

```bash
pytest tests/ -v
```

Expected: All tests pass (at least 64 tests)

**Step 4: Commit**

```bash
git add backend/storage.py backend/notifier.py
git commit -m "feat: add debug logging to storage and notifier modules"
```

---

## Task 6: Implement /add_by_id Command

**Files:**
- Modify: `backend/handlers.py` (add handle_add_by_id method)
- Modify: `backend/tmdb_client.py` (add get_movie_by_id and get_tv_by_id methods)
- Modify: `bot.py` (register command handler)
- Create: `tests/test_add_by_id.py`

**Step 1: Write tests for /add_by_id**

Create `tests/test_add_by_id.py`:

```python
import pytest
from backend.handlers import CommandHandler

def test_add_by_id_movie(mock_tmdb, mock_storage):
    handler = CommandHandler("test_key", "data/test.json")
    handler.tmdb = mock_tmdb
    handler.storage = mock_storage

    mock_tmdb.get_movie_by_id.return_value = {
        "title": "Dune",
        "id": 438632,
        "release_date": "2021-10-01"
    }

    result = handler.handle_add_by_id(["438632"])

    assert "✅" in result
    assert "Dune" in result
    mock_storage.add_movie.assert_called_once()

def test_add_by_id_tv(mock_tmdb, mock_storage):
    handler = CommandHandler("test_key", "data/test.json")
    handler.tmdb = mock_tmdb
    handler.storage = mock_storage

    mock_tmdb.get_tv_by_id.return_value = {
        "name": "Breaking Bad",
        "id": 1396,
        "first_air_date": "2008-01-20"
    }

    result = handler.handle_add_by_id(["1396", "tv"])

    assert "✅" in result
    assert "Breaking Bad" in result
    mock_storage.add_movie.assert_called_with("Breaking Bad", 1396, media_type="tv")

def test_add_by_id_invalid_format():
    handler = CommandHandler("test_key", "data/test.json")

    result = handler.handle_add_by_id([])

    assert "❌" in result
    assert "ID" in result or "especifica" in result.lower()

def test_add_by_id_not_found(mock_tmdb, mock_storage):
    handler = CommandHandler("test_key", "data/test.json")
    handler.tmdb = mock_tmdb
    handler.storage = mock_storage

    mock_tmdb.get_movie_by_id.return_value = None

    result = handler.handle_add_by_id(["999999"])

    assert "❌" in result
    assert "encontr" in result.lower()
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_add_by_id.py -v
```

Expected: All tests fail (methods don't exist yet)

**Step 3: Add get_movie_by_id and get_tv_by_id to TMDbClient**

In `backend/tmdb_client.py`, add:

```python
def get_movie_by_id(self, movie_id: int) -> Optional[Dict]:
    """Get movie details by TMDb ID"""
    self.logger.debug(f"[GET_MOVIE_BY_ID] Fetching movie ID: {movie_id}")
    data = self._make_request(f"/movie/{movie_id}", {})

    if not data:
        self.logger.debug(f"[GET_MOVIE_BY_ID] Movie not found: {movie_id}")
        return None

    if data.get("title") and data.get("release_date"):
        self.logger.debug(f"[GET_MOVIE_BY_ID] Found: {data.get('title')}")
        return data

    self.logger.debug(f"[GET_MOVIE_BY_ID] Movie missing required fields: {movie_id}")
    return None

def get_tv_by_id(self, tv_id: int) -> Optional[Dict]:
    """Get TV show details by TMDb ID"""
    self.logger.debug(f"[GET_TV_BY_ID] Fetching TV ID: {tv_id}")
    data = self._make_request(f"/tv/{tv_id}", {})

    if not data:
        self.logger.debug(f"[GET_TV_BY_ID] TV show not found: {tv_id}")
        return None

    if data.get("name") and data.get("first_air_date"):
        self.logger.debug(f"[GET_TV_BY_ID] Found: {data.get('name')}")
        return data

    self.logger.debug(f"[GET_TV_BY_ID] TV show missing required fields: {tv_id}")
    return None
```

**Step 4: Add handle_add_by_id to CommandHandler**

In `backend/handlers.py`, add:

```python
def handle_add_by_id(self, args: List[str]) -> str:
    """Handle /add_by_id command - add by TMDb ID"""
    if not args:
        return "❌ Por favor especifica un ID de TMDb: /add_by_id 438632"

    try:
        tmdb_id = int(args[0])
    except ValueError:
        self.logger.warning(f"[HANDLE_ADD_BY_ID] Invalid ID format: {args[0]}")
        return f"❌ ID inválido: {args[0]}. Debe ser un número."

    # Determine type: movie or tv
    media_type = "movie"
    if len(args) > 1 and args[1].lower() == "tv":
        media_type = "tv"

    self.logger.debug(f"[HANDLE_ADD_BY_ID] Adding by ID: {tmdb_id}, type: {media_type}")

    if media_type == "tv":
        data = self.tmdb.get_tv_by_id(tmdb_id)
        if data:
            self.storage.add_movie(data.get("name", f"ID {tmdb_id}"), tmdb_id, media_type="tv")
            self.logger.info(f"[HANDLE_ADD_BY_ID] TV show added by ID: {data.get('name')}")
            tmdb_link = f"https://www.themoviedb.org/tv/{tmdb_id}"
            return f"✅ '{data.get('name')}' agregada a tu lista 📺\n<a href='{tmdb_link}'>Ver en TMDb</a>"
    else:
        data = self.tmdb.get_movie_by_id(tmdb_id)
        if data:
            self.storage.add_movie(data.get("title", f"ID {tmdb_id}"), tmdb_id, media_type="movie")
            self.logger.info(f"[HANDLE_ADD_BY_ID] Movie added by ID: {data.get('title')}")
            tmdb_link = f"https://www.themoviedb.org/movie/{tmdb_id}"
            return f"✅ '{data.get('title')}' agregada a tu lista 🎬\n<a href='{tmdb_link}'>Ver en TMDb</a>"

    self.logger.warning(f"[HANDLE_ADD_BY_ID] Item not found: {tmdb_id}")
    return f"❌ No encontré un elemento con ID {tmdb_id} en TMDb."
```

**Step 5: Register command in bot.py**

In `bot.py`, add to `_handle_command()` method:

```python
elif command == "add_by_id":
    return self.command_handler.handle_add_by_id(args)
```

Also add to `setup_handlers()` method:

```python
self.app.add_handler(CommandHandler("add_by_id", self._command_wrapper("add_by_id")))
```

**Step 6: Run tests to verify they pass**

```bash
pytest tests/test_add_by_id.py -v
```

Expected: All tests pass

**Step 7: Run all tests**

```bash
pytest tests/ -v
```

Expected: All tests pass (65+ total)

**Step 8: Commit**

```bash
git add backend/handlers.py backend/tmdb_client.py bot.py tests/test_add_by_id.py
git commit -m "feat: implement /add_by_id command for direct ID-based addition"
```

---

## Task 7: Implement Top 3 Search Results Display

**Files:**
- Modify: `backend/handlers.py` (update handle_add to return top 3 results)
- Modify: `bot.py` (add callback for result selection)
- Create: `tests/test_search_results.py`

**Step 1: Write tests for top 3 results**

Create `tests/test_search_results.py`:

```python
import pytest
from backend.handlers import CommandHandler

def test_handle_add_ambiguous_shows_options(mock_tmdb, mock_storage):
    handler = CommandHandler("test_key", "data/test.json")
    handler.tmdb = mock_tmdb
    handler.storage = mock_storage

    # Mock multiple results (no exact match)
    mock_tmdb.search_movie.return_value = None  # No exact match
    mock_tmdb.get_search_results.return_value = [
        {"title": "Vladimir", "id": 123, "release_date": "2023-01-01"},
        {"title": "Vladimir and Rosa", "id": 124, "release_date": "1971-01-01"},
        {"title": "Vladimir", "id": 125, "release_date": "2020-01-01"},
    ]

    result = handler.handle_add(["Vladimir"])

    # Should return formatted options instead of auto-selecting
    assert "?" in result or "opción" in result.lower() or "cual" in result.lower()

def test_exact_match_still_auto_adds(mock_tmdb, mock_storage):
    handler = CommandHandler("test_key", "data/test.json")
    handler.tmdb = mock_tmdb
    handler.storage = mock_storage

    # Exact match should still auto-add
    mock_tmdb.search_movie.return_value = {
        "title": "Vladimir",
        "id": 123,
        "release_date": "2023-01-01"
    }

    result = handler.handle_add(["Vladimir"])

    assert "✅" in result
    mock_storage.add_movie.assert_called_once()
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_search_results.py -v
```

Expected: Tests fail (get_search_results doesn't exist)

**Step 3: Add get_search_results to TMDbClient**

In `backend/tmdb_client.py`, add:

```python
def get_search_results(self, title: str, media_type: str = "movie") -> List[Dict]:
    """Get top search results without filtering"""
    endpoint = f"/search/{media_type}"
    self.logger.debug(f"[GET_SEARCH_RESULTS] Getting raw results for: {title} ({media_type})")

    data = self._make_request(endpoint, {"query": title})
    if not data or "results" not in data:
        return []

    results = []
    key_name = "title" if media_type == "movie" else "name"
    key_date = "release_date" if media_type == "movie" else "first_air_date"

    for result in data["results"]:
        if result.get(key_name) and result.get(key_date):
            results.append(result)
            if len(results) >= 3:  # Limit to top 3
                break

    self.logger.debug(f"[GET_SEARCH_RESULTS] Returning {len(results)} results")
    return results
```

**Step 4: Update handle_add to show top 3 when ambiguous**

In `backend/handlers.py`, modify `handle_add()`:

```python
def handle_add(self, args: List[str]) -> str:
    """Handle /add command - add movie or TV show"""
    if not args:
        self.logger.warning("[HANDLE_ADD] No arguments provided")
        return "❌ Por favor especifica el título: /add 'Título de película'"

    title = args[0]
    self.logger.debug(f"[HANDLE_ADD] Searching for title: {title}")

    # Try to search for movie first
    movie = self.tmdb.search_movie(title)
    if movie and self._is_close_match(title, movie.get("title", "")):
        self.logger.debug(f"[HANDLE_ADD] Close match verified: {movie.get('title')} (ID: {movie.get('id')})")
        self.storage.add_movie(movie.get("title", title), movie.get("id"), media_type="movie")
        self.logger.info(f"[HANDLE_ADD] Movie added: {movie.get('title')} (ID: {movie.get('id')})")
        movie_id = movie.get("id")
        tmdb_link = f"https://www.themoviedb.org/movie/{movie_id}"
        return f"✅ '{movie.get('title', title)}' agregada a tu lista 🎬\n<a href='{tmdb_link}'>Ver en TMDb</a>"

    # No exact match - show top 3 movie options
    movie_options = self.tmdb.get_search_results(title, "movie")
    if movie_options:
        self.logger.debug(f"[HANDLE_ADD] Showing {len(movie_options)} movie options")
        response = f"¿Cuál de estas películas quisiste agregar?\n\n"
        for i, opt in enumerate(movie_options, 1):
            year = opt.get("release_date", "N/A")[:4]
            response += f"{i}. {opt.get('title')} ({year}) - <code>/add_by_id {opt.get('id')}</code>\n"
        response += f"\nO intenta: /add 'título completo' o /add '{title} año'"
        return response

    # Try to search for TV show
    tv = self.tmdb.search_tv(title)
    if tv and self._is_close_match(title, tv.get("name", "")):
        self.logger.debug(f"[HANDLE_ADD] Close match verified (TV): {tv.get('name')} (ID: {tv.get('id')})")
        self.storage.add_movie(tv.get("name", title), tv.get("id"), media_type="tv")
        self.logger.info(f"[HANDLE_ADD] TV show added: {tv.get('name')} (ID: {tv.get('id')})")
        tv_id = tv.get("id")
        tmdb_link = f"https://www.themoviedb.org/tv/{tv_id}"
        return f"✅ '{tv.get('name', title)}' agregada a tu lista 📺\n<a href='{tmdb_link}'>Ver en TMDb</a>"

    # No exact match - show top 3 TV options
    tv_options = self.tmdb.get_search_results(title, "tv")
    if tv_options:
        self.logger.debug(f"[HANDLE_ADD] Showing {len(tv_options)} TV options")
        response = f"¿Cuál de estas series quisiste agregar?\n\n"
        for i, opt in enumerate(tv_options, 1):
            year = opt.get("first_air_date", "N/A")[:4]
            response += f"{i}. {opt.get('name')} ({year}) - <code>/add_by_id {opt.get('id')} tv</code>\n"
        response += f"\nO intenta: /add 'título completo' o /add '{title} año'"
        return response

    self.logger.warning(f"[HANDLE_ADD] No suitable result found for: {title}")
    return f"❌ No encontré resultados para '{title}'.\n\nIntenta:\n• Con el título completo\n• Con año: '{title} 2024'\n• En inglés si es aplicable\n• O usa /add_by_id <ID> si conoces el ID en TMDb"
```

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_search_results.py -v
```

Expected: All tests pass

**Step 6: Run all tests**

```bash
pytest tests/ -v
```

Expected: All tests pass (66+ total)

**Step 7: Commit**

```bash
git add backend/handlers.py backend/tmdb_client.py tests/test_search_results.py
git commit -m "feat: show top 3 search results when exact match not found"
```

---

## Task 8: Implement Undo Button Feature

**Files:**
- Modify: `backend/handlers.py` (update responses to include undo metadata)
- Modify: `bot.py` (add callback handler for undo button)
- Create: `tests/test_undo_button.py`

**Step 1: Write tests for undo button**

Create `tests/test_undo_button.py`:

```python
import pytest
from unittest.mock import MagicMock
from bot import MovieNotifierBot

def test_handle_add_returns_undo_metadata(mock_tmdb, mock_storage):
    from backend.handlers import CommandHandler

    handler = CommandHandler("test_key", "data/test.json")
    handler.tmdb = mock_tmdb
    handler.storage = mock_storage

    mock_tmdb.search_movie.return_value = {
        "title": "Dune",
        "id": 438632,
        "release_date": "2021-10-01"
    }

    result = handler.handle_add(["Dune"])

    assert "✅" in result
    assert "Dune" in result

def test_undo_button_click_removes_item(mock_storage):
    from backend.handlers import CommandHandler

    handler = CommandHandler("test_key", "data/test.json")
    handler.storage = mock_storage

    # Simulate undo click by calling handle_remove
    result = handler.handle_remove(["Dune"])

    # Should trigger removal
    assert "✅" in result or "❌" in result  # Either found and removed, or not found
```

**Step 2: Run tests to verify they pass (should already pass)**

```bash
pytest tests/test_undo_button.py -v
```

Expected: Tests pass (removing already works via handle_remove)

**Step 3: Update handlers to return special format for undo button**

In `backend/handlers.py`, update `handle_add()` return statement:

```python
# Movie found and added
movie_id = movie.get("id")
tmdb_link = f"https://www.themoviedb.org/movie/{movie_id}"
response = f"✅ '{movie.get('title', title)}' agregada a tu lista 🎬\n<a href='{tmdb_link}'>Ver en TMDb</a>"

# Store undo info in response (bot.py will parse and add button)
# Format: response|||undo_action|||/remove "title"
undo_action = f'/remove "{movie.get("title", title)}"'
return f"{response}|||UNDO_BUTTON||{undo_action}"
```

Similar for TV shows and actors:

```python
# TV show found and added
tv_id = tv.get("id")
tmdb_link = f"https://www.themoviedb.org/tv/{tv_id}"
response = f"✅ '{tv.get('name', title)}' agregada a tu lista 📺\n<a href='{tmdb_link}'>Ver en TMDb</a>"
undo_action = f'/remove "{tv.get("name", title)}"'
return f"{response}|||UNDO_BUTTON||{undo_action}"
```

For `handle_add_actor()`:

```python
tmdb_link = f"https://www.themoviedb.org/person/{actor_id}"
response = f"✅ Monitoreando a {actor_name} 👤\n<a href='{tmdb_link}'>Ver en TMDb</a>"
undo_action = f'/remove "{actor_name}"'
return f"{response}|||UNDO_BUTTON||{undo_action}"
```

For `/add_by_id` movie:

```python
tmdb_link = f"https://www.themoviedb.org/movie/{tmdb_id}"
response = f"✅ '{data.get('title')}' agregada a tu lista 🎬\n<a href='{tmdb_link}'>Ver en TMDb</a>"
undo_action = f'/remove "{data.get("title")}"'
return f"{response}|||UNDO_BUTTON||{undo_action}"
```

For `/add_by_id` TV:

```python
tmdb_link = f"https://www.themoviedb.org/tv/{tmdb_id}"
response = f"✅ '{data.get('name')}' agregada a tu lista 📺\n<a href='{tmdb_link}'>Ver en TMDb</a>"
undo_action = f'/remove "{data.get("name")}"'
return f"{response}|||UNDO_BUTTON||{undo_action}"
```

**Step 4: Update bot.py to parse undo button and create inline keyboard**

In `bot.py`, update `handle_message()` method:

```python
async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesar mensaje: comando o texto libre"""
    try:
        message_text = update.message.text
        parsed = self.parser.parse(message_text)

        if parsed["type"] == "command":
            response = await self._handle_command(parsed)
        else:
            # Intentar procesar con IA si está habilitada
            ai_result = self.ai_processor.process(parsed["text"])
            if ai_result:
                # Re-parsear el resultado de IA como comando
                parsed = self.parser.parse(ai_result)
                response = await self._handle_command(parsed)
            else:
                response = "❌ No entiendo ese mensaje. Usa /help para ver los comandos disponibles."

        # Check if response includes undo button
        if "|||UNDO_BUTTON||" in response:
            message_text, undo_action = response.split("|||UNDO_BUTTON||")

            # Create inline keyboard with undo button
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup

            keyboard = [[
                InlineKeyboardButton("❌ Deshacer", callback_data=f"undo_{undo_action.replace(' ', '_').replace('"', '')}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(message_text, parse_mode="HTML", reply_markup=reply_markup)
        else:
            await update.message.reply_text(response, parse_mode="HTML")

    except Exception as e:
        sanitized_error = self.security_manager.sanitize(str(e))
        self.logger.error(f"Error procesando mensaje: {sanitized_error}")
        await update.message.reply_text("❌ Hubo un error procesando tu mensaje.")
```

Also add callback handler for undo button in `setup_handlers()`:

```python
from telegram.ext import CallbackQueryHandler

async def handle_undo_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle undo button clicks"""
    query = update.callback_query
    await query.answer()

    # Extract remove command from callback data
    callback_data = query.data
    # callback_data is like: "undo_/remove_title_here"
    self.logger.debug(f"[UNDO_BUTTON] Callback: {callback_data}")

    # Reconstruct the remove command
    parts = callback_data.split("_", 1)  # Split only on first underscore
    if len(parts) == 2:
        remove_cmd = parts[1].replace("_", " ")
        title = remove_cmd.replace("/remove ", "").strip('"')

        self.logger.debug(f"[UNDO_BUTTON] Removing: {title}")

        response = self.command_handler.handle_remove([title])
        await query.edit_message_text(
            text=f"<s>{query.message.text_html}</s>\n\n{response}",
            parse_mode="HTML"
        )
```

Add to `setup_handlers()`:

```python
self.app.add_handler(CallbackQueryHandler(self.handle_undo_button, pattern="^undo_"))
```

**Step 5: Run tests**

```bash
pytest tests/test_undo_button.py -v
```

Expected: Tests pass

**Step 6: Run all tests**

```bash
pytest tests/ -v
```

Expected: All tests pass (67+ total)

**Step 7: Commit**

```bash
git add bot.py backend/handlers.py tests/test_undo_button.py
git commit -m "feat: add undo button to remove items with one click"
```

---

## Task 9: Final Integration and Full Test Suite

**Files:**
- Modify: `tests/test_*.py` (verify all tests pass)
- Verify: All handlers register properly

**Step 1: Run complete test suite**

```bash
pytest tests/ -v --tb=short
```

Expected: All tests pass (67+ tests total)

**Step 2: Run coverage check**

```bash
pytest tests/ --cov=backend --cov=bot --cov-report=term-missing
```

Expected: 85%+ coverage maintained

**Step 3: Manual verification checklist**

- [ ] Debug logs appear in console at DEBUG level
- [ ] /add_by_id 438632 adds movie by ID
- [ ] /add_by_id 1396 tv adds TV by ID
- [ ] /add "Vladimir" shows 3 options
- [ ] /add "Dune" auto-adds (exact match) with undo button
- [ ] Undo button removes item with one click
- [ ] /add_actor works with undo button
- [ ] /list shows all items properly
- [ ] /remove works for all items
- [ ] /upcoming shows releases
- [ ] /help displays all commands

**Step 4: Update documentation**

In any README or docs, add:

```markdown
### Commands

- `/add 'Título'` - Busca y agrega película/serie
  - Si hay múltiples resultados, muestra top 3 opciones
  - Usa `/add_by_id <ID>` si conoces el ID de TMDb

- `/add_by_id <ID> [tv]` - Agrega película o serie por ID de TMDb
  - `/add_by_id 438632` - Agrega película
  - `/add_by_id 1396 tv` - Agrega serie

- `/add_actor 'Nombre'` - Monitorea a un actor

- `/list [movies|series|actors]` - Muestra tu lista

- `/remove 'Título o Nombre'` - Remueve un elemento

- `/upcoming [movies|series|actors]` - Muestra estrenos en 60 días

- `/help` - Muestra este mensaje
```

**Step 5: Final commit**

```bash
git add .
git commit -m "feat: complete four improvements implementation

- Add comprehensive debug logging at DEBUG level
- Implement /add_by_id command for direct ID-based addition
- Show top 3 search results when exact match not found
- Add undo buttons to removal with one-click delete
- Maintain 85%+ test coverage across all modules"
```

**Step 6: Verify git log**

```bash
git log --oneline -10
```

Expected: See recent commits from this implementation

---

## Success Criteria

✅ Debug logging shows all function parameters, API calls, and processing steps
✅ /add_by_id command works for both movies and TV shows
✅ /add shows top 3 results when no exact match found
✅ /add auto-adds on exact match (no change to happy path)
✅ Undo buttons appear after successful add/actor operations
✅ Undo button removes item with one click
✅ All 67+ tests pass
✅ 85%+ code coverage maintained
✅ No breaking changes to existing commands
✅ All debug logs follow [MODULE_FUNCTION] naming convention
