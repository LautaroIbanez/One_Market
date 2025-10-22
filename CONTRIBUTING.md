# Guía de Contribución

¡Gracias por tu interés en contribuir a One Market! Este documento proporciona guías y mejores prácticas.

## Código de Conducta

- Sé respetuoso y constructivo
- Acepta críticas constructivas
- Enfócate en lo mejor para la comunidad
- Muestra empatía hacia otros contribuidores

## Cómo Contribuir

### Reportar Bugs

Usa GitHub Issues e incluye:
- Descripción clara del problema
- Pasos para reproducir
- Comportamiento esperado vs actual
- Versión de Python, OS
- Stack trace si aplica

### Solicitar Features

Usa GitHub Issues con tag `enhancement`:
- Descripción del problema que resuelve
- Propuesta de solución
- Alternativas consideradas
- Ejemplos de uso

### Pull Requests

1. **Fork el repositorio**
```bash
git clone https://github.com/tu-usuario/one-market.git
cd one-market
```

2. **Crear rama**
```bash
git checkout -b feature/mi-feature
# o
git checkout -b fix/mi-bug-fix
```

3. **Hacer cambios**
- Sigue la guía de estilo
- Agrega tests
- Actualiza documentación

4. **Ejecutar tests**
```bash
pytest
pytest --cov=app
```

5. **Lint y format**
```bash
black app/ tests/
ruff check app/ tests/
mypy app/
```

6. **Commit**
```bash
git add .
git commit -m "feat: descripción clara del cambio"
```

Usa conventional commits:
- `feat:` Nueva feature
- `fix:` Bug fix
- `docs:` Cambios en documentación
- `test:` Agregar/modificar tests
- `refactor:` Refactoring
- `perf:` Mejoras de performance
- `chore:` Mantenimiento

7. **Push y crear PR**
```bash
git push origin feature/mi-feature
```

Luego crea el PR en GitHub.

## Guía de Estilo

### Python

Seguimos PEP 8 con modificaciones:
- Line length: 120 caracteres
- Use type hints
- Docstrings en formato Google

Ejemplo:
```python
def fetch_data(symbol: str, timeframe: str, since: int) -> List[OHLCVBar]:
    """Fetch OHLCV data from exchange.
    
    Args:
        symbol: Trading symbol (e.g., 'BTC/USDT')
        timeframe: Timeframe (e.g., '1h')
        since: Start timestamp in milliseconds
        
    Returns:
        List of OHLCVBar objects
        
    Raises:
        ValueError: If timeframe is invalid
    """
    ...
```

### Testing

- Usa pytest
- Fixtures en `conftest.py` si son compartidos
- Nombres descriptivos: `test_should_reject_future_timestamps`
- Test tanto happy path como edge cases
- Mock I/O externo (APIs, filesystem cuando sea apropiado)

Ejemplo:
```python
def test_ohlcv_bar_validates_high_price():
    """Test that high price must be >= open, low, close."""
    with pytest.raises(ValueError):
        OHLCVBar(
            timestamp=1697500000000,
            open=100.0,
            high=95.0,  # Invalid: high < open
            low=90.0,
            close=98.0,
            volume=1000.0,
            symbol="BTC/USDT",
            timeframe="1h"
        )
```

### Documentación

- README para overview
- Docstrings para módulos, clases, funciones públicas
- Type hints siempre
- Ejemplos en `examples/`

## Estructura de Epics

El proyecto sigue desarrollo por Epics (ver `EPICS.md`):

1. **Epic 1**: Fundaciones de Datos ✅
2. **Epic 2**: Estrategias Cuantitativas 🔄
3. **Epic 3**: Gestión de Riesgo
4. **Epic 4**: Ejecución
5. **Epic 5**: UI
6. **Epic 6**: API
7. **Epic 7**: DevOps

Contribuciones deben alinearse con el Epic actual o futuro.

## Proceso de Review

Los PRs serán revisados por:
- Calidad de código
- Tests adecuados
- Documentación actualizada
- Performance
- Compatibilidad con principios del proyecto

Cambios pueden ser solicitados antes de merge.

## Principios del Proyecto

1. **Modularidad**: Componentes desacoplados
2. **Reproducibilidad**: Mismos inputs → mismos outputs
3. **Performance**: <1s para señal diaria
4. **Testing**: >90% coverage
5. **Documentación**: Código autodocumentado + docs externos

## Setup para Desarrollo

```bash
# Clonar y entrar
git clone <repo>
cd one-market

# Virtual env
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar con dev dependencies
pip install -r requirements.txt

# Setup
python scripts/setup.py

# Tests
pytest

# Pre-commit (opcional pero recomendado)
# Instalar pre-commit hooks
# pip install pre-commit
# pre-commit install
```

## Recursos

- [README.md](README.md): Documentación principal
- [QUICKSTART.md](QUICKSTART.md): Guía de inicio
- [ARCHITECTURE.md](ARCHITECTURE.md): Arquitectura técnica
- [EPICS.md](EPICS.md): Roadmap
- [CHANGELOG.md](CHANGELOG.md): Historial de cambios

## Preguntas

Para preguntas, usa:
- GitHub Discussions para preguntas generales
- GitHub Issues para bugs/features
- Email a [pendiente] para temas privados

---

¡Gracias por contribuir a One Market! 🚀






