# Directors Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `/add_director` command to monitor directors and receive notifications when they release new films/TV shows (where they direct only).

**Architecture:** Add "directors" as a parallel feature to actors with identical patterns: search → store → monitor → notify. Filter TMDB results by `job == "Director"` to ensure only director credits are tracked.

**Tech Stack:** Python, TMDB API (person search + credits filtering), pytest, TDD

---

## Task 1: Storage - Add director methods

**Files:**
- Modify: `backend/storage.py` (add methods before `get_actors()`)
- Test: `tests/test_storage.py` (add 3 new test methods)

**Step 1: Add test for add_director**

Open `tests/test_storage.py` and add:

```python
def test_add_director():
    """Test adding a director to storage"""
    storage = Storage("test_data.json")
    storage.add_director("Quentin Tarantino", 3179)

    data = storage._load_data()
    assert len(data["directors"]) == 1
    assert data["directors"][0]["name"] == "Quentin Tarantino"
    assert data["directors"][0]["id"] == 3179
    assert "added_date" in data["directors"][0]
```

**Step 2: Run test - expect FAIL**

```bash
pytest tests/test_storage.py::test_add_director -v
```

Expected output: `AttributeError: 'Storage' object has no attribute 'add_director'`

**Step 3: Implement add_director in Storage**

In `backend/storage.py`, after `add_actor()` method (around line 73), add:

```python
def add_director(self, name: str, tmdb_id: int):
    """Agrega un director"""
    self.logger.debug(f"[STORAGE.ADD_DIRECTOR] Adding director: {name} (ID: {tmdb_id})")
    data = self._load_data()

    # Evita duplicados
    if any(director["id"] == tmdb_id for director in data.get("directors", [])):
        return

    director = {
        "name": name,
        "id": tmdb_id,
        "added_date": datetime.now().isoformat()
    }

    # Ensure directors array exists
    if "directors" not in data:
        data["directors"] = []

    data["directors"].append(director)
    self._save_data(data)
    self.logger.debug(f"[STORAGE.ADD_DIRECTOR] Successfully saved to storage")
```

**Step 4: Run test - expect PASS**

```bash
pytest tests/test_storage.py::test_add_director -v
```

Expected: `PASSED`

**Step 5: Add test for remove_director**

```python
def test_remove_director():
    """Test removing a director from storage"""
    storage = Storage("test_data.json")
    storage.add_director("Quentin Tarantino", 3179)

    result = storage.remove_director(3179)
    assert result is True

    data = storage._load_data()
    assert len(data["directors"]) == 0
```

**Step 6: Run test - expect FAIL**

```bash
pytest tests/test_storage.py::test_remove_director -v
```

Expected: `AttributeError`

**Step 7: Implement remove_director**

In `backend/storage.py`, after `add_director()`, add:

```python
def remove_director(self, tmdb_id: int) -> bool:
    """Elimina un director"""
    self.logger.debug(f"[STORAGE.REMOVE_DIRECTOR] Removing director ID: {tmdb_id}")
    data = self._load_data()

    if "directors" not in data:
        return False

    initial_length = len(data["directors"])
    data["directors"] = [d for d in data["directors"] if d["id"] != tmdb_id]

    if len(data["directors"]) < initial_length:
        self._save_data(data)
        self.logger.debug(f"[STORAGE.REMOVE_DIRECTOR] Director removed successfully")
        return True

    return False
```

**Step 8: Run test - expect PASS**

```bash
pytest tests/test_storage.py::test_remove_director -v
```

Expected: `PASSED`

**Step 9: Add test for get_directors**

```python
def test_get_directors():
    """Test retrieving all directors"""
    storage = Storage("test_data.json")
    storage.add_director("Quentin Tarantino", 3179)
    storage.add_director("Steven Spielberg", 488)

    directors = storage.get_directors()
    assert len(directors) == 2
    assert directors[0]["name"] == "Quentin Tarantino"
```

