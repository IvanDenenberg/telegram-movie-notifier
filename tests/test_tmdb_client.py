import unittest
from unittest.mock import patch, MagicMock
from backend.tmdb_client import TMDbClient


class TestTMDbClient(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_api_key_12345"
        self.client = TMDbClient(self.api_key)

    @patch('backend.tmdb_client.requests.get')
    def test_search_movie(self, mock_get):
        """Test successful movie search"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": 550,
                    "title": "Fight Club",
                    "release_date": "1999-10-15"
                }
            ]
        }
        mock_get.return_value = mock_response

        result = self.client.search_movie("Fight Club")

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 550)
        self.assertEqual(result["title"], "Fight Club")
        mock_get.assert_called_once()

    @patch('backend.tmdb_client.requests.get')
    def test_search_movie_not_found(self, mock_get):
        """Test movie search when not found"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        result = self.client.search_movie("NonexistentMovieXYZ123")

        self.assertIsNone(result)

    @patch('backend.tmdb_client.requests.get')
    def test_get_actor_id(self, mock_get):
        """Test getting actor ID"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": 287,
                    "name": "Brad Pitt"
                }
            ]
        }
        mock_get.return_value = mock_response

        result = self.client.get_actor_id("Brad Pitt")

        self.assertIsNotNone(result)
        self.assertEqual(result, 287)
        mock_get.assert_called_once()

    @patch('backend.tmdb_client.requests.get')
    def test_get_actor_filmography(self, mock_get):
        """Test getting actor filmography"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cast": [
                {
                    "id": 550,
                    "title": "Fight Club",
                    "release_date": "1999-10-15"
                },
                {
                    "id": 278,
                    "title": "The Shawshank Redemption",
                    "release_date": "1994-09-23"
                }
            ]
        }
        mock_get.return_value = mock_response

        result = self.client.get_actor_filmography(287)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], "Fight Club")
        mock_get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
