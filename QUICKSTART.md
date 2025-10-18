# One Market - Quick Start Guide

Esta guía te ayudará a poner en marcha One Market en menos de 5 minutos.

## Paso 1: Requisitos

Asegúrate de tener instalado:
- Python 3.11 o superior
- pip (gestor de paquetes Python)

Verifica tu versión de Python:
```bash
python --version
```

## Paso 2: Instalación

### Clonar el repositorio
```bash
git clone <repo-url>
cd One_Market
```

### Crear entorno virtual (recomendado)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### Instalar dependencias
```bash
pip install -r requirements.txt
```

## Paso 3: Configuración Inicial

### Ejecutar setup
```bash
python scripts/setup.py
```

Este script:
- ✅ Crea directorios necesarios
- ✅ Valida configuración
- ✅ Verifica dependencias

### Configurar variables de entorno (opcional)
```bash
# Copiar archivo de ejemplo
copy env.example .env  # Windows
cp env.example .env    # Linux/Mac

# Editar .env con tu editor favorito
# Solo necesario si quieres usar APIs privadas
```

## Paso 4: Primer Uso - Fetch de Datos

### Opción A: Usar script de ejemplo
```bash
python examples/example_fetch_data.py
```

Este script descargará datos de BTC/USDT de los últimos 7 días.

### Opción B: Código Python personalizado
```python
from datetime import datetime, timedelta
from app.data.fetch import DataFetcher
from app.data.store import DataStore

# Inicializar componentes
fetcher = DataFetcher(exchange_name="binance")
store = DataStore()

# Configurar parámetros
symbol = "ETH/USDT"
timeframe = "1h"
days_back = 3
since = int((datetime.utcnow() - timedelta(days=days_back)).timestamp() * 1000)

# Fetch incremental
print(f"Fetching {symbol} {timeframe}...")
bars = fetcher.fetch_incremental(symbol, timeframe, since)
print(f"Downloaded {len(bars)} bars")

# Validar datos
validation = fetcher.validate_data(bars)
print(f"Validation: OK={validation.is_valid}, Gaps={validation.gap_count}")

# Guardar
stats = store.write_bars(bars)
print(f"Saved to {len(stats)} partitions")
```

## Paso 5: Verificar Datos

### Leer datos almacenados
```bash
python examples/example_read_data.py
```

### O usar Python
```python
from app.data.store import DataStore

store = DataStore()

# Ver qué hay almacenado
symbols = store.list_stored_symbols()
print(f"Stored: {symbols}")

# Leer datos
symbol, timeframe = symbols[0]
bars = store.read_bars(symbol, timeframe)
print(f"Read {len(bars)} bars")

# Ver metadata
metadata = store.get_metadata(symbol, timeframe)
print(f"Records: {metadata.record_count}")
print(f"Range: {metadata.first_timestamp} to {metadata.last_timestamp}")
```

## Paso 6: Health Check

Verifica que todo funciona correctamente:
```bash
python scripts/health_check.py
```

## Paso 7: Probar Módulos Core (Epic 2) ✅

Ejecuta el ejemplo completo de módulos cuantitativos:
```powershell
# Windows PowerShell (usar .\ antes del comando)
.\run_example.bat examples\example_core_usage.py

# O manualmente
$env:PYTHONPATH="$PWD"
python examples\example_core_usage.py
```

Este ejemplo demuestra:
- ✅ Timeframes y conversiones
- ✅ Trading calendar (ventanas A/B)
- ✅ Risk management (ATR, SL/TP, position sizing)
- ✅ Performance metrics
- ✅ Prevención de lookahead bias

## Paso 8: Tests (opcional pero recomendado)

Ejecuta los tests para asegurar que todo está correcto:
```powershell
# Windows PowerShell
.\run_tests.bat

# O manualmente
$env:PYTHONPATH="$PWD"
python -m pytest

# Con output detallado
.\run_tests.bat -v

# Con cobertura
.\run_tests.bat --cov=app --cov-report=html

# Solo tests de Epic 2
.\run_tests.bat tests/test_core_*.py -v
```

## Uso Avanzado

