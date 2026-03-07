# Security Hardening - Plan de Mitigación de Riesgos

> **Para Claude:** REQUERIDO SUB-SKILL: Usa superpowers:executing-plans para implementar este plan task-by-task.

**Objetivo:** Mitigar 5 riesgos de seguridad identificados: API keys en URLs, logging sin sanitizar, falta de timeouts, integración IA insegura, y datos sin encripción.

**Arquitectura:** Crear utilidades de seguridad centralizadas (logging sanitizado, request manager con timeout), modificar clientes de API para usar headers en lugar de parámetros, preparar AIProcessor para integración segura de Claude API, y documentar mejores prácticas.

**Tech Stack:** Python logging, cryptography (Fernet), requests, anthropic SDK (futuro).

---

## Task 1: Crear utilidad de sanitización de logs

**Archivos:**
- Crear: `backend/security.py` - Módulo de utilidades de seguridad
- Modificar: `backend/__init__.py` - Exportar SecurityManager

**Paso 1: Escribir test para SecurityManager**

Crear `tests/test_security.py`:

```python
import unittest
from backend.security import SecurityManager


class TestSecurityManager(unittest.TestCase):
    def test_sanitize_sensitive_data(self):
        """Test sanitiza API keys de strings"""
        manager = SecurityManager()
        manager.add_sensitive_key("test_key_123")

        text = "Usando API key: test_key_123 en request"
        sanitized = manager.sanitize(text)

        assert "test_key_123" not in sanitized
        assert "***REDACTED***" in sanitized

    def test_multiple_keys_sanitized(self):
        """Test sanitiza múltiples keys"""
        manager = SecurityManager()
        manager.add_sensitive_key("key1")
        manager.add_sensitive_key("key2")

        text = "key1 and key2 in one string"
        sanitized = manager.sanitize(text)

        assert "key1" not in sanitized
        assert "key2" not in sanitized

    def test_sanitize_empty_string(self):
        """Test maneja strings vacíos"""
        manager = SecurityManager()
        manager.add_sensitive_key("key")

        result = manager.sanitize("")
        assert result == ""

    def test_sanitize_none_key(self):
        """Test ignora keys None"""
        manager = SecurityManager()
        manager.add_sensitive_key(None)

        text = "Some text"
        sanitized = manager.sanitize(text)
        assert sanitized == "Some text"
```

**Paso 2: Ejecutar tests (FALLAN)**

```bash
cd /home/ivan/projects/movies_series_notifier
pytest tests/test_security.py -v
```

Esperado: `FAILED - ModuleNotFoundError: No module named 'backend.security'`

**Paso 3: Implementar SecurityManager**

Crear `backend/security.py`:

```python
from typing import Set, Optional
import logging


class SecurityManager:
    """
    Utilidad para sanitizar datos sensibles en logs y mensajes.
    Previene exposure de API keys y tokens en output.
    """

    def __init__(self):
        self.sensitive_keys: Set[str] = set()

    def add_sensitive_key(self, key: Optional[str]):
        """Registra una API key o token como sensible"""
        if key and isinstance(key, str) and key.strip():
            self.sensitive_keys.add(key.strip())

    def sanitize(self, text: str) -> str:
        """
        Sanitiza un string, reemplazando keys sensibles con ***REDACTED***
        """
        if not text:
            return text

        sanitized = text
        for key in self.sensitive_keys:
            if key in sanitized:
                sanitized = sanitized.replace(key, "***REDACTED***")

        return sanitized

    def get_sanitized_logger(self, name: str) -> logging.Logger:
        """
        Retorna un logger que sanitiza mensajes automáticamente
        """
        logger = logging.getLogger(name)
        handler = SanitizingHandler(self)
        logger.addHandler(handler)
        return logger


class SanitizingHandler(logging.Handler):
    """Handler de logging que sanitiza records automáticamente"""

    def __init__(self, security_manager: SecurityManager):
        super().__init__()
        self.security_manager = security_manager

    def emit(self, record: logging.LogRecord):
        """Sanitiza el mensaje antes de emitir"""
        try:
            msg = record.getMessage()
            sanitized = self.security_manager.sanitize(msg)
            record.msg = sanitized
        except Exception:
            pass  # Si sanitización falla, loguear original
```

