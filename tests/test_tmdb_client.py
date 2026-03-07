import unittest
from unittest.mock import patch, MagicMock
from backend.tmdb_client import TMDbClient
from backend.http_client import RequestManager


class TestTMDbClient(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_api_key_12345"
        self.client = TMDbClient(self.api_key)

    @patch('backend.http_client.RequestManager.get')
    def test_search_movie(self, mock_get):
        """Test successful movie search"""
        mock_get.return_value = {
            "results": [
                {
                    "id": 550,
                    "title": "Fight Club",
                    "release_date": "1999-10-15"
                }
            ]
        }

        result = self.client.search_movie("Fight Club")

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 550)
        self.assertEqual(result["title"], "Fight Club")
        mock_get.assert_called_once()

    @patch('backend.http_client.RequestManager.get')
    def test_search_movie_not_found(self, mock_get):
        """Test movie search when not found"""
        mock_get.return_value = {"results": []}

        result = self.client.search_movie("NonexistentMovieXYZ123")

        self.assertIsNone(result)

    @patch('backend.http_client.RequestManager.get')
    def test_get_actor_id(self, mock_get):
        """Test getting actor ID"""
        mock_get.return_value = {
            "results": [
                {
                    "id": 287,
                    "name": "Brad Pitt"
                }
            ]
        }

        result = self.client.get_actor_id("Brad Pitt")

        self.assertIsNotNone(result)
        self.assertEqual(result, 287)
        mock_get.assert_called_once()

    @patch('backend.http_client.RequestManager.get')
    def test_get_actor_filmography(self, mock_get):
        """Test getting actor filmography"""
        mock_get.return_value = {
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

        result = self.client.get_actor_filmography(287)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], "Fight Club")
        mock_get.assert_called_once()

    @patch('backend.http_client.RequestManager.get')
    def test_search_tv(self, mock_get):
        """Test TV show search"""
        mock_get.return_value = {
            "results": [
                {
                    "id": 1399,
                    "name": "Breaking Bad",
                    "first_air_date": "2008-01-20"
                }
            ]
        }

        result = self.client.search_tv("Breaking Bad")

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 1399)
        self.assertEqual(result["name"], "Breaking Bad")

    @patch('backend.http_client.RequestManager.get')
    def test_search_tv_not_found(self, mock_get):
        """Test TV show search when not found"""
        mock_get.return_value = {"results": []}

        result = self.client.search_tv("NonexistentShowXYZ123")

        self.assertIsNone(result)

    @patch('backend.http_client.RequestManager.get')
    def test_get_actor_tv_credits(self, mock_get):
        """Test getting actor TV credits"""
        mock_get.return_value = {
            "cast": [
                {
                    "id": 1399,
                    "name": "Breaking Bad",
                    "first_air_date": "2008-01-20"
                }
            ]
        }

        result = self.client.get_actor_tv_credits(287)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Breaking Bad")

    @patch('backend.http_client.RequestManager.get')
    def test_get_upcoming_releases(self, mock_get):
        """Test getting upcoming movie releases"""
        mock_get.return_value = {
            "results": [
                {
                    "id": 603,
                    "title": "The Matrix Reloaded",
                    "release_date": "2025-05-20"
                }
            ]
        }

        result = self.client.get_upcoming_releases()

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "The Matrix Reloaded")

    @patch('backend.http_client.RequestManager.get')
    def test_get_actor_id_not_found(self, mock_get):
        """Test getting actor ID when not found"""
        mock_get.return_value = {"results": []}

        result = self.client.get_actor_id("UnknownActorXYZ")

        self.assertIsNone(result)

    @patch('backend.http_client.RequestManager.get')
    def test_api_request_error(self, mock_get):
        """Test handling API request errors"""
        mock_get.return_value = None

        result = self.client.search_movie("Test Movie")

        self.assertIsNone(result)

    @patch('backend.http_client.RequestManager.get')
    def test_get_actor_filmography_empty(self, mock_get):
        """Test getting actor filmography when empty"""
        mock_get.return_value = {"cast": []}

        result = self.client.get_actor_filmography(287)

        self.assertEqual(result, [])

    @patch('backend.http_client.RequestManager.get')
    def test_get_actor_tv_credits_empty(self, mock_get):
        """Test getting actor TV credits when empty"""
        mock_get.return_value = {"cast": []}

        result = self.client.get_actor_tv_credits(287)

        self.assertEqual(result, [])

    @patch('backend.http_client.RequestManager.get')
    def test_get_upcoming_releases_empty(self, mock_get):
        """Test getting upcoming releases when empty"""
        mock_get.return_value = {"results": []}

        result = self.client.get_upcoming_releases()

        self.assertEqual(result, [])

    @patch('backend.http_client.RequestManager.get')
    def test_search_movie_uses_secure_headers(self, mock_get):
        """Test que search_movie usa headers seguros, no parámetros"""
        mock_get.return_value = {
            "results": [
                {"id": 438632, "title": "Dune", "release_date": "2024-02-14"}
            ]
        }

        client = TMDbClient("fake_key")
        result = client.search_movie("Dune")

        # Verificar que se usó RequestManager.get
        assert mock_get.called

        # Verificar que headers contiene Authorization
        call_kwargs = mock_get.call_args[1]
        assert "headers" in call_kwargs
        assert "Authorization" in call_kwargs["headers"]
        assert "Bearer fake_key" in call_kwargs["headers"]["Authorization"]

        # Verificar que api_key NO está en params
        assert "api_key" not in call_kwargs.get("params", {})


if __name__ == "__main__":
    unittest.main()
