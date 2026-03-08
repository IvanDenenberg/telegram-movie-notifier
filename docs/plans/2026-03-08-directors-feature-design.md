# Design: Directors Feature

**Date:** 2026-03-08
**Status:** Approved
**Objective:** Add support for monitoring directors and receiving notifications when they release new films/TV shows

---

## Summary

Add a new "directors" feature parallel to the existing "actors" feature. Users can:
- `/add_director "Name"` - Monitor a director
- Get notifications when the director releases new films or TV shows (where they **direct only**)
- `/remove "Name"` - Remove director from monitoring
- `/list` - See all directors (alongside movies and actors)

---

## Requirements

1. **Role Filtering:** Only track films/shows where the person is credited as "Director" (not actor, screenwriter, producer, etc.)
2. **Both Media Types:** Support movies AND TV series
3. **No Duplicate Notifications:** Use existing `is_notified` / `mark_notified` system
4. **Consistent UX:** Same storage structure, list interface, and undo buttons as actors
5. **Search Quality:** Use same intelligent multi-word search as actors/movies (popularidad-based)

---

## Architecture

### Storage (`backend/storage.py`)

**New JSON structure:**
```json
{
  "movies": [...],
  "actors": [...],
  "directors": [
    {
      "name": "Quentin Tarantino",
      "id": 3179,
      "added_date": "2026-03-08T..."
    }
  ],
  "notified": [...]
}
```

**New methods:**
- `add_director(name: str, tmdb_id: int)` - Add director
- `remove_director(tmdb_id: int) -> bool` - Remove director
- `get_directors() -> List[Dict]` - Get all directors

**Reused:**
- `is_notified()`, `mark_notified()` - Same notification history

---

### TMDb Client (`backend/tmdb_client.py`)

**New methods:**
1. `get_director_id(director_name: str) -> Optional[int]`
   - Search for person by name (same intelligent search as `get_actor_id()`)
   - Returns TMDb person ID

2. `get_director_filmography(director_id: int) -> List[Dict]`
   - Get all movies credited as "Director" only
   - Filter: `job == "Director"`
   - Returns: List of movie dicts with title, release_date, id

3. `get_director_tv_credits(director_id: int) -> List[Dict]`
   - Get all TV shows credited as "Director" only
   - Filter: `job == "Director"`
   - Returns: List of TV show dicts with name, first_air_date, id

---

### Handlers (`backend/handlers.py`)

**New method:**
- `handle_add_director(args: List[str]) -> str`
  - Parse director name from args
  - Call `tmdb.get_director_id()`
  - If found: store with `storage.add_director()`
  - Response: "✅ Monitoreando a [Name] 🎬\n<a href='...'>Ver en TMDb</a>"
  - Include undo button: `/remove "[Name]"`
  - If not found: "❌ No encontré al director '[Name]' en TMDb"

**Updated method:**
- `handle_list()` - Show directors alongside actors in list output

---

### Notifier (`backend/notifier.py`)

**New section in `check_new_releases()`:**
```python
# Get directors being monitored
directors = storage.get_directors()
for director in directors:
    # Get movies where they directed
    filmography = tmdb.get_director_filmography(director["id"])
    for release in filmography:
        release_key = _make_release_key(release["id"], release.get("release_date", ""))
        if not is_notified(release_key):
            new_releases.append(release)
            mark_notified(release_key)

    # Get TV shows where they directed
    tv_credits = tmdb.get_director_tv_credits(director["id"])
    for release in tv_credits:
        release_key = _make_release_key(release["id"], release.get("first_air_date", ""))
        if not is_notified(release_key):
            new_releases.append(release)
            mark_notified(release_key)
```

---

## Bot Integration (`bot.py`)

Add handler registration:
```python
app.add_handler(CommandHandler("add_director", handle_add_director))
```

---

## Testing

1. **Unit Tests** (`tests/test_tmdb_client.py`):
   - `test_get_director_id()` - Search and find director
   - `test_get_director_id_multi_word()` - Test intelligent search
   - `test_get_director_filmography()` - Verify job filter = "Director"
   - `test_get_director_tv_credits()` - Verify job filter = "Director"

2. **Handler Tests** (`tests/test_handlers.py`):
   - `test_handle_add_director()` - Add director and store
   - `test_handle_add_director_not_found()` - Error handling

3. **Integration Tests** (`tests/test_notifier.py`):
   - `test_check_new_releases_director_filmography()` - Get new films
   - `test_check_new_releases_director_tv_credits()` - Get new TV shows

---

## Key Design Decisions

1. **Parallel Structure:** Directors as separate from actors (not a unified "people" table) for simplicity and consistency with current architecture
2. **Strict Role Filtering:** Only `job == "Director"`, not co-directors or other roles (keeps it clean)
3. **Reuse Notification System:** Existing `is_notified` / `mark_notified` prevents duplicate notifications across all media types
4. **Same Search Logic:** Use same intelligent multi-word search and popularity-based ranking as actors

---

## Future Enhancements (Out of Scope)

- Support other roles: screenwriter, producer, cinematographer
- Combined person monitoring (show all roles for a person)
- Filter notifications by role type
- Statistics: "Directors with most releases" dashboard

---

## Files Modified

- `backend/storage.py` - Add director methods
- `backend/tmdb_client.py` - Add director search/filmography
- `backend/handlers.py` - Add handle_add_director()
- `backend/notifier.py` - Add director monitoring loop
- `bot.py` - Register /add_director handler
- `tests/test_*.py` - Add tests

---

## Estimated Complexity

- **Storage:** Low (1 new section, 3 methods)
- **TMDb Client:** Medium (3 new methods, role filtering logic)
- **Handlers:** Low (1 new handler, reuse existing patterns)
- **Notifier:** Medium (parallel loop, same filtering)
- **Testing:** Medium (6-8 new tests)

**Total:** ~200-300 lines of new code