**Step 10: Run test - expect FAIL**

```bash
pytest tests/test_storage.py::test_get_directors -v
```

**Step 11: Implement get_directors**

In `backend/storage.py`, after `remove_director()`, add:

```python
def get_directors(self) -> List[Dict]:
    """Obtiene todos los directores"""
    data = self._load_data()
    return data.get("directors", [])
```

**Step 12: Run test - expect PASS**

```bash
pytest tests/test_storage.py::test_get_directors -v
```

**Step 13: Update storage initialization**

In `_initialize_storage()` (around line 17), update:

```python
def _initialize_storage(self):
    """Inicializa el archivo JSON con estructura vacía"""
    data = {
        "movies": [],
        "actors": [],
        "directors": [],  # ADD THIS LINE
        "notified": []
    }
    with open(self.path, 'w') as f:
        json.dump(data, f, indent=2)
```

**Step 14: Run all storage tests**

```bash
pytest tests/test_storage.py -v
```

Expected: All tests PASS (including existing ones)

**Step 15: Commit**

```bash
git add backend/storage.py tests/test_storage.py
git commit -m "feat: add director storage methods (add/remove/get)"
```

---

## Task 2: TMDb Client - get_director_id

**Files:**
- Modify: `backend/tmdb_client.py` (add new method before `get_actor_filmography`)
- Test: `tests/test_tmdb_client.py` (add 2 new test methods)

**Step 1: Write test for get_director_id - exact match**

```python
@patch('backend.http_client.RequestManager.get')
def test_get_director_id(self, mock_get):
    """Test getting director ID by name"""
    mock_get.return_value = {
        "results": [
            {
                "id": 3179,
                "name": "Quentin Tarantino",
                "known_for_department": "Directing"
            }
        ]
    }

    result = self.client.get_director_id("Quentin Tarantino")

    self.assertIsNotNone(result)
    self.assertEqual(result, 3179)
    mock_get.assert_called_once()
```

**Step 2: Run test - expect FAIL**

```bash
pytest tests/test_tmdb_client.py::TestTMDbClient::test_get_director_id -v
```

Expected: `AttributeError: 'TMDbClient' object has no attribute 'get_director_id'`

**Step 3: Implement get_director_id (identical to get_actor_id)**

In `backend/tmdb_client.py`, before `get_actor_filmography()`, add:

