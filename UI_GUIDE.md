# One Market - UI Guide v2.0

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

## Navegación por Pestañas (Nuevo en v2.0)

El dashboard ahora está organizado en **dos pestañas principales**:

### 🎯 Trading Plan (Vista Rápida)
**Propósito**: Decisión rápida y ejecución del trade diario.

**Contenido**:
- Indicador de confianza del sistema (semáforo: 🟢 Alta / 🟡 Media / 🔴 Baja)
- Señal del día (LONG/SHORT/FLAT) con nivel de confianza
- Plan de trade completo (entrada, SL, TP, tamaño de posición)
- Estado de ventana de trading (Ventana A/B o fuera de horario)
- Gráfico de precio con niveles marcados
- Botones de acción (Paper Trade / Live Trade / Guardar Plan)

**Ideal para**: Revisión matutina, decisión rápida, ejecución directa.

### 📊 Deep Dive (Análisis Detallado)
**Propósito**: Análisis profundo y métricas históricas.

**Contenido**:
- Análisis multi-horizonte (corto/medio/largo plazo)
- Métricas de performance completas (12 meses)
- Curva de equity y drawdown
- Desglose por estrategia individual
- Pesos de combinación de señales
- Trades históricos (próximamente)
- Parámetros de estrategias
- Estado detallado de datos

**Ideal para**: Análisis de fin de semana, ajuste de parámetros, evaluación de rendimiento.

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

### 📍 Indicador de Confianza (Nuevo)

**Sistema de semáforo basado en backtest rolling**:

🟢 **ALTA** (Score ≥ 75/100):
- Sharpe > 1.5
- Win Rate > 60%
- Max Drawdown < 5%
- **Acción recomendada**: Seguir señal con confianza

🟡 **MEDIA** (Score 50-74):
- Sharpe 0.5-1.5
- Win Rate 50-60%
- Max Drawdown 5-15%
- **Acción recomendada**: Seguir señal con precaución

🔴 **BAJA** (Score < 50):
- Sharpe < 0.5
- Win Rate < 50%
- Max Drawdown > 15%
- **Acción recomendada**: Considerar skip o reducir tamaño

**Cálculo**:
El score se calcula combinando métricas del backtest de los últimos 12 meses:
- 40 puntos por Sharpe ratio
- 30 puntos por Win rate
- 30 puntos por control de drawdown

---

### 📍 Señal del Día

**En Trading Plan Tab**:
- **Dirección**: 🟢 LONG / 🔴 SHORT / ⚪ FLAT
- **Confianza Señal**: Nivel de consenso entre estrategias
- **Precio Actual**: Precio de mercado
- **Estado**: ✅ EJECUTAR / ⏸️ SKIP

**En Deep Dive Tab - Strategy Breakdown**:
- MA Crossover signal individual
- RSI Regime signal individual
- Triple EMA signal individual
- Pesos de cada estrategia en la combinación

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

### Workflow Matutino (Trading Plan Tab) ⏱️ 2-3 minutos

1. **Abrir Dashboard** (09:00 AM)
   - Configurar símbolo y timeframe en sidebar
   - Ir a tab "🎯 Trading Plan"

2. **Revisar Confianza** (30 segundos)
   - Ver indicador de semáforo (🟢/🟡/🔴)
   - Leer descripción de confianza
   - Decidir si seguir o skip basado en confianza

3. **Revisar Señal** (30 segundos)
   - Ver dirección (LONG/SHORT/FLAT)
   - Verificar estado (EJECUTAR/SKIP)
   - Si SKIP: leer razón y confirmar

4. **Validar Plan** (1 minuto)
   - Revisar precio de entrada
   - Verificar SL y TP son razonables
   - Confirmar tamaño de posición (cantidad y riesgo $)
   - Ver R/R ratio

5. **Ejecutar** (30 segundos)
   - Click en "📄 Ejecutar Paper Trade" o "💰 Ejecutar Live Trade"
   - Confirmar ventana de trading activa
   - Guardar plan si necesario

### Workflow de Análisis (Deep Dive Tab) ⏱️ 10-15 minutos

1. **Revisar Performance** (3 minutos)
   - Ver métricas principales (CAGR, Sharpe, Max DD, Win Rate)
   - Analizar equity curve: ¿tendencia alcista sostenida?
   - Revisar drawdown: ¿controlado dentro de límites?

2. **Análisis Multi-Horizonte** (3 minutos)
   - **Corto plazo**: timing de entrada, volatilidad
   - **Medio plazo**: tendencia semanal, filtros
   - **Largo plazo**: régimen de mercado
   - Verificar consenso entre horizontes

