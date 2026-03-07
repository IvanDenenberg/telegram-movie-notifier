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
