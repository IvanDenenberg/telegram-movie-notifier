from typing import List, Optional
import logging
from backend.storage import Storage
from backend.tmdb_client import TMDbClient
from backend.notifier import Notifier

logger = logging.getLogger(__name__)


class CommandHandler:
    def __init__(self, tmdb_api_key: str, storage_path: str):
        """Initialize command handler with TMDb API key and storage path"""
        self.logger = logging.getLogger(__name__)
        self.tmdb = TMDbClient(tmdb_api_key)
        self.storage = Storage(storage_path)

    def handle_add(self, args: List[str]) -> str:
        """Handle /add command - add movie or TV show"""
        if not args:
            return "❌ Por favor especifica el título: /add \"Título de película\""

        title = args[0]

        # Try to search for movie first
        movie = self.tmdb.search_movie(title)
        if movie:
            # Verify it's a close match (avoid "Vladimir" → "Vladimir and Rosa")
            if self._is_close_match(title, movie.get("title", "")):
                self.storage.add_movie(movie.get("title", title), movie.get("id"), media_type="movie")
                movie_id = movie.get("id")
                tmdb_link = f"https://www.themoviedb.org/movie/{movie_id}"
                return f"✅ '{movie.get('title', title)}' agregada a tu lista 🎬\n<a href='{tmdb_link}'>Ver en TMDb</a>"

        # Try to search for TV show
        tv = self.tmdb.search_tv(title)
        if tv:
            # Verify it's a close match
            if self._is_close_match(title, tv.get("name", "")):
                self.storage.add_movie(tv.get("name", title), tv.get("id"), media_type="tv")
                tv_id = tv.get("id")
                tmdb_link = f"https://www.themoviedb.org/tv/{tv_id}"
                return f"✅ '{tv.get('name', title)}' agregada a tu lista 📺\n<a href='{tmdb_link}'>Ver en TMDb</a>"

        return f"❌ No encontré un resultado exacto para '{title}'.\n\nIntenta:\n• Con el título completo\n• Con año: '{title} 2024'\n• En inglés si es aplicable"

    def _is_close_match(self, search_term: str, result_title: str) -> bool:
        """Check if result title is close enough to search term"""
        search_lower = search_term.lower().strip()
        result_lower = result_title.lower().strip()

        # Exact match
        if search_lower == result_lower:
            return True

        # Result starts with search term
        if result_lower.startswith(search_lower):
            return True

        # Search term in result (but not too loose - require significant match)
        if search_lower in result_lower:
            # Check that it's not just a substring (e.g., "Vladimir" in "Vladimir and Rosa")
            # Only accept if search term is at least 50% of the result length
            if len(search_lower) >= len(result_lower) * 0.5:
                return True

        return False

    def handle_add_actor(self, args: List[str]) -> str:
        """Handle /add_actor command - monitor actor's projects"""
        if not args:
            return "❌ Por favor especifica el nombre del actor: /add_actor \"Nombre\""

        actor_name = args[0]
        actor_id = self.tmdb.get_actor_id(actor_name)

        if not actor_id:
            return f"❌ No encontré al actor '{actor_name}' en TMDb."

        self.storage.add_actor(actor_name, actor_id)
        tmdb_link = f"https://www.themoviedb.org/person/{actor_id}"
        return f"✅ Monitoreando a {actor_name} 👤\n<a href='{tmdb_link}'>Ver en TMDb</a>"

    def handle_list(self, args: List[str] = None) -> str:
        """Handle /list command - show movies, actors, or both"""
        all_items = self.storage.get_movies()
        actors = self.storage.get_actors()

        # Separar películas y series
        movies = [m for m in all_items if m.get("type") == "movie"]
        tv_shows = [m for m in all_items if m.get("type") == "tv"]

        # Determinar qué mostrar
        filter_type = "all"
        if args and len(args) > 0:
            filter_type = args[0].lower()

        # DEBUG LOGS
        logger.info(f"[/list] BASE DE DATOS - Películas: {len(movies)}, Series: {len(tv_shows)}, Actores: {len(actors)}")
        logger.info(f"[/list] Filtro: '{filter_type}'")

        if not movies and not tv_shows and not actors:
            return "No tienes nada en tu lista... 📋"

        result = "📋 <b>Tu Lista</b>\n\n"

        # Mostrar películas si filter_type es "all" o "movies"
        if filter_type in ["all", "movies"] and movies:
            result += "<b>🎬 Películas:</b>\n"
            for movie in movies:
                title = movie.get('title', 'Unknown')
                result += f"  • {title}\n"
                result += f"    <code>/remove \"{title}\"</code>\n"
            result += "\n"

        # Mostrar series si filter_type es "all" o "series"
        if filter_type in ["all", "series"] and tv_shows:
            result += "<b>📺 Series:</b>\n"
            for show in tv_shows:
                title = show.get('title', 'Unknown')
                result += f"  • {title}\n"
                result += f"    <code>/remove \"{title}\"</code>\n"
            result += "\n"

        # Mostrar actores si filter_type es "all" o "actors"
        if filter_type in ["all", "actors"] and actors:
            result += "<b>👤 Actores Monitoreados:</b>\n"
            for actor in actors:
                name = actor.get('name', 'Unknown')
                result += f"  • {name}\n"
                result += f"    <code>/remove \"{name}\"</code>\n"
            result += "\n"

        # Mostrar opciones de filtro
        if filter_type == "all":
            result += "<b>Filtros:</b>\n"
            result += "/list movies - solo películas\n"
            result += "/list series - solo series\n"
            result += "/list actors - solo actores"

        return result

    def handle_remove(self, args: List[str]) -> str:
        """Handle /remove command - remove movie, show, or actor"""
        if not args:
            return "❌ Por favor especifica qué remover: /remove \"Título o nombre\""

        # Clean search term: remove any quotes that might be included
        search_input = args[0].strip().strip('"\'""\'')  # Remove all types of quotes
        search_term = search_input.lower()

        # DEBUG LOGS
        logger.info(f"[/remove] BUSCANDO: '{args[0]}' → normalizado: '{search_term}'")

        # Search in movies/shows
        movies = self.storage.get_movies()
        logger.info(f"[/remove] Películas en DB: {[(m.get('title'), m.get('title', '').lower()) for m in movies]}")

        for movie in movies:
            movie_title_lower = movie.get("title", "").lower()
            logger.info(f"[/remove] Comparando '{search_term}' == '{movie_title_lower}' ? {search_term == movie_title_lower}")

            if movie_title_lower == search_term:
                if self.storage.remove_movie(movie.get("id")):
                    logger.info(f"[/remove] ✅ Película removida: {movie.get('title')}")
                    return f"✅ '{movie.get('title')}' removida de tu lista"

        # Search in actors
        actors = self.storage.get_actors()
        logger.info(f"[/remove] Actores en DB: {[(a.get('name'), a.get('name', '').lower()) for a in actors]}")

        for actor in actors:
            actor_name_lower = actor.get("name", "").lower()
            logger.info(f"[/remove] Comparando '{search_term}' == '{actor_name_lower}' ? {search_term == actor_name_lower}")

            if actor_name_lower == search_term:
                if self.storage.remove_actor(actor.get("id")):
                    logger.info(f"[/remove] ✅ Actor removido: {actor.get('name')}")
                    return f"✅ '{actor.get('name')}' removida de tu lista"

        logger.warning(f"[/remove] ❌ No encontrado: '{args[0]}'")
        return f"❌ No encontré '{args[0]}' en tu lista."

    def handle_help(self, args: List[str] = None) -> str:
        """Handle /help command - show available commands"""
        help_text = """📖 <b>Comandos Disponibles:</b>

<b>/add "Título"</b> - Agrega una película o serie
  Ejemplo: /add "Dune"

<b>/add_actor "Nombre"</b> - Monitorea a un actor
  Ejemplo: /add_actor "Tom Cruise"

<b>/list</b> - Muestra tu lista
  /list - Todo
  /list movies - Solo películas
  /list series - Solo series
  /list actors - Solo actores

<b>/remove "Título o Nombre"</b> - Remueve un elemento
  Ejemplo: /remove "Dune"

<b>/help</b> - Muestra este mensaje de ayuda
  Ejemplo: /help"""

        return help_text

    def handle_upcoming(self, args: List[str]) -> str:
        """Handle /upcoming command with optional filter (movies, series, actors)"""
        # Determine filter
        filter_type = "all"
        if args and len(args) > 0:
            filter_arg = args[0].lower()
            if filter_arg in ["movies", "series", "actors"]:
                filter_type = filter_arg

        # Get releases in range using Notifier
        notifier = Notifier(self.tmdb.api_key, self.storage.path)
        releases_by_type = notifier.get_releases_in_range(days=60, filter_type=filter_type)

        # Check if there are any results
        total_releases = sum(len(v) for v in releases_by_type.values())
        if total_releases == 0:
            return "No hay estrenos en los próximos 60 días"

        # Format response
        response = ""

        if filter_type in ["all", "movies"] and releases_by_type["movies"]:
            response += "<b>🎬 Películas (próximos 60 días):</b>\n"
            for release in releases_by_type["movies"]:
                response += f"  • {release['title']} - {release['release_date']}\n"
            response += "\n"

        if filter_type in ["all", "series"] and releases_by_type["series"]:
            response += "<b>📺 Series (próximos 60 días):</b>\n"
            for release in releases_by_type["series"]:
                response += f"  • {release['title']} - {release['release_date']}\n"
            response += "\n"

        if filter_type == "all" and releases_by_type["actors"]:
            response += "<b>👤 Actores (próximos 60 días):</b>\n"
            for release in releases_by_type["actors"]:
                actor_name = release.get("actor", "Unknown")
                response += f"  • {actor_name} - {release['title']} ({release['release_date']})\n"
            response += "\n"

        return response.rstrip()
