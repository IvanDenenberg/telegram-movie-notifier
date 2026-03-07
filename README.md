# Movie & Series Notifier 🎬📺

Bot de Telegram para recibir notificaciones automáticas sobre estrenos de películas y series en Argentina.

---

## Características ✨

- ✅ **Agregar películas y series** a tu lista de monitoreo
- ✅ **Monitorear actores y directores** favoritos
- ✅ **Notificaciones automáticas semanales** sobre nuevos estrenos
- ✅ **100% Gratuito** - Usa TMDb API gratuita
- ✅ **Preparado para IA** - Integración futura con Claude API
- ✅ **Storage ligero** - Almacenamiento en JSON, sin base de datos

---

## Requisitos 📋

- **Python 3.9+**
- **Telegram Bot Token** (obtén desde BotFather)
- **TMDb API Key** (obtén gratis desde TMDb)

---

## Instalación 🚀

### 1. Clonar el repositorio

```bash
git clone <repo-url>
cd movies_series_notifier
```

### 2. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo `.env.example` a `.env`:

```bash
cp .env.example .env
```

### 5. Obtener las claves necesarias

#### Telegram Bot Token
1. Abre Telegram y busca **@BotFather**
2. Escribe `/newbot` y sigue las instrucciones
3. Copia el token generado