**Paso 4: Ejecutar tests (PASAN)**

```bash
pytest tests/test_security.py -v
```

Esperado: `4 passed`

**Paso 5: Commit**

```bash
git add backend/security.py tests/test_security.py
git commit -m "feat: add security manager for sanitizing sensitive data in logs"
```

---

## Task 2: Refactorizar TMDb client para usar headers

**Archivos:**
- Modificar: `backend/tmdb_client.py` - Cambiar de params a headers
- Modificar: `tests/test_tmdb_client.py` - Actualizar tests

**Paso 1: Test fail - verificar que tests esperan nuevamente headers**

```bash
cd /home/ivan/projects/movies_series_notifier
pytest tests/test_tmdb_client.py::test_search_movie -v
```

Este test debería pasar primero (ya existe), luego lo modificaremos.

**Paso 2: Modificar TMDbClient**

En `backend/tmdb_client.py`, cambiar `_make_request`:

```python
def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
    """Make HTTP request to TMDb API with secure headers"""
    try:
        if params is None:
            params = {}

        # NO agregar api_key a params - usar header en su lugar
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        url = f"{self.BASE_URL}{endpoint}"
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=5  # Agregar timeout también
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None
```

**Paso 3: Actualizar tests**

En `tests/test_tmdb_client.py`, cambiar mock para verificar headers:

```python
@patch('backend.tmdb_client.requests.get')
def test_search_movie_uses_secure_headers(mock_get):
    """Test que search_movie usa headers seguros, no parámetros"""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {"id": 438632, "title": "Dune", "release_date": "2024-02-14"}
        ]
    }
    mock_get.return_value = mock_response

    client = TMDbClient("fake_key")
    result = client.search_movie("Dune")

    # Verificar que se usó request.get
    assert mock_get.called

    # Verificar que headers contiene Authorization
    call_kwargs = mock_get.call_args[1]
    assert "headers" in call_kwargs
    assert "Authorization" in call_kwargs["headers"]
    assert "Bearer fake_key" in call_kwargs["headers"]["Authorization"]

    # Verificar que api_key NO está en params
    assert "api_key" not in call_kwargs.get("params", {})

    # Verificar timeout
    assert call_kwargs.get("timeout") == 5
```

**Paso 4: Ejecutar tests (PASAN)**

```bash
pytest tests/test_tmdb_client.py -v
```

Esperado: `5+ passed`

**Paso 5: Commit**

```bash
git add backend/tmdb_client.py tests/test_tmdb_client.py
git commit -m "fix: use secure headers instead of URL parameters for TMDb API key"
```

---

## Task 3: Integrar SecurityManager en bot.py

**Archivos:**
- Modificar: `bot.py` - Usar SecurityManager para logs

**Paso 1: Modificar bot.py**

En `bot.py`, después de imports:

```python
from backend.security import SecurityManager

class MovieNotifierBot:
    def __init__(self):
        """Inicializar componentes del bot"""
        load_dotenv()

        # Cargar variables de entorno
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.tmdb_api_key = os.getenv('TMDB_API_KEY')
        self.telegram_user_id = int(os.getenv('TELEGRAM_USER_ID', 0))

        if not self.telegram_token or not self.tmdb_api_key:
            raise ValueError("TELEGRAM_BOT_TOKEN y TMDB_API_KEY son requeridos en .env")

        # Configurar security manager
        self.security_manager = SecurityManager()
        self.security_manager.add_sensitive_key(self.telegram_token)
        self.security_manager.add_sensitive_key(self.tmdb_api_key)

        # Logger con sanitización
        self.logger = self.security_manager.get_sanitized_logger(__name__)

        # ... resto del __init__
```

En método `handle_message`, cambiar:

```python
except Exception as e:
    sanitized_error = self.security_manager.sanitize(str(e))
    self.logger.error(f"Error procesando mensaje: {sanitized_error}")
    await update.message.reply_text("❌ Hubo un error procesando tu mensaje.")
```

**Paso 2: Commit**

```bash
git add bot.py
git commit -m "feat: integrate SecurityManager for safe logging in bot"
```

---

## Task 4: Crear RequestManager con timeout

