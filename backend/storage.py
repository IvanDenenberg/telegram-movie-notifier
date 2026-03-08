import logging
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class Storage:
    def __init__(self, path: str = "data/movies.json"):
        self.logger = logging.getLogger(__name__)
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            self._initialize_storage()

    def _initialize_storage(self):
        """Inicializa el archivo JSON con estructura vacía"""
        data = {
            "movies": [],
            "actors": [],
            "notified": []
        }
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_data(self) -> dict:
        """Carga datos del archivo JSON"""
        with open(self.path, 'r') as f:
            return json.load(f)

    def _save_data(self, data: dict):
        """Guarda datos al archivo JSON"""
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=2)

    def add_movie(self, title: str, tmdb_id: int, media_type: str = "movie"):
        """Agrega una película o serie (media_type: 'movie' o 'tv')"""
        self.logger.debug(f"[STORAGE.ADD_MOVIE] Adding {media_type}: {title} (ID: {tmdb_id})")
        data = self._load_data()

        # Evita duplicados
        if any(movie["id"] == tmdb_id for movie in data["movies"]):
            return

        movie = {
            "title": title,
            "id": tmdb_id,
            "type": media_type,  # "movie" o "tv"
            "added_date": datetime.now().isoformat()
        }
        data["movies"].append(movie)
        self._save_data(data)
        self.logger.debug(f"[STORAGE.ADD_MOVIE] Successfully saved to storage")

    def add_actor(self, name: str, tmdb_id: int):
        """Agrega un actor"""
        self.logger.debug(f"[STORAGE.ADD_ACTOR] Adding actor: {name} (ID: {tmdb_id})")
        data = self._load_data()

        # Evita duplicados
        if any(actor["id"] == tmdb_id for actor in data["actors"]):
            return

        actor = {
            "name": name,
            "id": tmdb_id,
            "added_date": datetime.now().isoformat()
        }
        data["actors"].append(actor)
        self._save_data(data)
        self.logger.debug(f"[STORAGE.ADD_ACTOR] Successfully saved to storage")

    def remove_movie(self, tmdb_id: int) -> bool:
        """Elimina una película"""
        self.logger.debug(f"[STORAGE.REMOVE_MOVIE] Removing movie ID: {tmdb_id}")
        data = self._load_data()

        initial_length = len(data["movies"])
        data["movies"] = [movie for movie in data["movies"] if movie["id"] != tmdb_id]

        if len(data["movies"]) < initial_length:
            self._save_data(data)
            return True
        return False

    def remove_actor(self, tmdb_id: int) -> bool:
        """Elimina un actor"""
        self.logger.debug(f"[STORAGE.REMOVE_ACTOR] Removing actor ID: {tmdb_id}")
        data = self._load_data()

        initial_length = len(data["actors"])
        data["actors"] = [actor for actor in data["actors"] if actor["id"] != tmdb_id]

        if len(data["actors"]) < initial_length:
            self._save_data(data)
            return True
        return False

    def get_movies(self) -> List[Dict]:
        """Obtiene todas las películas"""
        data = self._load_data()
        return data["movies"]

    def get_actors(self) -> List[Dict]:
        """Obtiene todos los actores"""
        data = self._load_data()
        return data["actors"]

    def mark_notified(self, release_key: str):
        """Marca un estreno como notificado"""
        data = self._load_data()

        if release_key not in data["notified"]:
            data["notified"].append(release_key)
            self._save_data(data)

    def is_notified(self, release_key: str) -> bool:
        """Verifica si un estreno ya fue notificado"""
        data = self._load_data()
        return release_key in data["notified"]
