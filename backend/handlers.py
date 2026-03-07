from typing import List, Optional
from backend.storage import Storage
from backend.tmdb_client import TMDbClient


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
            return f"✅ '{movie.get('title', title)}' agregada a tu lista 🎬"

        # Try to search for TV show
        tv = self.tmdb.search_tv(title)
        if tv:
            self.storage.add_movie(tv.get("name", title), tv.get("id"))
            return f"✅ '{tv.get('name', title)}' agregada a tu lista 📺"

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
        return f"✅ Monitoreando a {actor_name} 👤"

    def handle_list(self, args: List[str] = None) -> str:
        """Handle /list command - show all movies and actors"""
        movies = self.storage.get_movies()
        actors = self.storage.get_actors()

        if not movies and not actors:
            return "No tienes nada en tu lista... 📋"

        result = "📋 **Tu Lista:**\n\n"

        if movies:
            result += "**Películas y Series:**\n"
            for movie in movies:
                result += f"  🎬 {movie.get('title', 'Unknown')}\n"
            result += "\n"

        if actors:
            result += "**Actores Monitoreados:**\n"
            for actor in actors:
                result += f"  👤 {actor.get('name', 'Unknown')}\n"

        return result

    def handle_remove(self, args: List[str]) -> str:
        """Handle /remove command - remove movie, show, or actor"""
        if not args:
            return "❌ Por favor especifica qué remover: /remove \"Título o nombre\""

        search_term = args[0].lower()

        # Search in movies/shows
        movies = self.storage.get_movies()
        for movie in movies:
            if movie.get("title", "").lower() == search_term:
                if self.storage.remove_movie(movie.get("id")):
                    return f"✅ '{movie.get('title')}' removida de tu lista"

        # Search in actors
        actors = self.storage.get_actors()
        for actor in actors:
            if actor.get("name", "").lower() == search_term:
                if self.storage.remove_actor(actor.get("id")):
                    return f"✅ '{actor.get('name')}' removida de tu lista"

        return f"❌ No encontré '{args[0]}' en tu lista."

    def handle_help(self, args: List[str] = None) -> str:
        """Handle /help command - show available commands"""
        help_text = """📖 **Comandos Disponibles:**

**/add "Título"** - Agrega una película o serie
  Ejemplo: `/add "Dune"`

**/add_actor "Nombre"** - Monitorea a un actor
  Ejemplo: `/add_actor "Tom Cruise"`

**/list** - Muestra tu lista de películas y actores
  Ejemplo: `/list`

**/remove "Título o Nombre"** - Remueve un elemento
  Ejemplo: `/remove "Dune"`

**/help** - Muestra este mensaje de ayuda
  Ejemplo: `/help`"""

        return help_text