```python
def get_director_id(self, director_name: str) -> Optional[int]:
    """Get director ID by name - prefers exact matches, then most popular"""
    self.logger.debug(f"[GET_DIRECTOR_ID] Searching for director: {director_name}")

    data = self._make_request("/search/person", {"query": director_name})
    if not data or "results" not in data or not data["results"]:
        self.logger.debug(f"[GET_DIRECTOR_ID] No results for: {director_name}")
        return None

    self.logger.debug(f"[GET_DIRECTOR_ID] Found {len(data['results'])} results")

    # Normalize search name for comparison
    search_name_lower = director_name.lower().strip()
    search_words = set(search_name_lower.split())

    # First pass: look for exact name match
    for result in data["results"]:
        if result.get("name"):
            result_name_lower = result["name"].lower().strip()
            if result_name_lower == search_name_lower:
                self.logger.debug(f"[GET_DIRECTOR_ID] Exact match found: {result['name']} (ID: {result.get('id')})")
                return result.get("id")

    # Second pass: look for names containing all search words (multi-word matches)
    candidates = []
    for result in data["results"]:
        if result.get("name") and result.get("id"):
            result_name_lower = result["name"].lower().strip()
            result_words = set(result_name_lower.split())
            # Check if all search words are in result name
            if search_words.issubset(result_words):
                popularity = result.get("popularity", 0)
                candidates.append((popularity, result))

    if candidates:
        # Sort by popularity (descending) and take the most popular
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_match = candidates[0][1]
        self.logger.debug(f"[GET_DIRECTOR_ID] Multi-word match found: {best_match['name']} (ID: {best_match.get('id')}, popularity: {best_match.get('popularity')})")
        return best_match.get("id")

    # Third pass: look for names starting with search term
    for result in data["results"]:
        if result.get("name"):
            result_name_lower = result["name"].lower().strip()
            if result_name_lower.startswith(search_name_lower):
                self.logger.debug(f"[GET_DIRECTOR_ID] Prefix match found: {result['name']} (ID: {result.get('id')})")
                return result.get("id")

    # Fall back to most popular result with known_for_department
    best_result = None
    best_popularity = -1
    for result in data["results"]:
        if result.get("id") and result.get("known_for_department"):
            popularity = result.get("popularity", 0)
            if popularity > best_popularity:
                best_popularity = popularity
                best_result = result

    if best_result:
        self.logger.debug(f"[GET_DIRECTOR_ID] Using most popular result: {best_result['name']} (ID: {best_result.get('id')}, popularity: {best_popularity})")
        return best_result.get("id")

    # Last resort: most popular result with ID
    best_result = None
    best_popularity = -1
    for result in data["results"]:
        if result.get("id"):
            popularity = result.get("popularity", 0)
            if popularity > best_popularity:
                best_popularity = popularity
                best_result = result

    if best_result:
        self.logger.debug(f"[GET_DIRECTOR_ID] Using most popular result (last resort): {best_result.get('name')} (ID: {best_result['id']}, popularity: {best_popularity})")
        return best_result.get("id")

    self.logger.debug(f"[GET_DIRECTOR_ID] No valid results for: {director_name}")
    return None
```

**Step 4: Run test - expect PASS**

```bash
pytest tests/test_tmdb_client.py::TestTMDbClient::test_get_director_id -v
```

Expected: `PASSED`

**Step 5: Add test for multi-word director search**

```python
@patch('backend.http_client.RequestManager.get')
def test_get_director_id_multi_word(self, mock_get):
    """Test that director search prefers results with all keywords"""
    mock_get.return_value = {
        "results": [
            {
                "id": 1234,
                "name": "John",
                "popularity": 5.0,
                "known_for_department": "Directing"
            },
            {
                "id": 5678,
                "name": "John Hughes",
                "popularity": 50.0,
                "known_for_department": "Directing"
            }
        ]
    }

    result = self.client.get_director_id("John Hughes")

    self.assertEqual(result, 5678)
```

**Step 6: Run test - expect PASS**

```bash
pytest tests/test_tmdb_client.py::TestTMDbClient::test_get_director_id_multi_word -v
```

**Step 7: Run all TMDb tests**

```bash
pytest tests/test_tmdb_client.py -v
```

Expected: All tests PASS

**Step 8: Commit**

```bash
git add backend/tmdb_client.py tests/test_tmdb_client.py
git commit -m "feat: add get_director_id search method"
```

---

## Task 3: TMDb Client - get_director_filmography

**Files:**
- Modify: `backend/tmdb_client.py` (add method after `get_director_id`)
- Test: `tests/test_tmdb_client.py` (add test)

**Step 1: Write test for get_director_filmography**

```python
@patch('backend.http_client.RequestManager.get')
def test_get_director_filmography(self, mock_get):
    """Test getting director's filmography filtered by Director job"""
    mock_get.return_value = {
        "cast": [
            {
                "id": 550,
                "title": "Fight Club",
                "release_date": "1999-10-15",
                "job": "Actor"  # Should be filtered out
            }
        ],
        "crew": [
            {
                "id": 550,
                "title": "Fight Club",
                "release_date": "1999-10-15",
                "job": "Director"  # Should be included
            },
            {
                "id": 278,
                "title": "The Shawshank Redemption",
                "release_date": "1994-09-23",
                "job": "Director"  # Should be included
            }
        ]
    }

    result = self.client.get_director_filmography(3179)

    self.assertIsNotNone(result)
    self.assertEqual(len(result), 2)
    self.assertEqual(result[0]["title"], "Fight Club")
    self.assertEqual(result[1]["title"], "The Shawshank Redemption")
```