3. **Desglose de Estrategias** (2 minutos)
   - Ver señales individuales de cada estrategia
   - Identificar si hay divergencia
   - Revisar pesos asignados

4. **Ajuste de Parámetros** (3 minutos)
   - Basado en métricas, ajustar risk %
   - Si drawdown alto → reducir riesgo
   - Si Sharpe alto → considerar aumentar
   - Modificar TP/SL multipliers si necesario

5. **Historial y Logs** (2 minutos)
   - Revisar trades históricos (si disponible)
   - Verificar estado de datos
   - Confirmar última actualización

### Workflow de Fin de Semana 📅

1. **Review Completo** (Deep Dive Tab)
   - Analizar performance semanal
   - Comparar vs. expectativas
   - Identificar patrones de éxito/fracaso

2. **Optimización**
   - Ajustar parámetros basados en resultados
   - Considerar cambios en estrategias
   - Actualizar capital disponible

3. **Planning**
   - Establecer objetivos para semana entrante
   - Definir condiciones de skip
   - Preparar watchlist

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

## 🎨 Interpretación del Indicador de Confianza

### ¿Cómo usar el semáforo de confianza?

**🟢 ALTA Confianza**:
- **Significado**: Sistema funcionando excelentemente en últimos 12 meses
- **Acción**: Ejecutar trades normalmente, incluso considerar aumentar tamaño
- **Riesgo**: Bajo. Sistema ha demostrado consistencia

**🟡 MEDIA Confianza**:
- **Significado**: Sistema funcional pero con resultados mixtos
- **Acción**: Ejecutar con precaución, mantener tamaño estándar
- **Riesgo**: Moderado. Monitorear resultados de cerca

**🔴 BAJA Confianza**:
- **Significado**: Sistema underperforming o en período de ajuste
- **Acción**: Considerar skip o reducir tamaño a 50%
- **Riesgo**: Alto. Evaluar si continuar o pausar trading

### Casos de uso del semáforo

**Trader Conservador**:
- Solo operar en 🟢 Alta
- Skip en 🟡 y 🔴

**Trader Moderado**:
- Operar en 🟢 y 🟡
- Reducir tamaño en 🟡
- Skip solo en 🔴

**Trader Agresivo**:
- Operar en todos los niveles
- Ajustar tamaño según confianza
- Mayor énfasis en análisis multi-horizonte

---

## 💡 Tips y Best Practices

### Para Trading Plan Tab
- ✅ Revisar SIEMPRE el indicador de confianza primero
- ✅ Verificar ventana de trading antes de ejecutar
- ✅ Confirmar que SL y TP son razonables (R/R > 1.5)
- ❌ No ignorar señales de skip
- ❌ No ejecutar trades fuera de ventanas

### Para Deep Dive Tab
- ✅ Revisar semanalmente para ajuste de parámetros
- ✅ Monitorear cambios en equity curve
- ✅ Identificar divergencias entre estrategias
- ❌ No hacer cambios reactivos diarios
- ❌ No sobreoptimizar basado en pocos trades

### Para Gestión de Riesgo
- ✅ Mantener risk % consistente (2% recomendado)
- ✅ Ajustar según confianza del sistema
- ✅ Respetar límites de capital
- ❌ No aumentar risk % en racha perdedora
- ❌ No ignorar drawdowns altos (>15%)

---

## 📖 Recursos

- **Streamlit Docs**: https://docs.streamlit.io
- **Plotly Docs**: https://plotly.com/python/
- **One Market API**: http://localhost:8000/docs
- **Architecture**: Ver `ARCHITECTURE.md`
- **Backtest Design**: Ver `BACKTEST_DESIGN.md`

---

## 🆕 Changelog v2.0

**Nuevas Funcionalidades**:
- ✨ Navegación por pestañas (Trading Plan / Deep Dive)
- ✨ Indicador de confianza basado en backtest (sistema de semáforo)
- ✨ Helpers compartidos para carga de datos
- ✨ Cálculo centralizado de métricas
- ✨ Interfaz optimizada para decisión rápida

**Mejoras**:
- 🚀 Performance mejorado con cache de datos compartido
- 🎨 UX simplificada en Trading Plan tab
- 📊 Análisis más profundo en Deep Dive tab
- 🧪 Tests actualizados para verificar ambas tabs

**Breaking Changes**:
- Ninguno. Compatibilidad total con v1.0

---

**Version**: 2.0.0  
**Last Updated**: Octubre 2025

