import logging
import re
from typing import Optional, Dict, List, Tuple
from backend.http_client import RequestManager


class TMDbClient:
    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(self, api_key: str):
        """Initialize TMDb client with API key"""
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.request_manager = RequestManager(timeout=5)

    def _extract_year_from_search(self, search_text: str) -> Tuple[str, Optional[str]]:
        """Extract year from search text. Returns (cleaned_text, year) where year is YYYY format or None"""
        # Match 4-digit year between 1900 and 2099
        year_match = re.search(r'\b([12]\d{3})\b', search_text)
        if year_match:
            year = year_match.group(1)
            # Remove year from text
            cleaned = re.sub(r'\b' + year + r'\b', '', search_text).strip()
            return cleaned, year
        return search_text.strip(), None

    def _match_year(self, date_string: str, year: str) -> bool:
        """Check if a date string (YYYY-MM-DD) matches the target year"""
        if not date_string or not year:
            return False
        return date_string.startswith(year)

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make HTTP request to TMDb API with secure headers"""
        if params is None:
            params = {}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        url = f"{self.BASE_URL}{endpoint}"
        return self.request_manager.get(url, params=params, headers=headers)

    def search_movie(self, title: str) -> Optional[Dict]:
        """Search for a movie by title - prefers exact matches, then most popular. Supports year filtering."""
        self.logger.debug(f"[SEARCH_MOVIE] Querying TMDb for: {title}")

        # Extract year from search if present
        search_without_year, target_year = self._extract_year_from_search(title)
        if target_year:
            self.logger.debug(f"[SEARCH_MOVIE] Year filter detected: {target_year}")

        # Use search_without_year for API query if year was found, otherwise use original title
        api_query = search_without_year if search_without_year else title
        data = self._make_request("/search/movie", {"query": api_query})
        if not data or "results" not in data or not data["results"]:
            self.logger.debug(f"[SEARCH_MOVIE] No results found for: {title}")
            return None

        self.logger.debug(f"[SEARCH_MOVIE] Found {len(data['results'])} results")

        # Normalize search title for comparison
        search_title_lower = title.lower().strip()
        search_without_year_lower = search_without_year.lower().strip()
        search_words = set(search_without_year_lower.split()) if search_without_year_lower else set()

        # First pass: look for exact title match
        for result in data["results"]:
            if result.get("title") and result.get("release_date"):
                result_title_lower = result["title"].lower().strip()
                if result_title_lower == search_title_lower:
                    self.logger.debug(f"[SEARCH_MOVIE] Exact match found: {result['title']} (ID: {result.get('id')})")
                    return result

        # Second pass: look for titles containing all search words (multi-word matches), optionally filter by year
        candidates = []
        for result in data["results"]:
            if result.get("title") and result.get("release_date"):
                result_title_lower = result["title"].lower().strip()
                result_words = set(result_title_lower.split())

                # Check if all search words are in result title
                if search_words and search_words.issubset(result_words):
                    # If year filter exists, only consider results from that year
                    if target_year and not self._match_year(result.get("release_date", ""), target_year):
                        continue

                    popularity = result.get("popularity", 0)
                    candidates.append((popularity, result))

        if candidates:
            # Sort by popularity (descending) and take the most popular
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_match = candidates[0][1]
            self.logger.debug(f"[SEARCH_MOVIE] Multi-word match found: {best_match['title']} (ID: {best_match.get('id')}, popularity: {best_match.get('popularity')})")
            return best_match

        # Third pass: look for titles starting with search term (without year part)
        for result in data["results"]:
            if result.get("title") and result.get("release_date"):
                result_title_lower = result["title"].lower().strip()
                if search_without_year_lower and result_title_lower.startswith(search_without_year_lower):
                    # If year filter exists, only consider results from that year
                    if target_year and not self._match_year(result.get("release_date", ""), target_year):
                        continue
                    self.logger.debug(f"[SEARCH_MOVIE] Prefix match found: {result['title']} (ID: {result.get('id')})")
                    return result

        # Fall back to most popular valid result
        best_result = None
        best_popularity = -1
        for result in data["results"]:
            if result.get("title") and result.get("release_date"):
                # If year filter exists, only consider results from that year
                if target_year and not self._match_year(result.get("release_date", ""), target_year):
                    continue

                popularity = result.get("popularity", 0)
                if popularity > best_popularity:
                    best_popularity = popularity
                    best_result = result

        if best_result:
            self.logger.debug(f"[SEARCH_MOVIE] Using most popular result: {best_result['title']} (ID: {best_result.get('id')}, popularity: {best_popularity})")
            return best_result

        self.logger.debug(f"[SEARCH_MOVIE] No valid results for: {title}")
        return None

    def search_tv(self, title: str) -> Optional[Dict]:
        """Search for a TV show by title - prefers exact matches, then most popular. Supports year filtering."""
        self.logger.debug(f"[SEARCH_TV] Querying TMDb for: {title}")

        # Extract year from search if present
        search_without_year, target_year = self._extract_year_from_search(title)
        if target_year:
            self.logger.debug(f"[SEARCH_TV] Year filter detected: {target_year}")

        # Use search_without_year for API query if year was found, otherwise use original title
        api_query = search_without_year if search_without_year else title
        data = self._make_request("/search/tv", {"query": api_query})
        if not data or "results" not in data or not data["results"]:
            self.logger.debug(f"[SEARCH_TV] No results found for: {title}")
            return None

        self.logger.debug(f"[SEARCH_TV] Found {len(data['results'])} results")

        # Normalize search title for comparison
        search_title_lower = title.lower().strip()
        search_without_year_lower = search_without_year.lower().strip()
        search_words = set(search_without_year_lower.split()) if search_without_year_lower else set()

        # First pass: look for exact title match
        for result in data["results"]:
            if result.get("name") and result.get("first_air_date"):
                result_name_lower = result["name"].lower().strip()
                if result_name_lower == search_title_lower:
                    self.logger.debug(f"[SEARCH_TV] Exact match found: {result['name']} (ID: {result.get('id')})")
                    return result

        # Second pass: look for titles containing all search words (multi-word matches), optionally filter by year
        candidates = []
        for result in data["results"]:
            if result.get("name") and result.get("first_air_date"):
                result_name_lower = result["name"].lower().strip()
                result_words = set(result_name_lower.split())

                # Check if all search words are in result name
                if search_words and search_words.issubset(result_words):
                    # If year filter exists, only consider results from that year
                    if target_year and not self._match_year(result.get("first_air_date", ""), target_year):
                        continue

                    popularity = result.get("popularity", 0)
                    candidates.append((popularity, result))

        if candidates:
            # Sort by popularity (descending) and take the most popular
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_match = candidates[0][1]
            self.logger.debug(f"[SEARCH_TV] Multi-word match found: {best_match['name']} (ID: {best_match.get('id')}, popularity: {best_match.get('popularity')})")
            return best_match

        # Third pass: look for titles starting with search term (without year part)
        for result in data["results"]:
            if result.get("name") and result.get("first_air_date"):
                result_name_lower = result["name"].lower().strip()
                if search_without_year_lower and result_name_lower.startswith(search_without_year_lower):
                    # If year filter exists, only consider results from that year
                    if target_year and not self._match_year(result.get("first_air_date", ""), target_year):
                        continue
                    self.logger.debug(f"[SEARCH_TV] Prefix match found: {result['name']} (ID: {result.get('id')})")
                    return result

        # Fall back to most popular valid result
        best_result = None
        best_popularity = -1
        for result in data["results"]:
            if result.get("name") and result.get("first_air_date"):
                # If year filter exists, only consider results from that year
                if target_year and not self._match_year(result.get("first_air_date", ""), target_year):
                    continue

                popularity = result.get("popularity", 0)
                if popularity > best_popularity:
                    best_popularity = popularity
                    best_result = result

        if best_result:
            self.logger.debug(f"[SEARCH_TV] Using most popular result: {best_result['name']} (ID: {best_result.get('id')}, popularity: {best_popularity})")
            return best_result

        self.logger.debug(f"[SEARCH_TV] No valid results for: {title}")
        return None

    def get_search_results(self, title: str, media_type: str = "movie") -> List[Dict]:
        """Get top search results without filtering"""
        endpoint = f"/search/{media_type}"
        self.logger.debug(f"[GET_SEARCH_RESULTS] Getting raw results for: {title} ({media_type})")

        data = self._make_request(endpoint, {"query": title})
        if not data or "results" not in data:
            return []

        results = []
        key_name = "title" if media_type == "movie" else "name"
        key_date = "release_date" if media_type == "movie" else "first_air_date"

        for result in data["results"]:
            if result.get(key_name) and result.get(key_date):
                results.append(result)
                if len(results) >= 3:  # Limit to top 3
                    break

        self.logger.debug(f"[GET_SEARCH_RESULTS] Returning {len(results)} results")
        return results

    def get_actor_id(self, actor_name: str) -> Optional[int]:
        """Get actor ID by name - prefers exact matches, then most popular"""
        self.logger.debug(f"[GET_ACTOR_ID] Searching for actor: {actor_name}")

        data = self._make_request("/search/person", {"query": actor_name})
        if not data or "results" not in data or not data["results"]:
            self.logger.debug(f"[GET_ACTOR_ID] No results for: {actor_name}")
            return None

        self.logger.debug(f"[GET_ACTOR_ID] Found {len(data['results'])} results")

        # Normalize search name for comparison
        search_name_lower = actor_name.lower().strip()
        search_words = set(search_name_lower.split())

        # First pass: look for exact name match
        for result in data["results"]:
            if result.get("name"):
                result_name_lower = result["name"].lower().strip()
                if result_name_lower == search_name_lower:
                    self.logger.debug(f"[GET_ACTOR_ID] Exact match found: {result['name']} (ID: {result.get('id')})")
                    return result.get("id")

        # Second pass: look for names containing all search words (multi-word matches)
        candidates = []
        for result in data["results"]:
            if result.get("name") and result.get("id"):
                result_name_lower = result["name"].lower().strip()
                result_words = set(result_name_lower.split())
                # Check if all search words are in result name
                if search_words.issubset(result_words):
                    popularity = result.get("popularity", 0)
                    candidates.append((popularity, result))

        if candidates:
            # Sort by popularity (descending) and take the most popular
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_match = candidates[0][1]
            self.logger.debug(f"[GET_ACTOR_ID] Multi-word match found: {best_match['name']} (ID: {best_match.get('id')}, popularity: {best_match.get('popularity')})")
            return best_match.get("id")

        # Third pass: look for names starting with search term
        for result in data["results"]:
            if result.get("name"):
                result_name_lower = result["name"].lower().strip()
                if result_name_lower.startswith(search_name_lower):
                    self.logger.debug(f"[GET_ACTOR_ID] Prefix match found: {result['name']} (ID: {result.get('id')})")
                    return result.get("id")

        # Fall back to most popular result with known_for_department
        best_result = None
        best_popularity = -1
        for result in data["results"]:
            if result.get("id") and result.get("known_for_department"):
                popularity = result.get("popularity", 0)
                if popularity > best_popularity:
                    best_popularity = popularity
                    best_result = result

        if best_result:
            self.logger.debug(f"[GET_ACTOR_ID] Using most popular result: {best_result['name']} (ID: {best_result.get('id')}, popularity: {best_popularity})")
            return best_result.get("id")

        # Last resort: most popular result with ID
        best_result = None
        best_popularity = -1
        for result in data["results"]:
            if result.get("id"):
                popularity = result.get("popularity", 0)
                if popularity > best_popularity:
                    best_popularity = popularity
                    best_result = result

        if best_result:
            self.logger.debug(f"[GET_ACTOR_ID] Using most popular result (last resort): {best_result.get('name')} (ID: {best_result['id']}, popularity: {best_popularity})")
            return best_result.get("id")

        self.logger.debug(f"[GET_ACTOR_ID] No valid results for: {actor_name}")
        return None

    def get_director_id(self, director_name: str) -> Optional[int]:
        """Get director ID by name - prefers exact matches, then most popular"""
        self.logger.debug(f"[GET_DIRECTOR_ID] Searching for director: {director_name}")

        data = self._make_request("/search/person", {"query": director_name})
        if not data or "results" not in data or not data["results"]:
            self.logger.debug(f"[GET_DIRECTOR_ID] No results for: {director_name}")
            return None

        self.logger.debug(f"[GET_DIRECTOR_ID] Found {len(data['results'])} results")

        # Normalize search name for comparison
        search_name_lower = director_name.lower().strip()
        search_words = set(search_name_lower.split())

        # First pass: look for exact name match
        for result in data["results"]:
            if result.get("name"):
                result_name_lower = result["name"].lower().strip()
                if result_name_lower == search_name_lower:
                    self.logger.debug(f"[GET_DIRECTOR_ID] Exact match found: {result['name']} (ID: {result.get('id')})")
                    return result.get("id")

        # Second pass: look for names containing all search words (multi-word matches)
        candidates = []
        for result in data["results"]:
            if result.get("name") and result.get("id"):
                result_name_lower = result["name"].lower().strip()
                result_words = set(result_name_lower.split())
                # Check if all search words are in result name
                if search_words.issubset(result_words):
                    popularity = result.get("popularity", 0)
                    candidates.append((popularity, result))

        if candidates:
            # Sort by popularity (descending) and take the most popular
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_match = candidates[0][1]
            self.logger.debug(f"[GET_DIRECTOR_ID] Multi-word match found: {best_match['name']} (ID: {best_match.get('id')}, popularity: {best_match.get('popularity')})")
            return best_match.get("id")

        # Third pass: look for names starting with search term
        for result in data["results"]:
            if result.get("name"):
                result_name_lower = result["name"].lower().strip()
                if result_name_lower.startswith(search_name_lower):
                    self.logger.debug(f"[GET_DIRECTOR_ID] Prefix match found: {result['name']} (ID: {result.get('id')})")
                    return result.get("id")

        # Fall back to most popular result with known_for_department
        best_result = None
        best_popularity = -1
        for result in data["results"]:
            if result.get("id") and result.get("known_for_department"):
                popularity = result.get("popularity", 0)
                if popularity > best_popularity:
                    best_popularity = popularity
                    best_result = result

        if best_result:
            self.logger.debug(f"[GET_DIRECTOR_ID] Using most popular result: {best_result['name']} (ID: {best_result.get('id')}, popularity: {best_popularity})")
            return best_result.get("id")

        # Last resort: most popular result with ID
        best_result = None
        best_popularity = -1
        for result in data["results"]:
            if result.get("id"):
                popularity = result.get("popularity", 0)
                if popularity > best_popularity:
                    best_popularity = popularity
                    best_result = result

        if best_result:
            self.logger.debug(f"[GET_DIRECTOR_ID] Using most popular result (last resort): {best_result.get('name')} (ID: {best_result['id']}, popularity: {best_popularity})")
            return best_result.get("id")

        self.logger.debug(f"[GET_DIRECTOR_ID] No valid results for: {director_name}")
        return None

    def get_actor_filmography(self, actor_id: int) -> List[Dict]:
        """Get actor's movie filmography"""
        data = self._make_request(
            f"/person/{actor_id}/movie_credits",
            {}
        )
        if not data or "cast" not in data:
            return []

        # Filter for valid results (with title and release_date)
        filmography = []
        for movie in data["cast"]:
            if movie.get("title") and movie.get("release_date"):
                filmography.append(movie)

        return filmography

    def get_actor_tv_credits(self, actor_id: int) -> List[Dict]:
        """Get actor's TV show credits"""
        data = self._make_request(
            f"/person/{actor_id}/tv_credits",
            {}
        )
        if not data or "cast" not in data:
            return []

        # Filter for valid results (with name and first_air_date)
        tv_credits = []
        for show in data["cast"]:
            if show.get("name") and show.get("first_air_date"):
                tv_credits.append(show)

        return tv_credits

    def get_upcoming_releases(self, page: int = 1) -> List[Dict]:
        """Get upcoming movie releases"""
        data = self._make_request(
            "/movie/upcoming",
            {"page": page}
        )
        if not data or "results" not in data:
            return []

        # Filter for valid results (with title and release_date)
        releases = []
        for movie in data["results"]:
            if movie.get("title") and movie.get("release_date"):
                releases.append(movie)

        return releases

    def get_movie_by_id(self, movie_id: int) -> Optional[Dict]:
        """Get movie details by TMDb ID"""
        self.logger.debug(f"[GET_MOVIE_BY_ID] Fetching movie ID: {movie_id}")
        data = self._make_request(f"/movie/{movie_id}", {})

        if not data:
            self.logger.debug(f"[GET_MOVIE_BY_ID] Movie not found: {movie_id}")
            return None

        if data.get("title") and data.get("release_date"):
            self.logger.debug(f"[GET_MOVIE_BY_ID] Found: {data.get('title')}")
            return data

        self.logger.debug(f"[GET_MOVIE_BY_ID] Movie missing required fields: {movie_id}")
        return None

    def get_tv_by_id(self, tv_id: int) -> Optional[Dict]:
        """Get TV show details by TMDb ID"""
        self.logger.debug(f"[GET_TV_BY_ID] Fetching TV ID: {tv_id}")
        data = self._make_request(f"/tv/{tv_id}", {})

        if not data:
            self.logger.debug(f"[GET_TV_BY_ID] TV show not found: {tv_id}")
            return None

        if data.get("name") and data.get("first_air_date"):
            self.logger.debug(f"[GET_TV_BY_ID] Found: {data.get('name')}")
            return data

        self.logger.debug(f"[GET_TV_BY_ID] TV show missing required fields: {tv_id}")
        return None