**Step 2: Run test - expect FAIL**

```bash
pytest tests/test_tmdb_client.py::TestTMDbClient::test_get_director_filmography -v
```

Expected: `AttributeError`

**Step 3: Implement get_director_filmography**

In `backend/tmdb_client.py`, after `get_director_id()`, add:

```python
def get_director_filmography(self, director_id: int) -> List[Dict]:
    """Get director's movie filmography - only where job='Director'"""
    data = self._make_request(
        f"/person/{director_id}/movie_credits",
        {}
    )
    if not data:
        return []

    # Filter for Director role in crew
    filmography = []

    if "crew" in data:
        for movie in data["crew"]:
            if movie.get("job") == "Director" and movie.get("title") and movie.get("release_date"):
                filmography.append(movie)

    return filmography
```

**Step 4: Run test - expect PASS**

```bash
pytest tests/test_tmdb_client.py::TestTMDbClient::test_get_director_filmography -v
```

**Step 5: Run all TMDb tests**

```bash
pytest tests/test_tmdb_client.py -v
```

**Step 6: Commit**

```bash
git add backend/tmdb_client.py tests/test_tmdb_client.py
git commit -m "feat: add get_director_filmography with job filtering"
```

---

## Task 4: TMDb Client - get_director_tv_credits

**Files:**
- Modify: `backend/tmdb_client.py` (add method after `get_director_filmography`)
- Test: `tests/test_tmdb_client.py` (add test)

**Step 1: Write test for get_director_tv_credits**

```python
@patch('backend.http_client.RequestManager.get')
def test_get_director_tv_credits(self, mock_get):
    """Test getting director's TV credits filtered by Director job"""
    mock_get.return_value = {
        "crew": [
            {
                "id": 1399,
                "name": "Breaking Bad",
                "first_air_date": "2008-01-20",
                "job": "Director"
            },
            {
                "id": 1396,
                "name": "Better Call Saul",
                "first_air_date": "2015-02-09",
                "job": "Producer"  # Should be filtered out
            }
        ]
    }

    result = self.client.get_director_tv_credits(3179)

    self.assertIsNotNone(result)
    self.assertEqual(len(result), 1)
    self.assertEqual(result[0]["name"], "Breaking Bad")
```

**Step 2: Run test - expect FAIL**

```bash
pytest tests/test_tmdb_client.py::TestTMDbClient::test_get_director_tv_credits -v
```

**Step 3: Implement get_director_tv_credits**

In `backend/tmdb_client.py`, after `get_director_filmography()`, add:

```python
def get_director_tv_credits(self, director_id: int) -> List[Dict]:
    """Get director's TV show credits - only where job='Director'"""
    data = self._make_request(
        f"/person/{director_id}/tv_credits",
        {}
    )
    if not data:
        return []

    # Filter for Director role in crew
    tv_credits = []

    if "crew" in data:
        for show in data["crew"]:
            if show.get("job") == "Director" and show.get("name") and show.get("first_air_date"):
                tv_credits.append(show)

    return tv_credits
```

**Step 4: Run test - expect PASS**

```bash
pytest tests/test_tmdb_client.py::TestTMDbClient::test_get_director_tv_credits -v
```

**Step 5: Run all tests**

```bash
pytest tests/test_tmdb_client.py tests/test_storage.py -v
```

**Step 6: Commit**

```bash
git add backend/tmdb_client.py tests/test_tmdb_client.py
git commit -m "feat: add get_director_tv_credits with job filtering"
```

---

## Task 5: Handlers - handle_add_director

**Files:**
- Modify: `backend/handlers.py` (add new method)
- Test: `tests/test_handlers.py` (add 2 test methods)

**Step 1: Write test for handle_add_director - success**

