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
    def test_get_actor_id_multi_word_prefers_all_words(self, mock_get):
        """Test that multi-word actor search prefers results with all keywords"""
        # Simulates searching for "Anya Taylor-Joy" when multiple "Anya" results exist
        mock_get.return_value = {
            "results": [
                {
                    "id": 1234,
                    "name": "Anya",
                    "popularity": 5.0,
                    "known_for_department": "Acting"
                },
                {
                    "id": 5678,
                    "name": "Anya Taylor-Joy",
                    "popularity": 50.0,  # More popular
                    "known_for_department": "Acting"
                }
            ]
        }

        result = self.client.get_actor_id("Anya Taylor-Joy")

        # Should return the one with both words, not the first one
        self.assertEqual(result, 5678)

    @patch('backend.http_client.RequestManager.get')
    def test_search_movie_multi_word_prefers_all_words(self, mock_get):
        """Test that multi-word movie search prefers results with all keywords"""
        mock_get.return_value = {
            "results": [
                {
                    "id": 1111,
                    "title": "The Lord",
                    "release_date": "2020-01-01",
                    "popularity": 5.0
                },
                {
                    "id": 2222,
                    "title": "The Lord of the Rings",
                    "release_date": "2001-12-19",
                    "popularity": 100.0  # More popular
                }
            ]
        }

        result = self.client.search_movie("The Lord of the Rings")

        # Should return the one with all three words, not the first one
        self.assertEqual(result["id"], 2222)
        self.assertEqual(result["title"], "The Lord of the Rings")

    @patch('backend.http_client.RequestManager.get')
    def test_search_tv_prefers_most_popular(self, mock_get):
        """Test that TV search prefers most popular result on fallback"""
        mock_get.return_value = {
            "results": [
                {
                    "id": 3333,
                    "name": "Breaking Bad",
                    "first_air_date": "2008-01-20",
                    "popularity": 20.0
                },
                {
                    "id": 4444,
                    "name": "Better Call Saul",
                    "first_air_date": "2015-02-09",
                    "popularity": 50.0  # More popular
                }
            ]
        }

        result = self.client.search_tv("Breaking")

        # Should return the first prefix match
        self.assertEqual(result["id"], 3333)

    @patch('backend.http_client.RequestManager.get')
    def test_search_movie_fallback_uses_popularity(self, mock_get):
        """Test that movie search fallback uses most popular result"""
        mock_get.return_value = {
            "results": [
                {
                    "id": 5555,
                    "title": "Avatar",
                    "release_date": "2009-12-18",
                    "popularity": 10.0
                },
                {
                    "id": 6666,
                    "title": "Avatar: The Way of Water",
                    "release_date": "2022-12-16",
                    "popularity": 100.0  # More popular
                },
                {
                    "id": 7777,
                    "title": "Avatars of Kali",
                    "release_date": "2006-01-01",
                    "popularity": 2.0
                }
            ]
        }

        result = self.client.search_movie("Avatar Legends")

        # Should return most popular as fallback (none match all words)
        self.assertEqual(result["id"], 6666)

    @patch('backend.http_client.RequestManager.get')
    def test_search_movie_filters_by_year(self, mock_get):
        """Test that movie search filters by year when provided"""
        mock_get.return_value = {
            "results": [
                {
                    "id": 8888,
                    "title": "Vladimir",
                    "release_date": "2020-03-15",
                    "popularity": 50.0
                },
                {
                    "id": 9999,
                    "title": "Vladimir",
                    "release_date": "2026-06-20",
                    "popularity": 30.0
                }
            ]
        }

        result = self.client.search_movie("Vladimir 2026")

        # Should return 2026 release, not the more popular 2020 one
        self.assertEqual(result["id"], 9999)
        self.assertTrue(result["release_date"].startswith("2026"))

    @patch('backend.http_client.RequestManager.get')
    def test_search_tv_filters_by_year(self, mock_get):
        """Test that TV search filters by year when provided"""
        mock_get.return_value = {
            "results": [
                {
                    "id": 1111,
                    "name": "Breaking Bad",
                    "first_air_date": "2008-01-20",
                    "popularity": 100.0
                },
                {
                    "id": 2222,
                    "name": "Breaking Bad",
                    "first_air_date": "2025-03-15",
                    "popularity": 20.0
                }
            ]
        }

        result = self.client.search_tv("Breaking Bad 2025")

        # Should return 2025 release, not the more popular 2008 one
        self.assertEqual(result["id"], 2222)
        self.assertTrue(result["first_air_date"].startswith("2025"))

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

    @patch('backend.http_client.RequestManager.get')
    def test_get_director_id(self, mock_get):
        """Test getting director ID by name"""
        mock_get.return_value = {
            "results": [
                {
                    "id": 3179,
                    "name": "Quentin Tarantino",
                    "known_for_department": "Directing"
                }
            ]
        }

        result = self.client.get_director_id("Quentin Tarantino")

        self.assertIsNotNone(result)
        self.assertEqual(result, 3179)
        mock_get.assert_called_once()

    @patch('backend.http_client.RequestManager.get')
    def test_get_director_id_multi_word(self, mock_get):
        """Test that director search prefers results with all keywords"""
        mock_get.return_value = {
            "results": [
                {
                    "id": 1234,
                    "name": "John",
                    "popularity": 5.0,
                    "known_for_department": "Directing"
                },
                {
                    "id": 5678,
                    "name": "John Hughes",
                    "popularity": 50.0,
                    "known_for_department": "Directing"
                }
            ]
        }

        result = self.client.get_director_id("John Hughes")

        self.assertEqual(result, 5678)

    @patch('backend.http_client.RequestManager.get')
    def test_get_director_filmography(self, mock_get):
        """Test getting director's filmography filtered by Director job"""
        mock_get.return_value = {
            "cast": [
                {
                    "id": 550,
                    "title": "Fight Club",
                    "release_date": "1999-10-15",
                    "job": "Actor"  # Should be filtered out
                }
            ],
            "crew": [
                {
                    "id": 550,
                    "title": "Fight Club",
                    "release_date": "1999-10-15",
                    "job": "Director"  # Should be included
                },
                {
                    "id": 278,
                    "title": "The Shawshank Redemption",
                    "release_date": "1994-09-23",
                    "job": "Director"  # Should be included
                }
            ]
        }

        result = self.client.get_director_filmography(3179)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["title"], "Fight Club")
        self.assertEqual(result[1]["title"], "The Shawshank Redemption")

    @patch('backend.http_client.RequestManager.get')
    def test_get_director_tv_credits(self, mock_get):
        """Test getting director's TV credits filtered by Director job"""
        mock_get.return_value = {
            "crew": [
                {
                    "id": 1399,
                    "name": "Breaking Bad",
                    "first_air_date": "2008-01-20",
                    "job": "Director"
                },
                {
                    "id": 1396,
                    "name": "Better Call Saul",
                    "first_air_date": "2015-02-09",
                    "job": "Producer"  # Should be filtered out
                }
            ]
        }

        result = self.client.get_director_tv_credits(3179)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Breaking Bad")



if __name__ == "__main__":
    unittest.main()


# Pytest-style test for logging
def test_search_movie_logs_query(caplog):
    """Test that search_movie logs debug output"""
    import logging
    with patch('backend.http_client.RequestManager.get') as mock_get:
        client = TMDbClient("test_key")
        mock_get.return_value = {
            "results": [{"title": "Dune", "id": 438632, "release_date": "2021-10-01"}]
        }

        with caplog.at_level(logging.DEBUG):
            result = client.search_movie("Dune")

        assert "search_movie" in caplog.text.lower() or "dune" in caplog.text.lower()
