# One Market - UI Guide

## Ejecutar el Dashboard

### Opción 1: Modo Standalone (Sin API)
```bash
streamlit run ui/app.py
```

Este modo carga datos directamente desde el storage local.

### Opción 2: Modo API Connected
```bash
# Terminal 1: Iniciar API
python main.py

# Terminal 2: Iniciar UI
streamlit run ui/app_api_connected.py
```

Este modo se conecta al backend FastAPI para obtener datos y decisiones en tiempo real.

---

## Características de la UI

### 🎨 Panel de Configuración (Sidebar)

**Selección de Símbolo y Timeframe**:
- Symbol: BTC/USDT, ETH/USDT, etc.
- Timeframe: 15m, 1h, 4h, 1d
- Trading Mode: Paper / Live

**Risk Management**:
- Risk per Trade: 0.5% - 5.0%
- Capital: Configurable
- Target R/R Ratio: 1.0 - 5.0

**TP/SL Configuration**:
- Method: ATR / Swing / Hybrid
- ATR Multipliers (SL/TP)
- Customizable parameters

---

### 📍 Panel "Today's Signal"

Muestra:
- **Direction**: 🟢 LONG / 🔴 SHORT / ⚪ FLAT
- **Confidence**: Porcentaje de confianza
- **Market Price**: Precio actual
- **Status**: ✅ EXECUTE / ⏸️ SKIP

**Strategy Breakdown**:
- MA Crossover signal
- RSI Regime signal
- Triple EMA signal

---

### 💰 Trading Details (Si hay señal)

**Entry**:
- Entry Price (optimizado con VWAP)
- Entry Mid (VWAP reference)
- Entry Spread

**Stops**:
- Stop Loss price
- Take Profit price
- R/R Ratio calculado

**Position Sizing**:
- Quantity (units)
- Notional Value ($)
- Risk Amount ($)

---

### 🧭 Multi-Horizon Analysis

**Short-term (Today)**:
- Signal direction
- Entry timing (immediate/pullback/wait)
- Volatility state
- Recommended risk %

**Medium-term (Week)**:
- Trend direction
- EMA200 position
- Filter recommendation
- RSI weekly

**Long-term (Regime)**:
- Market regime (bull/bear/neutral)
- Volatility regime
- Exposure recommendation
- Regime probability

**Consensus**:
- Consensus direction across all horizons
- Overall confidence score
- Final risk recommendation

---

### 📈 Interactive Chart

**Candlestick Chart** (últimos 60 bars):
- OHLC candlesticks
- Entry price line (azul, dash)
- Stop loss line (rojo, dot)
- Take profit line (verde, dot)
- Entry band zone (rectángulo azul claro)

**Controls**:
- Zoom
- Pan
- Hover details
- Range selector

---

### 📊 Performance Metrics (12M Rolling)

**Métricas Principales**:
- CAGR (Compound Annual Growth Rate)
- Sharpe Ratio
- Maximum Drawdown
- Win Rate
- Profit Factor
- Total Return

**Equity Curve**:
- Gráfico de evolución del capital
- Últimos 12 meses
- Zoom interactivo

**Drawdown Chart**:
- Visualización de drawdowns
- Highlighted en rojo
- Fill to zero

---

### ℹ️ Data Status

- Bars Loaded: Cantidad de barras
- Latest Data: Timestamp del último dato
- Data Age: Antigüedad de los datos en minutos

---

## 🎯 Workflow Típico

### 1. Configurar
- Seleccionar símbolo (ej: BTC/USDT)
- Seleccionar timeframe (ej: 1h)
- Ajustar risk % si necesario
- Seleccionar estrategias

### 2. Generar Decisión
- Click en "Generate Decision"
- Esperar análisis (~2-3 segundos)

### 3. Revisar Resultado
- Ver señal (LONG/SHORT/FLAT)
- Revisar confidence score
- Validar entry, SL, TP
- Revisar multi-horizon advice

### 4. Análisis
- Revisar gráfico con niveles
- Ver performance metrics
- Analizar equity curve
- Revisar drawdowns

### 5. Acción
- Si EXECUTE: Anotar detalles
- Si SKIP: Entender razón
- Monitorear durante el día

---

## 🔌 Conexión con API

### Modo API Connected (app_api_connected.py)

**Ventajas**:
- ✅ Data actualizada en tiempo real
- ✅ Jobs programados funcionando
- ✅ Scheduler automático
- ✅ Event logging
- ✅ Paper trading DB actualizada

**Requisitos**:
- API debe estar corriendo (python main.py)
- SCHEDULER_ENABLED=true (opcional)

**Endpoints usados**:
- GET /health - Health check
- GET /symbols - Lista de símbolos
- GET /strategies - Lista de estrategias
- POST /decision - Genera decisión diaria

---

## 📸 Screenshots

### Dashboard Principal
![Dashboard Main]()  
*Vista principal con signal, chart y metrics*

### Multi-Horizon Analysis
![Multi-Horizon]()  
*Análisis en 3 horizontes temporales*

### Interactive Chart
![Chart with Entry Band]()  
*Chart con entry band, SL y TP*

---

## 🎨 Temas y Personalización

### Cambiar Tema
```bash
streamlit run ui/app.py --theme.base light
streamlit run ui/app.py --theme.base dark
```

### Configuración .streamlit/config.toml
```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

---

## 🐛 Troubleshooting

### "API Not Reachable"
- Verificar que API está corriendo: `python main.py`
- Verificar URL: `http://localhost:8000`
- Check firewall

### "No data available"
- Ejecutar: `python examples/example_fetch_data.py`
- Verificar storage/ directory
- Check symbol/timeframe combination

### "Insufficient data"
- Need mínimo 100 bars
- Fetch más datos históricos
- Reducir timeframe

---

## 🚀 Performance

### Tiempos de Respuesta
- Signal Generation: < 1s
- Decision Making: < 2s
- Chart Rendering: < 500ms
- API Calls: < 3s total

### Optimizaciones
- @st.cache_data para datos (TTL 5 min)
- Plotly para gráficos rápidos
- Lazy loading de componentes
- Efficient data queries

---

## 📖 Recursos

- **Streamlit Docs**: https://docs.streamlit.io
- **Plotly Docs**: https://plotly.com/python/
- **One Market API**: http://localhost:8000/docs

---

**Version**: 1.0.0  
**Last Updated**: Octubre 2024

