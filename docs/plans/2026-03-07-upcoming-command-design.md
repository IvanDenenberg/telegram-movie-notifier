# Comando /upcoming - Diseño

> **Aprobado:** 2026-03-07

## Propósito

Permitir al usuario consultar qué películas, series y actores monitoreados tienen estrenos programados en los próximos 60 días.

## Especificación

### Comando y variantes

```
/upcoming              → Muestra todo (películas, series, actores)
/upcoming movies      → Solo películas
/upcoming series      → Solo series
/upcoming actors      → Solo actores
```

### Rango temporal

- **Desde:** Hoy (fecha actual del sistema)
- **Hasta:** Hoy + 60 días
- **Granularidad:** Incluye cualquier estreno dentro de este período

### Formato de salida

**Estructura:**
- Agrupado por tipo (películas, series, actores)
- Dentro de cada grupo, ordenado por fecha (más cercano primero)
- Cada ítem muestra: título + fecha de estreno

**Formato HTML:**
```
🎬 Películas (próximos 60 días):
• Dune 2 - 29 de febrero
• Avatar 4 - 15 de marzo

📺 Series:
• Succession S5 - 5 de marzo

👤 Actores:
• Tom Cruise - Top Gun 3 (1 de abril)
```

**Sin resultados:**
```
No hay estrenos en los próximos 60 días
```

## Flujo de ejecución

1. Usuario envía `/upcoming [filter]`
2. Parser detecta comando y extrae filtro (movies/series/actors o ninguno)
3. Handler `handle_upcoming(args)` se ejecuta:
   - Obtiene películas de storage
   - Obtiene actores de storage
   - Para cada película: consulta TMDb por fecha de estreno
   - Para cada actor: obtiene filmografía + TV credits con fechas
4. Filtra resultados en rango 60 días
5. Agrupa por tipo (si no hay filtro) o mantiene solo el tipo filtrado
6. Ordena por fecha dentro de cada grupo
7. Formatea mensaje HTML
8. Envía al usuario

## Integración técnica

### Módulos afectados

- **handlers.py**: Nuevo método `handle_upcoming(args)`
- **notifier.py**: Nuevo método `get_releases_in_range(days)` para reutilizar lógica
- **tmdb_client.py**: Ya tiene métodos necesarios (search_movie, get_actor_filmography, etc.)
- **tests**: Tests para nuevo handler

### Métodos nuevos

**handlers.py:**
```python
def handle_upcoming(self, args: List[str]) -> str:
    """Handle /upcoming command with optional filter"""
    # Determinar filtro (all, movies, series, actors)
    # Obtener releases en rango de 60 días
    # Formatear y retornar mensaje HTML
```

**notifier.py:**
```python
def get_releases_in_range(self, days: int, filter_type: str = "all") -> Dict[str, List]:
    """Get releases for movies/actors within N days, grouped by type"""
    # Retorna: {"movies": [...], "series": [...], "actors": [...]}
```

### Dependencias

- Métodos existentes de TMDbClient (search_movie, get_actor_filmography, etc.)
- Storage.get_movies() y Storage.get_actors()
- Utilidades de fecha para cálculos de rango

## Casos especiales

1. **Sin datos:** Si storage está vacío → "No hay estrenos en los próximos 60 días"
2. **Múltiples estrenos mismo día:** Listar todos, ordenados alfabéticamente
3. **Películas/actores sin fecha:** Ignorar (no mostrar)
4. **Actor sin películas/series:** No mostrar en la sección de actores
5. **Filtro inválido:** Retornar help o usar default "all"

## Testing

Tests necesarios:
- `test_handle_upcoming_all` - Sin filtro, muestra todo
- `test_handle_upcoming_movies` - Solo películas
- `test_handle_upcoming_series` - Solo series
- `test_handle_upcoming_actors` - Solo actores
- `test_handle_upcoming_empty` - Sin datos
- `test_get_releases_in_range` - Lógica de rango de fechas
- `test_releases_sorted_by_date` - Verificar ordenamiento

## Validación

✅ **Usuario aprobó:**
- Comando: `/upcoming` + variantes
- Rango: 60 días
- Agrupación: Por tipo
- Información: Título + fecha
- Ordenamiento: Por fecha ascendente
- Sin resultados: Mensaje simple
