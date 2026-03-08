from typing import Optional, Dict, List
from backend.http_client import RequestManager


class TMDbClient:
    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(self, api_key: str):
        """Initialize TMDb client with API key"""
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
        data = self._make_request("/search/movie", {"query": title})
        if not data or "results" not in data or not data["results"]:
            return None

        # Normalize search title for comparison
        search_title_lower = title.lower().strip()

        # First pass: look for exact title match
        for result in data["results"]:
            if result.get("title") and result.get("release_date"):
                result_title_lower = result["title"].lower().strip()
                if result_title_lower == search_title_lower:
                    return result

        # Second pass: look for titles starting with search term
        for result in data["results"]:
            if result.get("title") and result.get("release_date"):
                result_title_lower = result["title"].lower().strip()
                if result_title_lower.startswith(search_title_lower):
                    return result

        # Fall back to first valid result
        for result in data["results"]:
            if result.get("title") and result.get("release_date"):
                return result

        return None

    def search_tv(self, title: str) -> Optional[Dict]:
        """Search for a TV show by title - prefers exact matches"""
        data = self._make_request("/search/tv", {"query": title})
        if not data or "results" not in data or not data["results"]:
            return None

        # Normalize search title for comparison
        search_title_lower = title.lower().strip()

        # First pass: look for exact title match
        for result in data["results"]:
            if result.get("name") and result.get("first_air_date"):
                result_name_lower = result["name"].lower().strip()
                if result_name_lower == search_title_lower:
                    return result

        # Second pass: look for titles starting with search term
        for result in data["results"]:
            if result.get("name") and result.get("first_air_date"):
                result_name_lower = result["name"].lower().strip()
                if result_name_lower.startswith(search_title_lower):
                    return result

        # Fall back to first valid result
        for result in data["results"]:
            if result.get("name") and result.get("first_air_date"):
                return result

        return None

    def get_actor_id(self, actor_name: str) -> Optional[int]:
        """Get actor ID by name - prefers exact matches"""
        data = self._make_request("/search/person", {"query": actor_name})
        if not data or "results" not in data or not data["results"]:
            return None

        # Normalize search name for comparison
        search_name_lower = actor_name.lower().strip()

        # First pass: look for exact name match
        for result in data["results"]:
            if result.get("name"):
                result_name_lower = result["name"].lower().strip()
                if result_name_lower == search_name_lower:
                    return result.get("id")

        # Second pass: look for names starting with search term
        for result in data["results"]:
            if result.get("name"):
                result_name_lower = result["name"].lower().strip()
                if result_name_lower.startswith(search_name_lower):
                    return result.get("id")

        # Fall back to first result (with popularity check - must have known_for_department)
        for result in data["results"]:
            if result.get("id") and result.get("known_for_department"):
                return result.get("id")

        # Last resort: first result with ID
        if data["results"] and data["results"][0].get("id"):
            return data["results"][0]["id"]

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
