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
