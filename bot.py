import os
import asyncio
import logging
from datetime import time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)
from backend.handlers import CommandHandler as BotCommandHandler
from backend.parser import MessageParser
from backend.ai_processor import AIProcessor
from backend.notifier import Notifier
from backend.security import SecurityManager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
# Logger global será reemplazado por instancia en __init__
# logger = logging.getLogger(__name__)


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

        # Inicializar componentes
        self.storage_path = "data/movies.json"
        self.command_handler = BotCommandHandler(self.tmdb_api_key, self.storage_path)
        self.parser = MessageParser()

        # Cargar Claude API key si está disponible
        claude_api_key = os.getenv('CLAUDE_API_KEY')
        self.ai_processor = AIProcessor(enabled=bool(claude_api_key))

        if claude_api_key:
            self.security_manager.add_sensitive_key(claude_api_key)

        self.notifier = Notifier(self.tmdb_api_key, self.storage_path)

        # Configurar callback de notificaciones
        self.app = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mensaje de bienvenida"""
        welcome_message = """¡Bienvenido a Movie & Series Notifier! 🎬📺

Soy tu bot de notificaciones de películas y series. Puedo ayudarte a:
✓ Agregar películas y series a tu lista
✓ Monitorear actores favoritos
✓ Notificarte sobre nuevos estrenos

Usa /help para ver todos los comandos disponibles."""

        await update.message.reply_text(welcome_message)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesar mensaje: comando o texto libre"""
        try:
            message_text = update.message.text
            parsed = self.parser.parse(message_text)

            if parsed["type"] == "command":
                response = await self._handle_command(parsed)
            else:
                # Intentar procesar con IA si está habilitada
                ai_result = self.ai_processor.process(parsed["text"])
                if ai_result:
                    # Re-parsear el resultado de IA como comando
                    parsed = self.parser.parse(ai_result)
                    response = await self._handle_command(parsed)
                else:
                    response = "❌ No entiendo ese mensaje. Usa /help para ver los comandos disponibles."

            await update.message.reply_text(response, parse_mode="HTML")
        except Exception as e:
            sanitized_error = self.security_manager.sanitize(str(e))
            self.logger.error(f"Error procesando mensaje: {sanitized_error}")
            await update.message.reply_text("❌ Hubo un error procesando tu mensaje.")

    async def _handle_command(self, parsed: dict) -> str:
        """Despachar comando a handlers según type"""
        command = parsed.get("command", "").lower()
        args = parsed.get("args", [])

        try:
            if command == "start":
                return "Bot iniciado. Usa /help para ver los comandos."
            elif command == "add":
                return self.command_handler.handle_add(args)
            elif command == "add_actor":
                return self.command_handler.handle_add_actor(args)
            elif command == "list":
                return self.command_handler.handle_list(args)
            elif command == "remove":
                return self.command_handler.handle_remove(args)
            elif command == "help":
                return self.command_handler.handle_help()
            elif command == "upcoming":
                return self.command_handler.handle_upcoming(args)
            elif command == "add_by_id":
                return self.command_handler.handle_add_by_id(args)
            else:
                return f"❌ Comando desconocido: /{command}. Usa /help para ver los comandos disponibles."
        except Exception as e:
            self.logger.error(f"Error en comando {command}: {e}")
            return f"❌ Error ejecutando comando: {str(e)}"

    async def check_releases_job(self):
        """Job que corre cada domingo a las 12 PM para chequear nuevos estrenos"""
        try:
            self.logger.info("Ejecutando check de nuevos estrenos...")

            # Obtener nuevos estrenos
            releases = self.notifier.check_new_releases()

            if releases and self.telegram_user_id:
                for release in releases:
                    # Obtener datos del release
                    release_data = release.get("data", {})
                    media_type = release.get("type", "movie")

                    # Formatear notificación
                    message = self.notifier.format_notification(release_data, media_type)

                    # Enviar notificación
                    try:
                        await self.app.bot.send_message(
                            chat_id=self.telegram_user_id,
                            text=message,
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        self.logger.error(f"Error enviando notificación: {e}")
            else:
                self.logger.info("No hay nuevos estrenos o TELEGRAM_USER_ID no está configurado")
        except Exception as e:
            self.logger.error(f"Error en check_releases_job: {e}")

    def setup_scheduler(self):
        """Configurar APScheduler para ejecutar job cada domingo a las 12 PM"""
        scheduler = AsyncIOScheduler()

        # Agregar job cada domingo a las 12:00 PM
        scheduler.add_job(
            self.check_releases_job,
            'cron',
            day_of_week=6,  # 6 = domingo (0=lunes, 6=domingo)
            hour=12,
            minute=0,
            id='check_releases_weekly'
        )

        scheduler.start()
        self.logger.info("Scheduler configurado para ejecutar cada domingo a las 12:00 PM")

    async def setup_handlers(self):
        """Agregar handlers de Telegram"""
        # Handler para /start
        self.app.add_handler(CommandHandler("start", self.start))

        # Handlers para comandos de control
        self.app.add_handler(CommandHandler("add", self._command_wrapper("add")))
        self.app.add_handler(CommandHandler("add_actor", self._command_wrapper("add_actor")))
        self.app.add_handler(CommandHandler("add_by_id", self._command_wrapper("add_by_id")))
        self.app.add_handler(CommandHandler("list", self._command_wrapper("list")))
        self.app.add_handler(CommandHandler("remove", self._command_wrapper("remove")))
        self.app.add_handler(CommandHandler("help", self._command_wrapper("help")))
        self.app.add_handler(CommandHandler("upcoming", self._command_wrapper("upcoming")))

        # Handler para mensajes de texto libre
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    def _command_wrapper(self, command_name: str):
        """Wrapper para convertir comandos de Telegram en mensajes parseables"""
        async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            # Reconstruir el mensaje como si fuera texto libre parseado
            args = context.args

            # Crear parsed como si hubiera venido del parser
            parsed = {
                "type": "command",
                "command": command_name,
                "args": args
            }

            response = await self._handle_command(parsed)
            if update.message:
                await update.message.reply_text(response, parse_mode="HTML")

        return handler

    async def run(self):
        """Iniciar bot"""
        try:
            # Crear aplicación
            self.app = Application.builder().token(self.telegram_token).build()

            # Setup handlers
            await self.setup_handlers()

            # Configurar scheduler
            self.setup_scheduler()

            # Iniciar bot
            self.logger.info("Iniciando Movie Notifier Bot...")
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()

            self.logger.info("Bot en funcionamiento. Presiona Ctrl+C para detener.")

            # Mantener bot activo
            await asyncio.Event().wait()
        except Exception as e:
            self.logger.error(f"Error iniciando bot: {e}")
            raise
        finally:
            if self.app:
                await self.app.stop()
                await self.app.shutdown()


async def main():
    """Función principal"""
    bot = MovieNotifierBot()
    await bot.run()


if __name__ == "__main__":
    # Logger global para la función main
    logger = logging.getLogger(__name__)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}")