```python
@patch('backend.tmdb_client.TMDbClient.get_director_id')
def test_handle_add_director(self, mock_get_id):
    """Test adding a director successfully"""
    mock_get_id.return_value = 3179

    handler = CommandHandler(self.api_key, self.storage_path)
    result = handler.handle_add_director(["Quentin Tarantino"])

    self.assertIn("Monitoreando a Quentin Tarantino", result)
    self.assertIn("🎬", result)
    self.assertIn("/remove", result)

    # Verify stored
    directors = handler.storage.get_directors()
    assert len(directors) == 1
    assert directors[0]["name"] == "Quentin Tarantino"
```

**Step 2: Run test - expect FAIL**

```bash
pytest tests/test_handlers.py::TestCommandHandler::test_handle_add_director -v
```

**Step 3: Implement handle_add_director**

In `backend/handlers.py`, after `handle_add_actor()` (around line 131), add:

```python
def handle_add_director(self, args: List[str]) -> str:
    """Handle /add_director command - monitor director's projects"""
    if not args:
        self.logger.warning("[HANDLE_ADD_DIRECTOR] No arguments provided")
        return "❌ Por favor especifica el nombre del director: /add_director \"Nombre\""

    director_name = args[0].strip().strip('"\'"\"\'')
    self.logger.debug(f"[HANDLE_ADD_DIRECTOR] Searching for director: {director_name}")

    director_id = self.tmdb.get_director_id(director_name)

    if not director_id:
        self.logger.warning(f"[HANDLE_ADD_DIRECTOR] Director not found: {director_name}")
        return f"❌ No encontré al director '{director_name}' en TMDb."

    self.storage.add_director(director_name, director_id)
    self.logger.info(f"[HANDLE_ADD_DIRECTOR] Director added: {director_name} (ID: {director_id})")
    tmdb_link = f"https://www.themoviedb.org/person/{director_id}"
    response = f"✅ Monitoreando a {director_name} 🎬\n<a href='{tmdb_link}'>Ver en TMDb</a>"
    undo_action = f'/remove "{director_name}"'
    return f"{response}|||UNDO_BUTTON||{undo_action}"
```

**Step 4: Run test - expect PASS**

```bash
pytest tests/test_handlers.py::TestCommandHandler::test_handle_add_director -v
```

**Step 5: Write test for handle_add_director - not found**

```python
@patch('backend.tmdb_client.TMDbClient.get_director_id')
def test_handle_add_director_not_found(self, mock_get_id):
    """Test adding director when not found"""
    mock_get_id.return_value = None

    handler = CommandHandler(self.api_key, self.storage_path)
    result = handler.handle_add_director(["UnknownDirector"])

    self.assertIn("❌", result)
    self.assertIn("No encontré", result)
```

**Step 6: Run test - expect PASS**

```bash
pytest tests/test_handlers.py::TestCommandHandler::test_handle_add_director_not_found -v
```

**Step 7: Run all handler tests**

```bash
pytest tests/test_handlers.py -v
```

**Step 8: Commit**

```bash
git add backend/handlers.py tests/test_handlers.py
git commit -m "feat: add handle_add_director command handler"
```

---

## Task 6: Handlers - update handle_list and handle_remove

**Files:**
- Modify: `backend/handlers.py` (update 2 methods)
- Test: `tests/test_handlers.py` (update tests)

**Step 1: Check current handle_list implementation**

Review `handle_list()` in handlers.py to understand structure

**Step 2: Update handle_list to show directors**

Find the section where actors are displayed (around line 145-170) and add directors:

```python
# After actors display, add:
if actors:
    response += "👤 **Actores monitoreados:**\n"
    for actor in actors:
        response += f"  • {actor['name']} - /remove \"{actor['name']}\"\n"

# Add directors display:
directors = self.storage.get_directors()
if directors:
    response += "\n🎬 **Directores monitoreados:**\n"
    for director in directors:
        response += f"  • {director['name']} - /remove \"{director['name']}\"\n"
```

