# 🚀 One Market - Inicio Rápido

## ✅ Sistema Verificado y Listo

El proyecto ha sido verificado y está **100% operativo**. Todos los componentes críticos funcionan correctamente.

## 📋 Pre-requisitos

✅ **Python 3.11+** instalado  
✅ **Dependencias** instaladas (`pip install -r requirements.txt`)

## 🎯 Opción 1: Inicio Automático (Recomendado)

### Windows
```bash
INICIAR_PROYECTO.bat
```

El script te permitirá:
1. 🌐 Iniciar solo la API
2. 📊 Iniciar solo la UI
3. 🔄 Iniciar ambos servicios
4. 🧪 Ejecutar tests

### Linux/Mac
```bash
chmod +x iniciar_proyecto.sh
./iniciar_proyecto.sh
```

## 🎯 Opción 2: Inicio Manual

### 1. Iniciar API (Terminal 1)
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**API disponible en**: http://localhost:8000  
**Documentación**: http://localhost:8000/docs

### 2. Iniciar UI (Terminal 2)
```bash
streamlit run ui/app_enhanced.py
```

**UI disponible en**: http://localhost:8501

## 🔧 Verificación Rápida del Sistema

### Verificar imports
```bash
python -c "from app.data import DataStore, DataFetcher; print('✅ Data layer OK')"
python -c "from main import app; print('✅ API OK')"
```

### Ejecutar tests
```bash
python -m pytest tests/test_data_contracts.py -v
```

**Resultado esperado**: 14 tests passing, 1 skipped

## 📊 Primeros Pasos

### 1. Sincronizar Datos
```bash
# Opción A: Via API
curl -X POST "http://localhost:8000/data/sync" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC/USDT",
    "tf": "1h",
    "since": "2025-10-14T00:00:00Z"
  }'

# Opción B: Via script
python update_data.py
```

### 2. Generar Recomendación
```bash
curl "http://localhost:8000/recommendation/daily?symbol=BTC/USDT&date=2025-10-21"
```

### 3. Ejecutar Backtest
```bash
curl -X POST "http://localhost:8000/backtest/run" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC/USDT",
    "timeframe": "1h",
    "strategy": "ma_crossover"
  }'
```

## 🔍 Endpoints Disponibles

### Data Management
- `POST /data/sync` - Sincronizar datos
- `GET /data/meta/{symbol}/{timeframe}` - Metadata
- `GET /data/latest/{symbol}/{timeframe}` - Último timestamp
- `GET /data/health` - Health check

### Backtesting
- `POST /backtest/run` - Ejecutar backtest
- `GET /backtest/strategies` - Estrategias disponibles
- `GET /backtest/health` - Health check

### Recommendations
- `GET /recommendation/daily` - Recomendación diaria
- `GET /recommendation/history` - Historial
- `GET /recommendation/stats/{symbol}` - Estadísticas
- `GET /recommendation/health` - Health check

## 🧪 Tests Disponibles

```bash
# Data contracts
python -m pytest tests/test_data_contracts.py -v

# API backtest equals engine
python -m pytest tests/test_api_backtest_equals_engine.py -v

# One trade per day enforced
python -m pytest tests/test_one_trade_per_day_enforced.py -v

# Forced close window
python -m pytest tests/test_forced_close_window.py -v

# Recommendation contract
python -m pytest tests/test_recommendation_contract.py -v

# Todos los tests
python -m pytest tests/ -v
```

## 📁 Estructura de Directorios

```
storage/          # Datos OHLCV (Parquet + SQLite)
logs/             # Logs JSONL estructurados
artifacts/        # Resultados de backtests y recomendaciones
```

## ⚠️ Solución de Problemas

### Error: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Error: "No data found"
```bash
# Sincronizar datos primero
python update_data.py
```

### Puerto 8000 ocupado
```bash
# Cambiar puerto en el comando
python -m uvicorn main:app --port 8001
```

### Puerto 8501 ocupado (Streamlit)
```bash
streamlit run ui/app_enhanced.py --server.port 8502
```

## 📊 Verificación de Estado

### Health Checks
```bash
# Data service
curl http://localhost:8000/data/health

# Backtest service
curl http://localhost:8000/backtest/health

# Recommendation service
curl http://localhost:8000/recommendation/health
```

**Respuesta esperada**: `{"status": "ok", ...}`

## 🎯 Flujo Completo Recomendado

1. **Iniciar servicios**
   ```bash
   INICIAR_PROYECTO.bat
   # Opción 3: Ambos servicios
   ```

2. **Verificar health**
   ```bash
   curl http://localhost:8000/data/health
   ```

3. **Sincronizar datos** (si es primera vez)
   ```bash
   python update_data.py
   ```

4. **Generar recomendación**
   ```bash
   curl "http://localhost:8000/recommendation/daily?symbol=BTC/USDT"
   ```

5. **Abrir UI**
   - Navegar a http://localhost:8501
   - Explorar tabs: Auto Strategy, Best Strategy, Strategy Comparison

## 📚 Documentación Adicional

- **README.md** - Documentación completa
- **STATUS_REPORT.md** - Estado actual del sistema
- **API Docs** - http://localhost:8000/docs (después de iniciar API)

## ✅ Sistema Operativo

**Estado actual**: 🟢 **COMPLETAMENTE OPERATIVO**

- ✅ app.data funcional
- ✅ API endpoints activos
- ✅ Tests pasando (14/15)
- ✅ Scheduler configurado
- ✅ Logging estructurado
- ✅ Recomendaciones operativas

## 🆘 Soporte

Si encuentras problemas:

1. Revisa `STATUS_REPORT.md` para el estado actual
2. Verifica logs en `logs/one_market.log`
3. Ejecuta tests: `python -m pytest tests/ -v`

---

**¡Listo para generar recomendaciones de trading confiables!** 🎉