**Archivos:**
- Crear: `backend/http_client.py` - RequestManager con timeouts
- Modificar: `backend/tmdb_client.py` - Usar RequestManager
- Crear: `tests/test_http_client.py`

**Paso 1: Escribir tests**

Crear `tests/test_http_client.py`:

```python
import unittest
from unittest.mock import patch, MagicMock
from backend.http_client import RequestManager


class TestRequestManager(unittest.TestCase):
    def test_request_manager_initialization(self):
        """Test que RequestManager se inicializa correctamente"""
        manager = RequestManager(timeout=10)
        assert manager.timeout == 10

    def test_default_timeout(self):
        """Test timeout por default es 5 segundos"""
        manager = RequestManager()
        assert manager.timeout == 5

    @patch('backend.http_client.requests.get')
    def test_get_with_timeout(self, mock_get):
        """Test que get() aplica timeout"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        manager = RequestManager(timeout=8)
        result = manager.get("http://test.com", params={"q": "test"})

        # Verificar que se pasó timeout
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs.get("timeout") == 8
```

**Paso 2: Tests FALLAN**

```bash
pytest tests/test_http_client.py -v
```

**Paso 3: Implementar RequestManager**

Crear `backend/http_client.py`:

```python
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
```

**Paso 4: Tests PASAN**

```bash
pytest tests/test_http_client.py -v
```

**Paso 5: Modificar TMDbClient para usar RequestManager**

En `backend/tmdb_client.py`:

```python
from backend.http_client import RequestManager

class TMDbClient:
    def __init__(self, api_key: str):
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
```

**Paso 6: Commit**

```bash
git add backend/http_client.py backend/tmdb_client.py tests/test_http_client.py
git commit -m "feat: add RequestManager with enforced timeouts and refactor TMDb client"
```

---

## Task 5: Preparar AIProcessor para Claude API segura

**Archivos:**
- Modificar: `backend/ai_processor.py` - Agregar soporte para Claude API
- Crear: `tests/test_ai_processor.py`

**Paso 1: Escribir tests**

Crear `tests/test_ai_processor.py`:

```python
import unittest
import os
from unittest.mock import patch, MagicMock
from backend.ai_processor import AIProcessor


class TestAIProcessor(unittest.TestCase):
    def test_ai_processor_disabled_by_default(self):
        """Test AIProcessor está deshabilitado por default"""
        processor = AIProcessor(enabled=False)
        result = processor.process("test message")
        assert result is None

    def test_ai_processor_requires_api_key(self):
        """Test que habilitar IA requiere API key"""
        with patch.dict(os.environ, {}, clear=True):
            processor = AIProcessor(enabled=True)
            # Debería lanzar error si falta CLAUDE_API_KEY
            assert processor.client is None or processor.enabled is False

    @patch.dict(os.environ, {'CLAUDE_API_KEY': 'test_key'})
    @patch('backend.ai_processor.anthropic.Anthropic')
    def test_ai_processor_with_api_key(self, mock_anthropic):
        """Test AIProcessor se inicializa con API key"""
        processor = AIProcessor(enabled=True)
        assert processor.enabled is True
        # Verificar que se creó cliente Anthropic
        mock_anthropic.assert_called_once()

    @patch.dict(os.environ, {'CLAUDE_API_KEY': 'test_key'})
    @patch('backend.ai_processor.anthropic.Anthropic')
    def test_ai_processor_sanitizes_output(self, mock_anthropic):
        """Test que output de IA se sanitiza"""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        processor = AIProcessor(enabled=True)
        processor.security_manager.add_sensitive_key("secret_key_123")

        # Simular respuesta con dato sensible
        mock_response = "Comando: /add_actor secret_key_123"
        result = processor._sanitize_response(mock_response)

        assert "secret_key_123" not in result
        assert "***REDACTED***" in result
```

**Paso 2: Tests FALLAN**

```bash
pytest tests/test_ai_processor.py -v
```

**Paso 3: Modificar AIProcessor**

En `backend/ai_processor.py`:

```python
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

        Ejemplo:
        Input: "Quiero ver películas de Spielberg"
        Output: "/add_actor Steven Spielberg"
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
```

