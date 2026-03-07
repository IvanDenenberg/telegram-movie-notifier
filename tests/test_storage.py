import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from backend.storage import Storage


def test_storage_initialization():
    """storage se crea con estructura correcta"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "movies.json"
        storage = Storage(str(storage_path))

        assert storage_path.exists()
        with open(storage_path, 'r') as f:
            data = json.load(f)
        assert "movies" in data
        assert "actors" in data
        assert "notified" in data
        assert data["movies"] == []
        assert data["actors"] == []
        assert data["notified"] == []


def test_add_movie():
    """agregar película"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "movies.json"
        storage = Storage(str(storage_path))

        storage.add_movie("The Matrix", 603)
        movies = storage.get_movies()

        assert len(movies) == 1
        assert movies[0]["title"] == "The Matrix"
        assert movies[0]["id"] == 603
        assert "added_date" in movies[0]


def test_add_actor():
    """agregar actor"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "movies.json"
        storage = Storage(str(storage_path))

        storage.add_actor("Keanu Reeves", 2157)
        actors = storage.get_actors()

        assert len(actors) == 1
        assert actors[0]["name"] == "Keanu Reeves"
        assert actors[0]["id"] == 2157
        assert "added_date" in actors[0]


def test_mark_notified():
    """marcar como notificado"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "movies.json"
        storage = Storage(str(storage_path))

        release_key = "movie_603_2025-05-20"
        storage.mark_notified(release_key)

        with open(storage_path, 'r') as f:
            data = json.load(f)
        assert release_key in data["notified"]


def test_is_notified():
    """verificar si fue notificado"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "movies.json"
        storage = Storage(str(storage_path))

        release_key = "movie_603_2025-05-20"
        assert storage.is_notified(release_key) is False

        storage.mark_notified(release_key)
        assert storage.is_notified(release_key) is True


def test_remove_movie():
    """eliminar película"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "movies.json"
        storage = Storage(str(storage_path))

        storage.add_movie("The Matrix", 603)
        assert len(storage.get_movies()) == 1

        result = storage.remove_movie(603)
        assert result is True
        assert len(storage.get_movies()) == 0

        result = storage.remove_movie(999)
        assert result is False


def test_remove_actor():
    """eliminar actor"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "movies.json"
        storage = Storage(str(storage_path))

        storage.add_actor("Keanu Reeves", 2157)
        assert len(storage.get_actors()) == 1

        result = storage.remove_actor(2157)
        assert result is True
        assert len(storage.get_actors()) == 0

        result = storage.remove_actor(999)
        assert result is False
