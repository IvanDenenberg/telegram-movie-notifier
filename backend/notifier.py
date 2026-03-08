import logging
from typing import List, Dict, Callable, Optional
from datetime import datetime, timedelta
from backend.storage import Storage
from backend.tmdb_client import TMDbClient


class Notifier:
    def __init__(self, tmdb_api_key: str, storage_path: str):
        """Inicializa el Notifier con TMDb API key y ruta de storage"""
        self.logger = logging.getLogger(__name__)
        self.tmdb_api_key = tmdb_api_key
        self.storage = Storage(storage_path)
        self.tmdb_client = TMDbClient(tmdb_api_key)
        self.callback = None

    def check_new_releases(self) -> List[Dict]:
        """
        Obtiene nuevos estrenos de películas y actores.
        Filtra por no-notificados y marca como notificados.
        """
        new_releases = []

        # Obtener películas seguidas
        movies = self.storage.get_movies()
        for movie in movies:
            # Obtener estrenos próximos
            upcoming = self.tmdb_client.get_upcoming_releases()
            for release in upcoming:
                # Si es una versión/secuela de la película seguida
                if self._is_related_to_movie(release, movie):
                    release_key = self._make_release_key(
                        release["id"],
                        release.get("release_date", "")
                    )

                    # Verificar si ya fue notificado
                    if not self.storage.is_notified(release_key):
                        new_releases.append(release)
                        self.storage.mark_notified(release_key)

        # Obtener actores seguidos
        actors = self.storage.get_actors()
        for actor in actors:
            # Obtener filmografía del actor
            filmography = self.tmdb_client.get_actor_filmography(actor["id"])
            for release in filmography:
                release_key = self._make_release_key(
                    release["id"],
                    release.get("release_date", "")
                )

                # Verificar si ya fue notificado
                if not self.storage.is_notified(release_key):
                    new_releases.append(release)
                    self.storage.mark_notified(release_key)

            # Obtener series del actor
            tv_credits = self.tmdb_client.get_actor_tv_credits(actor["id"])
            for release in tv_credits:
                release_key = self._make_release_key(
                    release["id"],
                    release.get("first_air_date", "")
                )

                # Verificar si ya fue notificado
                if not self.storage.is_notified(release_key):
                    new_releases.append(release)
                    self.storage.mark_notified(release_key)

        # Obtener directores seguidos
        directors = self.storage.get_directors()
        for director in directors:
            # Obtener filmografía del director (solo donde dirige)
            filmography = self.tmdb_client.get_director_filmography(director["id"])
            for release in filmography:
                release_key = self._make_release_key(
                    release["id"],
                    release.get("release_date", "")
                )

                # Verificar si ya fue notificado
                if not self.storage.is_notified(release_key):
                    new_releases.append(release)
                    self.storage.mark_notified(release_key)

            # Obtener series del director (solo donde dirige)
            tv_credits = self.tmdb_client.get_director_tv_credits(director["id"])
            for release in tv_credits:
                release_key = self._make_release_key(
                    release["id"],
                    release.get("first_air_date", "")
                )

                # Verificar si ya fue notificado
                if not self.storage.is_notified(release_key):
                    new_releases.append(release)
                    self.storage.mark_notified(release_key)

        return new_releases

    def _is_related_to_movie(self, release: Dict, movie: Dict) -> bool:
        """Verifica si un estreno está relacionado con la película seguida"""
        # Buscar palabras clave del título original en el título del estreno
        movie_words = movie["title"].lower().split()
        release_title = release.get("title", "").lower()

        for word in movie_words:
            if len(word) > 3 and word in release_title:
                return True

        return False

    def _make_release_key(self, tmdb_id: int, release_date: str) -> str:
        """Crea una clave única para un estreno"""
        return f"release_{tmdb_id}_{release_date}"

    def format_notification(self, release: Dict, media_type: str) -> str:
        """Formatea un mensaje de notificación con emojis"""
        if media_type == "movie":
            emoji = "🎬"
            title_key = "title"
            date_key = "release_date"
        else:  # tv
            emoji = "📺"
            title_key = "name"
            date_key = "first_air_date"

        title = release.get(title_key, "Unknown")
        release_date = release.get(date_key, "TBA")

        message = f"{emoji} Nuevo estreno: {title}\n📅 Fecha: {release_date}"
        return message

    def notify_callback(self, callback: Callable[[str], None]):
        """Establece el callback para notificaciones"""
        self.callback = callback

    def process_releases(self):
        """Procesa nuevos estrenos y ejecuta callbacks"""
        releases = self.check_new_releases()

        for release in releases:
            # Determinar tipo de media
            if "title" in release:
                media_type = "movie"
            else:
                media_type = "tv"

            message = self.format_notification(release, media_type)

            if self.callback:
                self.callback(message)

    def get_releases_in_range(self, days: int = 60, filter_type: str = "all") -> Dict[str, List]:
        """
        Get releases for movies/actors within N days, grouped by type.

        Args:
            days: Number of days to look ahead (default 60)
            filter_type: "all", "movies", "series", or "actors"

        Returns:
            Dict with keys: "movies", "series", "actors", each containing list of releases
        """
        self.logger.debug(f"[NOTIFIER] Checking releases for next {days} days (filter: {filter_type})")
        result = {"movies": [], "series": [], "actors": []}

        today = datetime.now().date()
        end_date = today + timedelta(days=days)

        # Process movies
        if filter_type in ["all", "movies"]:
            for movie in self.storage.get_movies():
                movie_data = self.tmdb_client.search_movie(movie["title"])
                if movie_data and movie_data.get("release_date"):
                    release_date = datetime.strptime(
                        movie_data["release_date"], "%Y-%m-%d"
                    ).date()
                    if today <= release_date <= end_date:
                        result["movies"].append({
                            "title": movie_data.get("title", movie["title"]),
                            "release_date": movie_data["release_date"],
                            "type": "movie"
                        })

        # Process actors
        if filter_type in ["all", "movies", "series", "actors"]:
            for actor in self.storage.get_actors():
                # Get filmography (movies)
                if filter_type in ["all", "movies", "actors"]:
                    filmography = self.tmdb_client.get_actor_filmography(actor["id"])
                    for movie in filmography:
                        if movie.get("release_date"):
                            release_date = datetime.strptime(
                                movie["release_date"], "%Y-%m-%d"
                            ).date()
                            if today <= release_date <= end_date:
                                result["movies"].append({
                                    "title": movie.get("title", "Unknown"),
                                    "release_date": movie["release_date"],
                                    "type": "movie",
                                    "actor": actor["name"]
                                })

                # Get TV credits (series)
                if filter_type in ["all", "series", "actors"]:
                    tv_credits = self.tmdb_client.get_actor_tv_credits(actor["id"])
                    for show in tv_credits:
                        if show.get("first_air_date"):
                            release_date = datetime.strptime(
                                show["first_air_date"], "%Y-%m-%d"
                            ).date()
                            if today <= release_date <= end_date:
                                result["series"].append({
                                    "title": show.get("name", "Unknown"),
                                    "release_date": show["first_air_date"],
                                    "type": "tv",
                                    "actor": actor["name"]
                                })

        # Sort each list by release_date
        for key in result:
            result[key].sort(key=lambda x: x["release_date"])

        self.logger.debug(f"[NOTIFIER] Found {len(result['movies'])} movies, {len(result['series'])} series, {len(result.get('actors', []))} actor projects")
        return result
