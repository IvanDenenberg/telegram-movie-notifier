import unittest
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
        mock_storage.add_movie.assert_called_once_with("Dune", 438631)

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
            {"title": "Dune", "id": 438631}
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


if __name__ == "__main__":
    unittest.main()
