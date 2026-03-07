from typing import Optional


class AIProcessor:
    """
    Procesa texto libre con IA (futuro).
    Ahora solo retorna None (desactivado).
    """

    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def process(self, message: str) -> Optional[str]:
        """
        Procesa mensaje con IA.
        Retorna comando (ej: "/add_actor Tom Cruise") o None.

        Futuro:
        - Integrar Claude API
        - O integrar modelo local (Mistral, Phi)
        """
        if not self.enabled:
            return None

        # Placeholder para IA futura
        return None
