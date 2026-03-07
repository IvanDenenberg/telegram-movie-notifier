import requests
from typing import Optional, Dict, Any


class RequestManager:
    """
    Manejador centralizado de requests HTTP.
    Asegura timeouts y buenas prácticas en todas las llamadas.
    """

    DEFAULT_TIMEOUT = 5
    DEFAULT_RETRIES = 2

    def __init__(self, timeout: int = DEFAULT_TIMEOUT, retries: int = DEFAULT_RETRIES):
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()

    def get(
        self,
        url: str,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        **kwargs
    ) -> Optional[Dict]:
        """Realizar GET request con timeout"""
        try:
            # Asegurar que siempre haya timeout
            if "timeout" not in kwargs:
                kwargs["timeout"] = self.timeout

            response = self.session.get(url, params=params, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return None

    def close(self):
        """Cerrar session"""
        self.session.close()