#### TMDb API Key
1. Ve a [TMDb](https://www.themoviedb.org/settings/api)
2. Solicita una API Key (gratis)
3. Copia tu clave

#### Telegram User ID
1. Busca **@userinfobot** en Telegram
2. Escribe `/start`
3. Te mostrará tu User ID

Edita `.env` y completa:

```env
TELEGRAM_BOT_TOKEN=tu_token_aqui
TMDB_API_KEY=tu_api_key_aqui
TELEGRAM_USER_ID=tu_user_id_aqui
```

### 6. Ejecutar el bot

```bash
python bot.py
```

El bot estará activo y listo para recibir comandos.

---

## Comandos Disponibles 🤖

| Comando | Uso | Ejemplo |
|---------|-----|---------|
| `/start` | Mensaje de bienvenida | `/start` |
| `/add` | Agregar película o serie | `/add "Dune"` |
| `/add_actor` | Monitorear un actor | `/add_actor "Timothée Chalamet"` |
| `/list` | Ver tus películas y actores | `/list` |
| `/remove` | Eliminar película o serie | `/remove "Dune"` |
| `/help` | Ver todos los comandos | `/help` |

### Ejemplos de uso

```
/add "Avatar: La forma del agua"
/add_actor "Leonardo DiCaprio"
/list
/remove "Película que no interesa"
/help
```

---

## Cómo funciona ⚙️

### Flujo principal

1. **Usuario agrega contenido** - Envía `/add "Título"` o `/add_actor "Nombre"`
2. **Bot busca en TMDb** - Valida el título contra la base de datos de TMDb
3. **Almacena en JSON** - Guarda la película/actor en `data/movies.json`
4. **Chequeo semanal** - Cada 7 días, el bot revisa TMDb por estrenos
5. **Notificación** - Envía un mensaje con los nuevos estrenos
6. **Actualización** - Marca como notificado para evitar duplicados

### Procesamiento de mensajes

```
Mensaje de usuario
       ↓
Parser (identifica comando o texto)
       ↓
¿AI habilitada? → Procesar con Claude (futuro)
       ↓
Handlers (ejecutan acción)
       ↓
Respuesta al usuario
```

---

## Estructura de carpetas 📂

```
movies_series_notifier/
├── bot.py                      # Bot principal
├── requirements.txt            # Dependencias
├── .env.example               # Variables de entorno (ejemplo)
├── .gitignore                 # Archivos ignorados por git
│
├── backend/
│   ├── __init__.py
│   ├── handlers.py            # Handlers de comandos
│   ├── parser.py              # Parser de mensajes
│   ├── storage.py             # Gestión de JSON
│   ├── tmdb_client.py         # Cliente de TMDb API
│   ├── notifier.py            # Lógica de notificaciones
│   └── ai_processor.py        # Stub para integración IA
│
├── tests/
│   ├── __init__.py
│   ├── test_handlers.py       # Tests para handlers
│   ├── test_parser.py         # Tests para parser
│   ├── test_storage.py        # Tests para storage
│   ├── test_notifier.py       # Tests para notifier
│   └── test_tmdb_client.py    # Tests para TMDb
│
├── data/
│   └── movies.json            # Almacenamiento de datos (generado)
│
└── docs/
    └── plans/                 # Documentación de diseño
```

---

## Testing 🧪

### Ejecutar todos los tests

```bash
pytest tests/ -v
```

### Tests con cobertura de código

```bash
pytest --cov=backend tests/
```

### Ejecutar test específico

```bash
pytest tests/test_handlers.py -v
```

---

## Roadmap 🗺️

- [ ] **Integración Claude API** - Usar IA para respuestas más inteligentes
- [ ] **Soporte más países** - Expandir a otros mercados latinoamericanos
- [ ] **Más detalles** - Mostrar director, sinopsis, calificación
- [ ] **Base de datos SQLite** - Migrar de JSON para mejor escalabilidad
- [ ] **Desplegar en servidor** - Correr en VPS (Heroku, Railway, etc)
- [ ] **Notificaciones por imagen** - Mostrar póster de película
- [ ] **Filtros por género** - Recibir solo ciertos géneros

---

## Integración IA Futura 🤖

El bot está preparado para integración con Claude API. Actualmente el procesador de IA está deshabilitado, pero puede activarse.

### Cómo activar

En `bot.py`, cambiar:

```python
self.ai_processor = AIProcessor(enabled=False)
```

A:

```python
self.ai_processor = AIProcessor(enabled=True)
```

Luego establecer tu clave de Claude:

```env
CLAUDE_API_KEY=tu_clave_aqui
```

### Ejemplo de conversación futura

```
Usuario: "Quiero agregar todas las películas de Avatar"

Claude IA: Identifica que es una búsqueda múltiple
         ↓
Bot: "Encontré 2 películas Avatar:
     1. Avatar (2009)
     2. Avatar: La forma del agua (2022)

     ¿Cuál agregamos?"

Usuario: "Ambas"

Bot: "✅ Avatar (2009) agregada
     ✅ Avatar: La forma del agua (2022) agregada"
```

---

## Troubleshooting 🔧

### "TELEGRAM_BOT_TOKEN y TMDB_API_KEY son requeridos"

**Solución:** Verifica que completaste correctamente el archivo `.env` con tus claves.

```bash
cat .env  # Verifica que las claves estén presentes
```

### "Error: No connection to Telegram"

**Solución:** Verifica tu conexión a internet y que el token sea válido.

```bash
# Intenta nuevamente
python bot.py
```

### TMDb no encuentra la película

**Solución:** El título debe existir en TMDb. Intenta con el título en inglés o busca en [TMDb](https://www.themoviedb.org/) primero.

```
/add "The Matrix"  # Mejor que "Matrix" (más específico)
```

### No recibo notificaciones

**Solución:** Verifica que `TELEGRAM_USER_ID` esté correctamente configurado.

```bash
# En tu .env
TELEGRAM_USER_ID=123456789  # Debe ser un número válido
```

### Tests fallando

**Solución:** Limpia la caché y reinstala dependencias.

```bash
rm -rf __pycache__ .pytest_cache
pip install -r requirements.txt --upgrade
pytest tests/ -v
```

---

## Dependencias 📦

| Librería | Versión | Propósito |
|----------|---------|-----------|
| python-telegram-bot | 20.7 | API de Telegram |
| requests | 2.31.0 | Requests HTTP |
| apscheduler | 3.10.4 | Tareas programadas |
| python-dotenv | 1.0.0 | Variables de entorno |
| pytest | 7.4.3 | Testing |
| pytest-cov | 4.1.0 | Cobertura de tests |

---

## Licencia 📄

MIT License - Eres libre de usar, modificar y distribuir este proyecto.

---

## Autor 👨‍💻

Creado por **Ivan**

---

## Contribuciones 🤝

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/mejora`)
3. Commit tus cambios (`git commit -m "Agrega mejora"`)
4. Push a la rama (`git push origin feature/mejora`)
5. Abre un Pull Request

---

## Soporte 💬

Si tienes preguntas o encuentras problemas:

1. Revisa la sección **Troubleshooting**
2. Abre un issue en GitHub
3. Contacta al autor

---

**¡Disfruta recibiendo notificaciones de tus películas y series favoritas!** 🍿📺