**Paso 4: Tests PASAN**

```bash
pytest tests/test_ai_processor.py -v
```

**Paso 5: Actualizar bot.py para usar AIProcessor seguro**

En `bot.py`, en el método `__init__`:

```python
# Cargar Claude API key si está disponible
claude_api_key = os.getenv('CLAUDE_API_KEY')
self.ai_processor = AIProcessor(enabled=bool(claude_api_key))

if claude_api_key:
    self.security_manager.add_sensitive_key(claude_api_key)
```

**Paso 6: Commit**

```bash
git add backend/ai_processor.py tests/test_ai_processor.py bot.py
git commit -m "feat: secure Claude API integration with sanitization"
```

---

## Task 6: Crear documentation de seguridad

**Archivos:**
- Crear: `SECURITY.md` - Guía de seguridad

**Paso 1: Crear SECURITY.md**

Crear `SECURITY.md`:

```markdown
# 🔒 Guía de Seguridad

## Variables de Entorno Sensibles

### Requeridas
- `TELEGRAM_BOT_TOKEN` - Token del bot (nunca compartir)
- `TMDB_API_KEY` - API key de TMDb
- `TELEGRAM_USER_ID` - Tu ID en Telegram

### Opcionales (para IA)
- `CLAUDE_API_KEY` - API key de Claude (si usas IA)

## Mejores Prácticas

### 1. Nunca Commitees Secrets
```bash
# ✅ Bien
.env  # En .gitignore
.env.local  # En .gitignore

# ❌ Malo
git add .env
git commit -m "add env file"
```

### 2. Rotación de Keys
- Rota TMDb API key: https://www.themoviedb.org/settings/api
- Rota Telegram token: /revoke en BotFather
- Rota Claude API key: Regenera en https://console.anthropic.com

### 3. Producción vs Desarrollo

**Desarrollo:**
```bash
cp .env.example .env
# Editar con valores TEST (no reales)
```

**Producción:**
```bash
# NO uses .env en producción
# Usa variables de entorno del sistema o secrets manager
export TELEGRAM_BOT_TOKEN="xxx"
export TMDB_API_KEY="yyy"
export CLAUDE_API_KEY="zzz"

python bot.py
```

### 4. Logging Seguro

El bot sanitiza automáticamente logs:
- Reemplaza API keys con `***REDACTED***`
- Nunca loguea tokens completos
- Verificar logs no contienen secrets

```bash
grep -i "api_key\|token\|secret" /var/log/bot.log
# Esperado: ningún resultado o solo ***REDACTED***
```

### 5. Storage de Datos

Datos almacenados en `data/movies.json`:
- **Ahora:** Texto plano (agregar .env a .gitignore)
- **Futuro:** Considera encriptar si en servidor

Para encriptar (futuro):
```python
from cryptography.fernet import Fernet

# Generar key (una sola vez)
key = Fernet.generate_key()
# Guardar en .env: ENCRYPTION_KEY=<key>

# Usar en Storage
cipher = Fernet(os.getenv('ENCRYPTION_KEY'))
encrypted = cipher.encrypt(data)
```

### 6. Acceso a API

- TMDb API: Usa headers `Authorization: Bearer`
- Claude API: Usa SDK official (anthropic library)
- No pasar keys en URLs

## Auditoría de Seguridad

### Tests
```bash
# Ejecutar tests regularmente
pytest tests/ -v

# Verificar cobertura
pytest --cov=backend
```

### Código
```bash
# Buscar secrets accidentales
grep -r "api_key.*=" --include="*.py" .
grep -r "token.*=" --include="*.py" .

# Esperado: Solo en .env.example, security.py, tests
```

### Dependencias
```bash
# Verificar dependencias desactualizadas
pip list --outdated

# Actualizar
pip install --upgrade -r requirements.txt
```

## Reportar Problemas de Seguridad

Si encuentras un vulnerability:
1. NO lo publiques en Issues públicas
2. Contacta: ivan.denenberg@gmail.com
3. Proporciona:
   - Descripción del issue
   - Pasos para reproducir
   - Posible solución

## Cambios de Seguridad

v1.1 (2026-03-07):
- ✅ API keys ahora en headers (no URLs)
- ✅ Logging sanitizado automáticamente
- ✅ Timeouts en todas las requests
- ✅ Claude API secura (para futuro)

## Referencias

- [OWASP Top 10](https://owasp.org/Top10/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Telegram Bot Security](https://core.telegram.org/bots/api-security)
```