### Fetch de múltiples símbolos
```python
symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
timeframe = "4h"

for symbol in symbols:
    print(f"Processing {symbol}...")
    bars = fetcher.fetch_incremental(symbol, timeframe, since)
    store.write_bars(bars)
```

### Diferentes timeframes
```python
timeframes = ["1h", "4h", "1d"]
symbol = "BTC/USDT"

for tf in timeframes:
    print(f"Processing {symbol} {tf}...")
    bars = fetcher.fetch_incremental(symbol, tf, since)
    store.write_bars(bars)
```

### Lectura con filtros temporales
```python
from datetime import datetime, timedelta

# Últimas 24 horas
end = int(datetime.utcnow().timestamp() * 1000)
start = end - (24 * 60 * 60 * 1000)

bars = store.read_bars(
    "BTC/USDT",
    "1h",
    start_timestamp=start,
    end_timestamp=end
)
```

## Comandos Útiles

### Con Makefile (Linux/Mac)
```bash
make install      # Instalar dependencias
make test        # Ejecutar tests
make test-cov    # Tests con cobertura
make lint        # Verificar código
make format      # Formatear código
make clean       # Limpiar cache
make run-example # Ejecutar ejemplo
```

### Sin Makefile (Windows)
```bash
pip install -r requirements.txt
pytest
pytest --cov=app
ruff check app/
black app/
```

## Estructura de Datos Almacenados

Tus datos se guardan en:
```
storage/
└── symbol=BTC-USDT/
    └── tf=1h/
        └── year=2024/
            └── month=10/
                └── data.parquet
```

Cada partition es un archivo parquet comprimido que contiene:
- timestamp (int64)
- open, high, low, close, volume (float64)
- symbol, timeframe (string)

## Troubleshooting

### Error: "Module not found"
```bash
# Asegúrate de estar en el entorno virtual
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt
```

### Error: "Exchange not available"
Verifica tu conexión a internet. El módulo usa APIs públicas de Binance por defecto.

### Error: "Rate limit exceeded"
Reduce la frecuencia de requests o espera 60 segundos. El rate limiter maneja esto automáticamente.

### Datos con gaps
Es normal que haya gaps en datos históricos. Configura `ALLOW_GAPS=true` en `.env` para permitirlos.

## Módulos Core Disponibles (Epic 2) ✅

Ya puedes usar estos módulos en tu código:

### Timeframes
```python
from app.core.timeframes import Timeframe, get_bars_per_day

tf = Timeframe.H1
print(f"Bars per day: {get_bars_per_day('1h')}")  # 24
```

### Trading Calendar
```python
from app.core.calendar import TradingCalendar

calendar = TradingCalendar()
if calendar.is_trading_hours():
    window = calendar.get_current_window()
    print(f"Current window: {window}")  # "A" o "B"
```

### Risk Management
```python
from app.core.risk import compute_levels, calculate_position_size_fixed_risk

# Calcular SL/TP basados en ATR
levels = compute_levels(entry_price=50000, atr=1000, side="long")

# Calcular tamaño de posición
pos = calculate_position_size_fixed_risk(
    capital=100000,
    risk_pct=0.02,  # 2% risk
    entry_price=levels.entry_price,
    stop_loss=levels.stop_loss
)
print(f"Position: {pos.quantity} units @ ${levels.entry_price}")
```

### Prevención de Lookahead
```python
from app.core.utils import prevent_lookahead

# CRÍTICO para backtesting confiable
df = prevent_lookahead(df, signal_column='signal')
```

## Próximos Pasos

Con Epic 1 ✅ y Epic 2 ✅ completadas:

1. **Epic 3**: Sistema de señales (indicadores + estrategias)
2. **Epic 4**: Backtesting engine
3. **Epic 5**: API REST con FastAPI
4. **Epic 6**: Dashboard Streamlit

## Soporte

Para issues, consulta:
- README.md - Documentación completa
- tests/ - Ejemplos de uso
- examples/ - Scripts de ejemplo

## Recursos

- Documentación ccxt: https://docs.ccxt.com/
- PyArrow docs: https://arrow.apache.org/docs/python/
- Pydantic docs: https://docs.pydantic.dev/

---

¡Felicitaciones! Ya tienes One Market funcionando 🚀