**Step 3: Review handle_remove implementation**

The existing `handle_remove()` already supports both actors and directors since it searches by name/ID in all categories.

**Step 4: Add test to verify directors in list**

```python
@patch('backend.tmdb_client.TMDbClient.get_actor_id')
@patch('backend.tmdb_client.TMDbClient.get_director_id')
def test_handle_list_shows_directors(self, mock_dir_id, mock_actor_id):
    """Test that /list shows directors"""
    mock_actor_id.return_value = 287
    mock_dir_id.return_value = 3179

    handler = CommandHandler(self.api_key, self.storage_path)
    handler.handle_add_actor(["Brad Pitt"])
    handler.handle_add_director(["Quentin Tarantino"])

    result = handler.handle_list()

    self.assertIn("Brad Pitt", result)
    self.assertIn("Quentin Tarantino", result)
    self.assertIn("Directores", result)
```

**Step 5: Run test**

```bash
pytest tests/test_handlers.py::TestCommandHandler::test_handle_list_shows_directors -v
```

**Step 6: Run all tests**

```bash
pytest tests/test_handlers.py -v
```

**Step 7: Commit**

```bash
git add backend/handlers.py tests/test_handlers.py
git commit -m "feat: update handle_list and handle_remove to support directors"
```

---

## Task 7: Notifier - add director monitoring

**Files:**
- Modify: `backend/notifier.py` (add director section in check_new_releases)
- Test: `tests/test_notifier.py` (add 2 tests)

**Step 1: Write test for director filmography notifications**

```python
@patch('backend.tmdb_client.TMDbClient.get_director_filmography')
def test_check_new_releases_director_filmography(self, mock_filmography):
    """Test that new director filmography is detected"""
    mock_filmography.return_value = [
        {
            "id": 550,
            "title": "Fight Club",
            "release_date": "1999-10-15"
        }
    ]

    notifier = Notifier(self.api_key, self.storage_path)
    notifier.storage.add_director("Quentin Tarantino", 3179)

    releases = notifier.check_new_releases()

    assert len(releases) > 0
    assert any(r["title"] == "Fight Club" for r in releases)
```

**Step 2: Run test - expect FAIL**

```bash
pytest tests/test_notifier.py::test_check_new_releases_director_filmography -v
```

**Step 3: Update check_new_releases in Notifier**

In `backend/notifier.py`, in `check_new_releases()` method, after the actors section (around line 69), add:

```python
        # Obtener directores seguidos
        directors = self.storage.get_directors()
        for director in directors:
            # Obtener filmografía del director (solo donde dirige)
            filmography = self.tmdb_client.get_director_filmography(director["id"])
            for release in filmography:
                release_key = self._make_release_key(
                    release["id"],
                    release.get("release_date", "")
                )

                # Verificar si ya fue notificado
                if not self.storage.is_notified(release_key):
                    new_releases.append(release)
                    self.storage.mark_notified(release_key)

            # Obtener series del director (solo donde dirige)
            tv_credits = self.tmdb_client.get_director_tv_credits(director["id"])
            for release in tv_credits:
                release_key = self._make_release_key(
                    release["id"],
                    release.get("first_air_date", "")
                )

                # Verificar si ya fue notificado
                if not self.storage.is_notified(release_key):
                    new_releases.append(release)
                    self.storage.mark_notified(release_key)
```

**Step 4: Run test - expect PASS**

```bash
pytest tests/test_notifier.py::test_check_new_releases_director_filmography -v
```

**Step 5: Write test for director TV credits**