**Paso 2: Commit**

```bash
git add SECURITY.md
git commit -m "docs: add comprehensive security guide"
```

---

## Task 7: Actualizar .env.example con nuevas variables

**Archivos:**
- Modificar: `.env.example`

**Paso 1: Actualizar .env.example**

En `.env.example`:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here_get_from_botfather
TELEGRAM_USER_ID=your_telegram_user_id_get_from_userinfobot

# TMDb API
TMDB_API_KEY=your_tmdb_api_key_here_get_from_tmdb

# Claude API (OPCIONAL - para IA futura)
# Descomenta esta línea si quieres usar Claude AI
# CLAUDE_API_KEY=your_claude_api_key_here

# Encripción de datos (OPCIONAL - futuro)
# ENCRYPTION_KEY=generated_by_cryptography_fernet
```

**Paso 2: Commit**

```bash
git add .env.example
git commit -m "docs: update .env.example with security notes"
```

---

## Task 8: Actualizar requirements.txt con nuevas dependencias

**Archivos:**
- Modificar: `requirements.txt`

**Paso 1: Agregar dependencias opcionales**

En `requirements.txt`, agregar:

```txt
python-telegram-bot==20.7
requests==2.31.0
apscheduler==3.10.4
python-dotenv==1.0.0
pytest==7.4.3
pytest-cov==4.1.0

# Seguridad
cryptography==42.0.5  # Para encripción futura

# IA (OPCIONAL - descomentar para usar Claude)
# anthropic==0.28.0
```

**Paso 2: Actualizar README con instrucciones**

En `README.md`, agregar sección en "Instalación":

```markdown
### Integración IA (Opcional)

Para habilitar Claude AI:

```bash
pip install anthropic
```

Luego en `.env`:
```env
CLAUDE_API_KEY=your_api_key_here
```
```

**Paso 3: Commit**

```bash
git add requirements.txt README.md
git commit -m "docs: update dependencies with optional AI support"
```

---

## Task 9: Tests finales de seguridad

**Paso 1: Ejecutar todos los tests**

```bash
cd /home/ivan/projects/movies_series_notifier
pytest tests/ -v
```

Esperado: 50+ tests passing

**Paso 2: Verificar cobertura**

```bash
pytest --cov=backend --cov-report=term-missing
```

Esperado: >90% cobertura

**Paso 3: Buscar secrets accidentales en código**

```bash
grep -r "api_key\|token\|secret" --include="*.py" . | grep -v "test_\|\.env\|security.py"
```

Esperado: solo en comentarios o literales de test

**Paso 4: Commit**

```bash
git add .
git commit -m "test: all security tests passing and verified"
```

---

## Resumen de Cambios

### Riesgos Mitigados

| Riesgo | Severidad | Mitigación |
|--------|-----------|-----------|
| API keys en URLs | 🔴 ALTO | Usar headers + RequestManager |
| Logging no sanitizado | 🟡 MEDIO | SecurityManager sanitiza logs |
| Sin timeout | 🟢 BAJO | RequestManager enforce timeout=5 |
| Claude API insegura | 🔴 ALTO | AIProcessor usa SDK + sanitización |
| JSON sin encripción | 🟢 BAJO | Documentado para futuro |

### Archivos Nuevos
- `backend/security.py` - SecurityManager
- `backend/http_client.py` - RequestManager
- `SECURITY.md` - Guía de seguridad
- `tests/test_security.py` - Tests de seguridad
- `tests/test_http_client.py` - Tests de RequestManager
- `tests/test_ai_processor.py` - Tests de AIProcessor

### Archivos Modificados
- `backend/tmdb_client.py` - Usar headers en lugar de params
- `backend/ai_processor.py` - Integración Claude segura
- `bot.py` - Usar SecurityManager
- `.env.example` - Nuevas variables
- `requirements.txt` - Nuevas dependencias
- `README.md` - Instrucciones IA

---

