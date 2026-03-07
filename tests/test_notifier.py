import pytest
import tempfile
from unittest.mock import patch, MagicMock
from backend.notifier import Notifier


def test_check_new_releases_movie():
    """detecta nuevos estrenos de películas"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = f"{tmpdir}/movies.json"

        with patch('backend.notifier.Storage') as mock_storage_class, \
             patch('backend.notifier.TMDbClient') as mock_tmdb_class:

            # Setup Storage mock
            mock_storage = MagicMock()
            mock_storage_class.return_value = mock_storage
            mock_storage.get_movies.return_value = [
                {"id": 603, "title": "The Matrix"}
            ]
            mock_storage.get_actors.return_value = []
            mock_storage.is_notified.return_value = False

            # Setup TMDbClient mock
            mock_tmdb = MagicMock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.get_upcoming_releases.return_value = [
                {
                    "id": 603,
                    "title": "The Matrix Reloaded",
                    "release_date": "2025-05-20"
                }
            ]

            notifier = Notifier("test_key", storage_path)
            releases = notifier.check_new_releases()

            assert len(releases) > 0
            assert releases[0]["id"] == 603
            assert releases[0]["title"] == "The Matrix Reloaded"
            mock_storage.mark_notified.assert_called()


def test_format_notification_message():
    """formatea mensajes de notificación con emojis"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = f"{tmpdir}/movies.json"

        with patch('backend.notifier.Storage'), \
             patch('backend.notifier.TMDbClient'):

            notifier = Notifier("test_key", storage_path)

            release = {
                "id": 603,
                "title": "The Matrix Reloaded",
                "release_date": "2025-05-20"
            }

            message = notifier.format_notification(release, "movie")

            assert "The Matrix Reloaded" in message
            assert "2025-05-20" in message
            assert "🎬" in message or "🎥" in message
            assert isinstance(message, str)
            assert len(message) > 0


def test_format_notification_tv():
    """formatea mensajes de notificación para TV"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = f"{tmpdir}/movies.json"

        with patch('backend.notifier.Storage'), \
             patch('backend.notifier.TMDbClient'):

            notifier = Notifier("test_key", storage_path)

            release = {
                "id": 1399,
                "name": "Breaking Bad",
                "first_air_date": "2025-03-15"
            }

            message = notifier.format_notification(release, "tv")

            assert "Breaking Bad" in message
            assert "2025-03-15" in message
            assert "📺" in message
            assert isinstance(message, str)


def test_is_related_to_movie():
    """verifica si un estreno está relacionado con una película"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = f"{tmpdir}/movies.json"

        with patch('backend.notifier.Storage'), \
             patch('backend.notifier.TMDbClient'):

            notifier = Notifier("test_key", storage_path)

            movie = {"title": "The Matrix", "id": 603}
            related = {"title": "The Matrix Reloaded", "id": 234}
            unrelated = {"title": "Inception", "id": 456}

            assert notifier._is_related_to_movie(related, movie) is True
            assert notifier._is_related_to_movie(unrelated, movie) is False


def test_make_release_key():
    """crea clave única para un estreno"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = f"{tmpdir}/movies.json"

        with patch('backend.notifier.Storage'), \
             patch('backend.notifier.TMDbClient'):

            notifier = Notifier("test_key", storage_path)

            key = notifier._make_release_key(603, "2025-05-20")

            assert key == "release_603_2025-05-20"
            assert isinstance(key, str)


def test_notify_callback():
    """establece y ejecuta callbacks de notificación"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = f"{tmpdir}/movies.json"

        with patch('backend.notifier.Storage') as mock_storage_class, \
             patch('backend.notifier.TMDbClient') as mock_tmdb_class:

            mock_storage = MagicMock()
            mock_storage_class.return_value = mock_storage
            mock_storage.get_movies.return_value = []
            mock_storage.get_actors.return_value = []

            mock_tmdb = MagicMock()
            mock_tmdb_class.return_value = mock_tmdb

            notifier = Notifier("test_key", storage_path)

            callback = MagicMock()
            notifier.notify_callback(callback)

            assert notifier.callback == callback


def test_process_releases_with_callback():
    """procesa nuevos estrenos y ejecuta callbacks"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = f"{tmpdir}/movies.json"

        with patch('backend.notifier.Storage') as mock_storage_class, \
             patch('backend.notifier.TMDbClient') as mock_tmdb_class:

            mock_storage = MagicMock()
            mock_storage_class.return_value = mock_storage
            mock_storage.get_movies.return_value = [{"id": 550, "title": "Fight Club"}]
            mock_storage.get_actors.return_value = []
            mock_storage.is_notified.return_value = False

            mock_tmdb = MagicMock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.get_upcoming_releases.return_value = [
                {"id": 550, "title": "Fight Club 2", "release_date": "2025-06-01"}
            ]
            mock_tmdb.get_actor_filmography.return_value = []
            mock_tmdb.get_actor_tv_credits.return_value = []

            notifier = Notifier("test_key", storage_path)

            callback = MagicMock()
            notifier.notify_callback(callback)
            notifier.process_releases()

            callback.assert_called()
