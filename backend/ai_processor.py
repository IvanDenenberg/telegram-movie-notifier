import os
from typing import Optional
from backend.security import SecurityManager


class AIProcessor:
    """
    Procesa texto libre con Claude API (cuando habilitado).
    Sanitiza respuestas para evitar exposure de datos sensibles.
    """

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.client = None
        self.security_manager = SecurityManager()

        if enabled:
            try:
                import anthropic
                api_key = os.getenv('CLAUDE_API_KEY')
                if not api_key:
                    raise ValueError("CLAUDE_API_KEY requerido en .env para habilitar IA")

                self.client = anthropic.Anthropic(api_key=api_key)
                # NO guardar la API key en memoria, solo en self.client
            except ImportError:
                print("⚠️  anthropic no instalado. Instala: pip install anthropic")
                self.enabled = False
            except ValueError as e:
                print(f"⚠️  {e}")
                self.enabled = False

    def process(self, message: str) -> Optional[str]:
        """
        Procesa mensaje con Claude API.
        Retorna comando parseado o None.
        """
        if not self.enabled or not self.client:
            return None

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=100,
                system="""Eres un asistente que convierte frases en comandos de bot.

Comandos disponibles:
- /add "título" - agregar película
- /add_actor "nombre" - monitorear actor
- /list - ver lista
- /remove "título" - eliminar

Si el usuario quiere una película, responde solo: /add "Titulo"
Si quiere un actor, responde solo: /add_actor "Nombre"
Si no es claro, responde "UNCLEAR"

NO incluyas otra cosa en la respuesta.""",
                messages=[
                    {"role": "user", "content": message}
                ]
            )

            result = response.content[0].text.strip()

            # Sanitizar respuesta
            sanitized = self._sanitize_response(result)

            # Validar que es un comando
            if sanitized.startswith("/") or sanitized == "UNCLEAR":
                return sanitized if sanitized != "UNCLEAR" else None

            return None

        except Exception as e:
            # Log error sin exponer API key
            print(f"Error en IA: {self.security_manager.sanitize(str(e))}")
            return None

    def _sanitize_response(self, response: str) -> str:
        """Sanitiza respuesta de IA antes de retornar"""
        return self.security_manager.sanitize(response)
