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


def test_check_new_releases_actor_filmography():
    """detecta nuevos estrenos de filmografía de actores"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = f"{tmpdir}/movies.json"

        with patch('backend.notifier.Storage') as mock_storage_class, \
             patch('backend.notifier.TMDbClient') as mock_tmdb_class:

            mock_storage = MagicMock()
            mock_storage_class.return_value = mock_storage
            mock_storage.get_movies.return_value = []
            mock_storage.get_actors.return_value = [{"id": 1, "name": "Brad Pitt"}]
            mock_storage.is_notified.return_value = False

            mock_tmdb = MagicMock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.get_upcoming_releases.return_value = []
            mock_tmdb.get_actor_filmography.return_value = [
                {"id": 550, "title": "Fight Club", "release_date": "2025-01-01"}
            ]
            mock_tmdb.get_actor_tv_credits.return_value = []

            notifier = Notifier("test_key", storage_path)
            releases = notifier.check_new_releases()

            assert len(releases) > 0
            assert releases[0]["id"] == 550
            assert releases[0]["title"] == "Fight Club"
            mock_storage.mark_notified.assert_called()


def test_check_new_releases_actor_tv_credits():
    """detecta nuevos estrenos de series de actores"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = f"{tmpdir}/movies.json"

        with patch('backend.notifier.Storage') as mock_storage_class, \
             patch('backend.notifier.TMDbClient') as mock_tmdb_class:

            mock_storage = MagicMock()
            mock_storage_class.return_value = mock_storage
            mock_storage.get_movies.return_value = []
            mock_storage.get_actors.return_value = [{"id": 1, "name": "Bryan Cranston"}]
            mock_storage.is_notified.return_value = False

            mock_tmdb = MagicMock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.get_upcoming_releases.return_value = []
            mock_tmdb.get_actor_filmography.return_value = []
            mock_tmdb.get_actor_tv_credits.return_value = [
                {"id": 1399, "name": "Breaking Bad", "first_air_date": "2025-02-01"}
            ]

            notifier = Notifier("test_key", storage_path)
            releases = notifier.check_new_releases()

            assert len(releases) > 0
            assert releases[0]["id"] == 1399
            assert releases[0]["name"] == "Breaking Bad"
            mock_storage.mark_notified.assert_called()


def test_process_releases_without_callback():
    """procesa nuevos estrenos sin callback configurado"""
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
            # No configurar callback, debería ejecutarse sin error
            notifier.process_releases()

            assert notifier.callback is None


def test_process_releases_tv_with_callback():
    """procesa nuevos estrenos de TV y ejecuta callbacks"""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = f"{tmpdir}/movies.json"

        with patch('backend.notifier.Storage') as mock_storage_class, \
             patch('backend.notifier.TMDbClient') as mock_tmdb_class:

            mock_storage = MagicMock()
            mock_storage_class.return_value = mock_storage
            mock_storage.get_movies.return_value = []
            mock_storage.get_actors.return_value = [{"id": 1, "name": "Bryan Cranston"}]
            mock_storage.is_notified.return_value = False

            mock_tmdb = MagicMock()
            mock_tmdb_class.return_value = mock_tmdb
            mock_tmdb.get_upcoming_releases.return_value = []
            mock_tmdb.get_actor_filmography.return_value = []
            mock_tmdb.get_actor_tv_credits.return_value = [
                {"id": 1399, "name": "Breaking Bad", "first_air_date": "2025-02-01"}
            ]

            notifier = Notifier("test_key", storage_path)

            callback = MagicMock()
            notifier.notify_callback(callback)
            notifier.process_releases()

            callback.assert_called()
            # Verificar que el mensaje contiene información de TV
            call_args = callback.call_args[0][0]
            assert "Breaking Bad" in call_args or "📺" in call_args


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
