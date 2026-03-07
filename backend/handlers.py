from typing import List, Optional
import logging
from backend.storage import Storage
from backend.tmdb_client import TMDbClient

logger = logging.getLogger(__name__)


class CommandHandler:
    def __init__(self, tmdb_api_key: str, storage_path: str):
        """Initialize command handler with TMDb API key and storage path"""
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
            self.storage.add_movie(movie.get("title", title), movie.get("id"))
            movie_id = movie.get("id")
            tmdb_link = f"https://www.themoviedb.org/movie/{movie_id}"
            return f"✅ '{movie.get('title', title)}' agregada a tu lista 🎬\n<a href='{tmdb_link}'>Ver en TMDb</a>"

        # Try to search for TV show
        tv = self.tmdb.search_tv(title)
        if tv:
            self.storage.add_movie(tv.get("name", title), tv.get("id"))
            tv_id = tv.get("id")
            tmdb_link = f"https://www.themoviedb.org/tv/{tv_id}"
            return f"✅ '{tv.get('name', title)}' agregada a tu lista 📺\n<a href='{tmdb_link}'>Ver en TMDb</a>"

        return f"❌ No encontré '{title}' en TMDb. Intenta con otro título."

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
        """Handle /list command - show all movies and actors"""
        movies = self.storage.get_movies()
        actors = self.storage.get_actors()

        # DEBUG LOGS
        logger.info(f"[/list] BASE DE DATOS - Películas: {len(movies)}, Actores: {len(actors)}")
        logger.info(f"[/list] Películas en DB: {[m.get('title') for m in movies]}")
        logger.info(f"[/list] Actores en DB: {[a.get('name') for a in actors]}")

        if not movies and not actors:
            return "No tienes nada en tu lista... 📋"

        result = "📋 <b>Tu Lista:</b>\n\n"

        if movies:
            result += "<b>Películas y Series:</b>\n"
            for movie in movies:
                result += f"  🎬 {movie.get('title', 'Unknown')}\n"
            result += "\n"

        if actors:
            result += "<b>Actores Monitoreados:</b>\n"
            for actor in actors:
                result += f"  👤 {actor.get('name', 'Unknown')}\n"

        return result

    def handle_remove(self, args: List[str]) -> str:
        """Handle /remove command - remove movie, show, or actor"""
        if not args:
            return "❌ Por favor especifica qué remover: /remove \"Título o nombre\""

        search_term = args[0].lower()

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

<b>/list</b> - Muestra tu lista de películas y actores
  Ejemplo: /list

<b>/remove "Título o Nombre"</b> - Remueve un elemento
  Ejemplo: /remove "Dune"

<b>/help</b> - Muestra este mensaje de ayuda
  Ejemplo: /help"""

        return help_text
