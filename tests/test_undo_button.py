import unittest
import logging
from unittest.mock import patch, MagicMock
from backend.handlers import CommandHandler


class TestUndoButton(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_api_key_12345"
        self.storage_path = "test_data/test_movies.json"

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_add_movie_returns_undo_metadata(self, mock_tmdb_class, mock_storage_class):
        """Test that /add_movie command returns undo metadata"""
        # Setup mocks
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock search result for movie
        mock_tmdb.search_movie.return_value = {
            "id": 438632,
            "title": "Dune",
            "release_date": "2021-10-01"
        }

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_add_movie(["Dune"])

        # Result should contain success marker and undo metadata
        self.assertIn("✅", result)
        self.assertIn("Dune", result)
        self.assertIn("|||UNDO_BUTTON||", result)
        self.assertIn('/remove "Dune"', result)

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_add_movie_tv_returns_undo_metadata(self, mock_tmdb_class, mock_storage_class):
        """Test that /add_movie command returns undo metadata for TV shows"""
        # Setup mocks
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock no movie result but TV result
        mock_tmdb.search_movie.return_value = None
        mock_tmdb.get_search_results.return_value = []
        mock_tmdb.search_tv.return_value = {
            "id": 1234,
            "name": "Breaking Bad",
            "first_air_date": "2008-01-20"
        }

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_add_movie(["Breaking Bad"])

        # Result should contain success marker and undo metadata
        self.assertIn("✅", result)
        self.assertIn("Breaking Bad", result)
        self.assertIn("|||UNDO_BUTTON||", result)
        self.assertIn('/remove "Breaking Bad"', result)

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_add_actor_returns_undo_metadata(self, mock_tmdb_class, mock_storage_class):
        """Test that /add_actor command returns undo metadata"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock actor ID
        mock_tmdb.get_actor_id.return_value = 500

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_add_actor(["Tom Cruise"])

        # Result should contain success marker and undo metadata
        self.assertIn("✅", result)
        self.assertIn("Tom Cruise", result)
        self.assertIn("|||UNDO_BUTTON||", result)
        self.assertIn('/remove "Tom Cruise"', result)

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_add_movie_by_id_movie_returns_undo_metadata(self, mock_tmdb_class, mock_storage_class):
        """Test that /add_movie_by_id command returns undo metadata for movies"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock movie by ID
        mock_tmdb.get_movie_by_id.return_value = {
            "id": 438632,
            "title": "Dune",
            "release_date": "2021-10-01"
        }

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_add_movie_by_id(["438632"])

        # Result should contain success marker and undo metadata
        self.assertIn("✅", result)
        self.assertIn("Dune", result)
        self.assertIn("|||UNDO_BUTTON||", result)
        self.assertIn('/remove "Dune"', result)

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_handle_add_movie_by_id_tv_returns_undo_metadata(self, mock_tmdb_class, mock_storage_class):
        """Test that /add_movie_by_id command returns undo metadata for TV shows"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock TV show by ID
        mock_tmdb.get_tv_by_id.return_value = {
            "id": 1234,
            "name": "Breaking Bad",
            "first_air_date": "2008-01-20"
        }

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_add_movie_by_id(["1234", "tv"])

        # Result should contain success marker and undo metadata
        self.assertIn("✅", result)
        self.assertIn("Breaking Bad", result)
        self.assertIn("|||UNDO_BUTTON||", result)
        self.assertIn('/remove "Breaking Bad"', result)

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_undo_button_click_removes_item(self, mock_tmdb_class, mock_storage_class):
        """Test that clicking undo button removes the item"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        # Mock find and remove
        mock_storage.get_movies.return_value = [
            {"title": "Dune", "id": 438632}
        ]
        mock_storage.get_actors.return_value = []
        mock_storage.remove_movie.return_value = True

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_remove(["Dune"])

        # Should trigger removal response
        self.assertIn("✅", result)
        self.assertIn("removida", result)
        mock_storage.remove_movie.assert_called_once()


if __name__ == "__main__":
    unittest.main()
