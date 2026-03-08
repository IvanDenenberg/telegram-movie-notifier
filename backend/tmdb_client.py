import logging
from typing import Optional, Dict, List
from backend.http_client import RequestManager


class TMDbClient:
    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(self, api_key: str):
        """Initialize TMDb client with API key"""
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.request_manager = RequestManager(timeout=5)

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
        """Search for a movie by title - prefers exact matches"""
        self.logger.debug(f"[SEARCH_MOVIE] Querying TMDb for: {title}")

        data = self._make_request("/search/movie", {"query": title})
        if not data or "results" not in data or not data["results"]:
            self.logger.debug(f"[SEARCH_MOVIE] No results found for: {title}")
            return None

        self.logger.debug(f"[SEARCH_MOVIE] Found {len(data['results'])} results")

        # Normalize search title for comparison
        search_title_lower = title.lower().strip()

        # First pass: look for exact title match
        for result in data["results"]:
            if result.get("title") and result.get("release_date"):
                result_title_lower = result["title"].lower().strip()
                if result_title_lower == search_title_lower:
                    self.logger.debug(f"[SEARCH_MOVIE] Exact match found: {result['title']} (ID: {result.get('id')})")
                    return result

        # Second pass: look for titles starting with search term
        for result in data["results"]:
            if result.get("title") and result.get("release_date"):
                result_title_lower = result["title"].lower().strip()
                if result_title_lower.startswith(search_title_lower):
                    self.logger.debug(f"[SEARCH_MOVIE] Prefix match found: {result['title']} (ID: {result.get('id')})")
                    return result

        # Fall back to first valid result
        for result in data["results"]:
            if result.get("title") and result.get("release_date"):
                self.logger.debug(f"[SEARCH_MOVIE] Using first valid result: {result['title']} (ID: {result.get('id')})")
                return result

        self.logger.debug(f"[SEARCH_MOVIE] No valid results for: {title}")
        return None

    def search_tv(self, title: str) -> Optional[Dict]:
        """Search for a TV show by title - prefers exact matches"""
        self.logger.debug(f"[SEARCH_TV] Querying TMDb for: {title}")

        data = self._make_request("/search/tv", {"query": title})
        if not data or "results" not in data or not data["results"]:
            self.logger.debug(f"[SEARCH_TV] No results found for: {title}")
            return None

        self.logger.debug(f"[SEARCH_TV] Found {len(data['results'])} results")

        # Normalize search title for comparison
        search_title_lower = title.lower().strip()

        # First pass: look for exact title match
        for result in data["results"]:
            if result.get("name") and result.get("first_air_date"):
                result_name_lower = result["name"].lower().strip()
                if result_name_lower == search_title_lower:
                    self.logger.debug(f"[SEARCH_TV] Exact match found: {result['name']} (ID: {result.get('id')})")
                    return result

        # Second pass: look for titles starting with search term
        for result in data["results"]:
            if result.get("name") and result.get("first_air_date"):
                result_name_lower = result["name"].lower().strip()
                if result_name_lower.startswith(search_title_lower):
                    self.logger.debug(f"[SEARCH_TV] Prefix match found: {result['name']} (ID: {result.get('id')})")
                    return result

        # Fall back to first valid result
        for result in data["results"]:
            if result.get("name") and result.get("first_air_date"):
                self.logger.debug(f"[SEARCH_TV] Using first valid result: {result['name']} (ID: {result.get('id')})")
                return result

        self.logger.debug(f"[SEARCH_TV] No valid results for: {title}")
        return None

    def get_actor_id(self, actor_name: str) -> Optional[int]:
        """Get actor ID by name - prefers exact matches"""
        self.logger.debug(f"[GET_ACTOR_ID] Searching for actor: {actor_name}")

        data = self._make_request("/search/person", {"query": actor_name})
        if not data or "results" not in data or not data["results"]:
            self.logger.debug(f"[GET_ACTOR_ID] No results for: {actor_name}")
            return None

        self.logger.debug(f"[GET_ACTOR_ID] Found {len(data['results'])} results")

        # Normalize search name for comparison
        search_name_lower = actor_name.lower().strip()

        # First pass: look for exact name match
        for result in data["results"]:
            if result.get("name"):
                result_name_lower = result["name"].lower().strip()
                if result_name_lower == search_name_lower:
                    self.logger.debug(f"[GET_ACTOR_ID] Exact match found: {result['name']} (ID: {result.get('id')})")
                    return result.get("id")

        # Second pass: look for names starting with search term
        for result in data["results"]:
            if result.get("name"):
                result_name_lower = result["name"].lower().strip()
                if result_name_lower.startswith(search_name_lower):
                    self.logger.debug(f"[GET_ACTOR_ID] Prefix match found: {result['name']} (ID: {result.get('id')})")
                    return result.get("id")

        # Fall back to first result (with popularity check - must have known_for_department)
        for result in data["results"]:
            if result.get("id") and result.get("known_for_department"):
                self.logger.debug(f"[GET_ACTOR_ID] Using result with known_for_department: {result['name']} (ID: {result.get('id')})")
                return result.get("id")

        # Last resort: first result with ID
        if data["results"] and data["results"][0].get("id"):
            self.logger.debug(f"[GET_ACTOR_ID] Using first result: {data['results'][0].get('name')} (ID: {data['results'][0]['id']})")
            return data["results"][0]["id"]

        self.logger.debug(f"[GET_ACTOR_ID] No valid results for: {actor_name}")
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
