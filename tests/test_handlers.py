import unittest
import logging
from unittest.mock import patch, MagicMock
from backend.handlers import CommandHandler


class TestCommandHandler(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_api_key_12345"
        self.storage_path = "test_data/test_movies.json"

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_add_movie(self, mock_tmdb_class, mock_storage_class):
        """Test adding a movie with /add command"""
        # Setup mocks
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock search result
        mock_tmdb.search_movie.return_value = {
            "id": 438631,
            "title": "Dune",
            "release_date": "2021-09-03"
        }

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_add(["Dune"])

        # Verify
        self.assertIn("Dune", result)
        self.assertIn("✅", result)
        mock_storage.add_movie.assert_called_once_with("Dune", 438631, media_type="movie")

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_add_movie_not_found(self, mock_tmdb_class, mock_storage_class):
        """Test adding a movie when it's not found"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock no result for both movie and TV
        mock_tmdb.search_movie.return_value = None
        mock_tmdb.search_tv.return_value = None
        mock_tmdb.get_search_results.return_value = []

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_add(["NonexistentMovieXYZ"])

        # Verify
        self.assertIn("❌", result)
        self.assertIn("No encontré", result)
        mock_storage.add_movie.assert_not_called()

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_add_actor(self, mock_tmdb_class, mock_storage_class):
        """Test adding an actor with /add_actor command"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock actor ID
        mock_tmdb.get_actor_id.return_value = 500

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_add_actor(["Tom Cruise"])

        # Verify
        self.assertIn("Tom Cruise", result)
        self.assertIn("✅", result)
        self.assertIn("Monitoreando", result)
        mock_storage.add_actor.assert_called_once_with("Tom Cruise", 500)

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_add_actor_not_found(self, mock_tmdb_class, mock_storage_class):
        """Test adding an actor when not found"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock no actor found
        mock_tmdb.get_actor_id.return_value = None

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_add_actor(["UnknownActorXYZ"])

        # Verify
        self.assertIn("❌", result)
        self.assertIn("No encontré al actor", result)
        mock_storage.add_actor.assert_not_called()

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_list(self, mock_tmdb_class, mock_storage_class):
        """Test listing movies and actors"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock data
        mock_storage.get_movies.return_value = [
            {"title": "Dune", "id": 438631, "type": "movie"}
        ]
        mock_storage.get_actors.return_value = [
            {"name": "Tom Cruise", "id": 500}
        ]

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_list()

        # Verify
        self.assertIn("Dune", result)
        self.assertIn("Tom Cruise", result)
        self.assertIn("🎬", result)
        self.assertIn("👤", result)

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_list_empty(self, mock_tmdb_class, mock_storage_class):
        """Test listing when empty"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock empty data
        mock_storage.get_movies.return_value = []
        mock_storage.get_actors.return_value = []
        mock_storage.get_directors.return_value = []

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_list()

        # Verify
        self.assertIn("No tienes nada en tu lista", result)

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_remove(self, mock_tmdb_class, mock_storage_class):
        """Test removing a movie"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock find and remove
        mock_storage.get_movies.return_value = [
            {"title": "Dune", "id": 438631}
        ]
        mock_storage.get_actors.return_value = []
        mock_storage.remove_movie.return_value = True

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_remove(["Dune"])

        # Verify
        self.assertIn("✅", result)
        self.assertIn("removida", result)
        mock_storage.remove_movie.assert_called_once()

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_remove_not_found(self, mock_tmdb_class, mock_storage_class):
        """Test removing when item not found"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock empty storage
        mock_storage.get_movies.return_value = []
        mock_storage.get_actors.return_value = []

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_remove(["NonexistentItem"])

        # Verify
        self.assertIn("❌", result)
        self.assertIn("No encontré", result)

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_help(self, mock_tmdb_class, mock_storage_class):
        """Test help command"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_help()

        # Verify help contains commands
        self.assertIn("/add", result)
        self.assertIn("/add_actor", result)
        self.assertIn("/list", result)
        self.assertIn("/remove", result)
        self.assertIn("/help", result)

    @patch('backend.handlers.Notifier')
    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_upcoming_all(self, mock_tmdb, mock_storage, mock_notifier):
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

        mock_notifier_instance = MagicMock()
        mock_notifier.return_value = mock_notifier_instance
        mock_notifier_instance.get_releases_in_range.return_value = {
            "movies": [
                {
                    "id": 1,
                    "title": "Movie1",
                    "release_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                }
            ],
            "series": [],
            "actors": []
        }

        handler = CommandHandler("fake_key", "fake_storage.json")
        response = handler.handle_upcoming([])

        assert "🎬" in response or "Movie1" in response
        assert "película" in response.lower() or "películas" in response.lower()

    @patch('backend.handlers.Notifier')
    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_upcoming_empty(self, mock_tmdb, mock_storage, mock_notifier):
        """Test /upcoming sin resultados"""
        mock_storage_instance = MagicMock()
        mock_storage.return_value = mock_storage_instance
        mock_storage_instance.get_movies.return_value = []
        mock_storage_instance.get_actors.return_value = []

        mock_tmdb_instance = MagicMock()
        mock_tmdb.return_value = mock_tmdb_instance

        mock_notifier_instance = MagicMock()
        mock_notifier.return_value = mock_notifier_instance
        mock_notifier_instance.get_releases_in_range.return_value = {
            "movies": [],
            "series": [],
            "actors": []
        }

        handler = CommandHandler("fake_key", "fake_storage.json")
        response = handler.handle_upcoming([])

        assert "No hay estrenos" in response or "próximos 60 días" in response

    @patch('backend.handlers.Notifier')
    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_upcoming_filter_movies(self, mock_tmdb, mock_storage, mock_notifier):
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

        mock_notifier_instance = MagicMock()
        mock_notifier.return_value = mock_notifier_instance
        mock_notifier_instance.get_releases_in_range.return_value = {
            "movies": [
                {
                    "id": 1,
                    "title": "Movie1",
                    "release_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                }
            ],
            "series": [],
            "actors": []
        }

        handler = CommandHandler("fake_key", "fake_storage.json")
        response = handler.handle_upcoming(["movies"])

        assert "Movie1" in response or "película" in response.lower()

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_add_logs_operation(self, mock_tmdb_class, mock_storage_class):
        """Test that /add command logs debug information"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        mock_tmdb.search_movie.return_value = {"title": "Dune", "id": 438632, "release_date": "2021-10-01"}

        handler = CommandHandler("test_key", "data/test.json")

        # Capture logs
        with self.assertLogs('backend.handlers', level=logging.DEBUG) as cm:
            result = handler.handle_add(["Dune"])

        # Verify logging occurred
        log_text = '\n'.join(cm.output).lower()
        self.assertTrue(
            "dune" in log_text or "438632" in log_text,
            f"Expected log output to contain 'dune' or '438632', but got: {cm.output}"
        )

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_add_director(self, mock_tmdb_class, mock_storage_class):
        """Test adding a director successfully"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock director ID
        mock_tmdb.get_director_id.return_value = 3179

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_add_director(["Quentin Tarantino"])

        # Verify response
        self.assertIn("Monitoreando a Quentin Tarantino", result)
        self.assertIn("🎬", result)
        self.assertIn("/remove", result)

        # Verify stored
        mock_storage.add_director.assert_called_once_with("Quentin Tarantino", 3179)

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_add_director_not_found(self, mock_tmdb_class, mock_storage_class):
        """Test adding director when not found"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock no director found
        mock_tmdb.get_director_id.return_value = None

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_add_director(["UnknownDirector"])

        # Verify error response
        self.assertIn("❌", result)
        self.assertIn("No encontré", result)
        mock_storage.add_director.assert_not_called()

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_list_shows_directors(self, mock_tmdb_class, mock_storage_class):
        """Test that /list shows directors"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock data with directors
        mock_storage.get_movies.return_value = [
            {"title": "Dune", "id": 438631, "type": "movie"}
        ]
        mock_storage.get_actors.return_value = [
            {"name": "Brad Pitt", "id": 287}
        ]
        mock_storage.get_directors.return_value = [
            {"name": "Quentin Tarantino", "id": 3179}
        ]

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_list()

        # Verify directors are shown
        self.assertIn("Brad Pitt", result)
        self.assertIn("Quentin Tarantino", result)
        self.assertIn("Directores Monitoreados", result)
        self.assertIn("🎬", result)

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_remove_director(self, mock_tmdb_class, mock_storage_class):
        """Test removing a director"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock find and remove
        mock_storage.get_movies.return_value = []
        mock_storage.get_actors.return_value = []
        mock_storage.get_directors.return_value = [
            {"name": "Quentin Tarantino", "id": 3179}
        ]
        mock_storage.remove_director.return_value = True

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_remove(["Quentin Tarantino"])

        # Verify
        self.assertIn("✅", result)
        self.assertIn("removida", result)
        self.assertIn("Quentin Tarantino", result)
        mock_storage.remove_director.assert_called_once()


if __name__ == "__main__":
    unittest.main()