```python
@patch('backend.tmdb_client.TMDbClient.get_director_tv_credits')
def test_check_new_releases_director_tv(self, mock_tv_credits):
    """Test that new director TV credits are detected"""
    mock_tv_credits.return_value = [
        {
            "id": 1399,
            "name": "Breaking Bad",
            "first_air_date": "2008-01-20"
        }
    ]

    notifier = Notifier(self.api_key, self.storage_path)
    notifier.storage.add_director("Vince Gilligan", 2288)

    releases = notifier.check_new_releases()

    assert len(releases) > 0
    assert any(r["name"] == "Breaking Bad" for r in releases)
```

**Step 6: Run test - expect PASS**

```bash
pytest tests/test_notifier.py::test_check_new_releases_director_tv -v
```

**Step 7: Run all notifier tests**

```bash
pytest tests/test_notifier.py -v
```

**Step 8: Commit**

```bash
git add backend/notifier.py tests/test_notifier.py
git commit -m "feat: add director monitoring to notifier"
```

---

## Task 8: Bot - register /add_director handler

**Files:**
- Modify: `bot.py` (register command handler)

**Step 1: Add handler registration**

In `bot.py`, find where handlers are registered (search for `CommandHandler`), and add:

```python
# Add director command
app.add_handler(CommandHandler("add_director", handle_add_director))
```

Where `handle_add_director` is defined as:

```python
async def handle_add_director(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add_director command"""
    try:
        args = context.args if context.args else []
        response = command_handler.handle_add_director(args)
        await update.message.reply_html(response, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error en /add_director: {str(e)}")
        await update.message.reply_text("❌ Hubo un error procesando tu mensaje.")
```

**Step 2: Test manually**

Run bot: `python bot.py`
Send `/add_director "Steven Spielberg"`
Expected: Bot responds with director added message

**Step 3: Commit**

```bash
git add bot.py
git commit -m "feat: register /add_director command handler"
```

---

## Task 9: Integration testing and full test run

**Files:**
- Run: All tests

**Step 1: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests PASS

**Step 2: Check test coverage**

```bash
pytest --cov=backend tests/
```

Expected: Coverage maintained or improved

**Step 3: Manual bot testing**

Run: `python bot.py`

Test commands:
- `/add_director "Quentin Tarantino"`
- `/list` (should show director)
- `/remove "Quentin Tarantino"`
- `/list` (should be gone)

**Step 4: Final commit**

```bash
git status
```

If clean, done. If not, commit remaining changes:

```bash
git add .
git commit -m "test: add director integration tests"
```

---

## Commit Summary

Expected commits (in order):
1. `feat: add director storage methods (add/remove/get)`
2. `feat: add get_director_id search method`
3. `feat: add get_director_filmography with job filtering`
4. `feat: add get_director_tv_credits with job filtering`
5. `feat: add handle_add_director command handler`
6. `feat: update handle_list and handle_remove to support directors`
7. `feat: add director monitoring to notifier`
8. `feat: register /add_director command handler`
9. `test: add director integration tests` (if needed)

---

## Key Implementation Notes

1. **Job Filtering:** TMDB API returns crew credits with a `job` field. Filter strictly for `job == "Director"` in both movies and TV shows.

2. **Storage Consistency:** Directors stored exactly like actors with `name`, `id`, `added_date`.

3. **Notification Key:** Reuse existing `_make_release_key()` to create unique keys per film/show, preventing duplicates.

4. **Search Logic:** `get_director_id()` uses identical logic to `get_actor_id()` - exact match → multi-word → prefix → most popular.

5. **Error Handling:** Handle missing `known_for_department` and empty results gracefully.

6. **Test Mocking:** Mock `RequestManager.get()` in TMDB client tests; mock entire methods in handler/notifier tests.

---

## Success Criteria

- ✅ All 85+ tests pass
- ✅ `/add_director "Name"` searches and adds directors
- ✅ `/list` shows directors separately
- ✅ `/remove` works with directors
- ✅ Notifier detects new films/TV shows where director directed
- ✅ No duplicate notifications (uses existing `is_notified` system)
- ✅ Undo buttons work with directors
- ✅ Bot handles `/add_director` command without errors
