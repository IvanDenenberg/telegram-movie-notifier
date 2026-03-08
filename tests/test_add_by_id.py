import unittest
from unittest.mock import patch, MagicMock
from backend.handlers import CommandHandler


class TestAddById(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_api_key_12345"
        self.storage_path = "test_data/test_movies.json"

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_add_by_id_movie(self, mock_tmdb_class, mock_storage_class):
        """Test adding a movie by TMDb ID"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        mock_tmdb.get_movie_by_id.return_value = {
            "title": "Dune",
            "id": 438632,
            "release_date": "2021-10-01"
        }

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_add_by_id(["438632"])

        self.assertIn("✅", result)
        self.assertIn("Dune", result)
        mock_storage.add_movie.assert_called_once()

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_add_by_id_tv(self, mock_tmdb_class, mock_storage_class):
        """Test adding a TV show by TMDb ID"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        mock_tmdb.get_tv_by_id.return_value = {
            "name": "Breaking Bad",
            "id": 1396,
            "first_air_date": "2008-01-20"
        }

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_add_by_id(["1396", "tv"])

        self.assertIn("✅", result)
        self.assertIn("Breaking Bad", result)
        mock_storage.add_movie.assert_called_with("Breaking Bad", 1396, media_type="tv")

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_add_by_id_invalid_format(self, mock_tmdb_class, mock_storage_class):
        """Test adding by ID with no arguments"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_add_by_id([])

        self.assertIn("❌", result)

    @patch('backend.handlers.Storage')
    @patch('backend.handlers.TMDbClient')
    def test_add_by_id_not_found(self, mock_tmdb_class, mock_storage_class):
        """Test adding by ID when item not found"""
        mock_tmdb = MagicMock()
        mock_tmdb_class.return_value = mock_tmdb
        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        mock_tmdb.get_movie_by_id.return_value = None

        handler = CommandHandler(self.api_key, self.storage_path)
        result = handler.handle_add_by_id(["999999"])

        self.assertIn("❌", result)


if __name__ == "__main__":
    unittest.main()
