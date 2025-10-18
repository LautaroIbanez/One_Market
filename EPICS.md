# One Market - Planificación de Epics

Este documento detalla todos los Epics planificados para One Market, desde fundaciones de datos hasta deployment en producción.

---

## ✅ Epic 1 — Fundaciones de Datos y Almacenamiento

**Status**: COMPLETADO  
**Duración estimada**: 2 semanas  
**Completado**: Octubre 2024

### Objetivo
Asegurar ingestión, almacenamiento y validaciones de OHLCV robustos para múltiples símbolos y timeframes.

### Historias

#### ✅ Historia 1.1 — Arquitectura de app/data y esquema
- Modelos Pydantic para Bars y metadatos
- Validaciones de consistencia OHLC
- Particionamiento `symbol=X/tf=Y/year=Z/month=M/`
- **Entregables**: `schema.py` con OHLCVBar, DatasetMetadata, StoragePartitionKey

#### ✅ Historia 1.2 — Fetch incremental con ccxt
- Cliente ccxt con rate limiting
- Fetch incremental con paginación automática
- Manejo de errores y retry
- Normalización UTC
- **Entregables**: `fetch.py` con DataFetcher, RateLimiter

#### ✅ Historia 1.3 — store.py con pyarrow/parquet
- Escritura incremental particionada
- Lectura eficiente con filtros
- Gestión de metadatos
- Deduplicación configurable
- **Entregables**: `store.py` con DataStore

#### ✅ Historia 1.4 — Testing y QA de datos
- Tests de validación de schema
- Tests de detección de gaps
- Tests de storage idempotency
- Fixtures para testing
- **Entregables**: `test_data.py` con 20+ tests

### Criterios de Aceptación
- ✅ Fetch de 10k bars en <10s
- ✅ Write/Read de 1k bars en <500ms
- ✅ Detección automática de gaps y duplicados
- ✅ Cobertura de tests >90%
- ✅ Storage particionado por mes
- ✅ Metadata tracking completo

---

## 🔄 Epic 2 — Estrategias Cuantitativas

**Status**: PENDIENTE  
**Duración estimada**: 3 semanas  
**Inicio previsto**: Noviembre 2024

### Objetivo
Implementar framework de indicadores técnicos, generación de señales y backtesting engine para validación de estrategias.

### Historias

#### Historia 2.1 — Framework de Indicadores Técnicos
**Esfuerzo**: 5 días

Implementar librería modular de indicadores con interfaz unificada.

**Tareas**:
- Crear clase base `Indicator` con API estándar
- Implementar indicadores básicos:
  - SMA, EMA, WMA (medias móviles)
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - ATR (Average True Range)
- Implementar indicadores avanzados:
  - Ichimoku Cloud
  - Fibonacci retracements
  - Volume Profile
- Testing exhaustivo de cálculos vs referencia (TA-Lib)

**Entregables**:
- `app/indicators/base.py`: Clase base Indicator
- `app/indicators/trend.py`: SMA, EMA, MACD
- `app/indicators/momentum.py`: RSI, Stochastic
- `app/indicators/volatility.py`: BB, ATR
- `tests/test_indicators.py`: Tests de precisión

**Criterios de aceptación**:
- Precisión <0.01% vs TA-Lib para indicadores estándar
- Cálculo de 1000 períodos en <100ms por indicador
- API consistente: `indicator.calculate(bars) → Series`
- Tests con datos conocidos (fixtures)

#### Historia 2.2 — Motor de Señales (Entry/Exit)
**Esfuerzo**: 5 días

Sistema de generación de señales basado en condiciones.

**Tareas**:
- Diseñar DSL para condiciones de señal
- Implementar `SignalGenerator` base
- Crear estrategias ejemplo:
  - SMA Crossover
  - RSI Oversold/Overbought
  - MACD Signal Line Cross
  - Bollinger Band Breakout
- Sistema de filtros (múltiples timeframes)
- Gestión de estado de señales

**Entregables**:
- `app/signals/base.py`: SignalGenerator base
- `app/signals/conditions.py`: DSL de condiciones
- `app/signals/strategies/`: Estrategias predefinidas
- `tests/test_signals.py`: Tests de lógica

**Criterios de aceptación**:
- Generación de señal en <1s (target Epic 1)
- Soporte para condiciones compuestas (AND/OR/NOT)
- Tracking de estado: no_position, long, short
- Signals tipados: LONG_ENTRY, LONG_EXIT, SHORT_ENTRY, SHORT_EXIT

#### Historia 2.3 — Backtesting Engine
**Esfuerzo**: 8 días

Motor de backtesting vectorizado con métricas robustas.

**Tareas**:
- Implementar `Backtester` con vectorización
- Sistema de ejecución de órdenes simulado
- Cálculo de métricas:
  - Sharpe Ratio, Sortino Ratio
  - Max Drawdown, Calmar Ratio
  - Win Rate, Profit Factor
  - Expectancy, Average R
- Generación de equity curve
- Análisis de trades (duración, R múltiples)
- Export de resultados (JSON, CSV)

**Entregables**:
- `app/backtest/engine.py`: Backtester core
- `app/backtest/metrics.py`: Cálculo de métricas
- `app/backtest/reports.py`: Generación de reportes
- `tests/test_backtest.py`: Tests de lógica

**Criterios de aceptación**:
- Backtest de 1 año (8760 bars 1h) en <5s
- Precisión en cálculo de P&L (accounting correcto)
- Slippage y comisiones configurables
- Reproducibilidad total (misma seed → mismos resultados)
- Export completo de trades

#### Historia 2.4 — Optimización de Parámetros
**Esfuerzo**: 5 días

Sistema de optimización de parámetros con grid search y walk-forward.

**Tareas**:
- Implementar grid search
- Walk-forward analysis
- Optimización con objetivos múltiples (Sharpe, Drawdown)
- Detección de overfitting
- Visualización de optimization surface

**Entregables**:
- `app/optimize/grid.py`: Grid search
- `app/optimize/walkforward.py`: Walk-forward
- `app/optimize/objectives.py`: Funciones objetivo
- `tests/test_optimize.py`: Tests

**Criterios de aceptación**:
- Grid search de 100 combinaciones en <5min
- Walk-forward con 5 windows
- Detection de curve fitting (validation metrics)
- Export de mejores parámetros

---

## 📋 Epic 3 — Gestión de Riesgo

**Status**: PENDIENTE  
**Duración estimada**: 2 semanas  
**Inicio previsto**: Diciembre 2024

### Objetivo
Implementar sistema robusto de gestión de riesgo con position sizing, SL/TP dinámicos y portfolio management.

### Historias

#### Historia 3.1 — Position Sizing
**Esfuerzo**: 3 días

Cálculo de tamaño de posición basado en riesgo.

**Tareas**:
- Implementar métodos de sizing:
  - Fixed fractional (% del capital)
  - Kelly Criterion
  - ATR-based
  - Volatility-adjusted
- Cálculo de riesgo por trade
- Máximo % de capital por trade
- Gestión de leverage

**Entregables**:
- `app/risk/sizing.py`: Position sizers
- Tests de cálculo

**Criterios de aceptación**:
- Sizing respeta max risk % configurado
- Ajuste automático por volatilidad
- Cálculo de leverage requerido

#### Historia 3.2 — Stop Loss / Take Profit Dinámicos
**Esfuerzo**: 4 días

Sistema de SL/TP adaptativo.

**Tareas**:
- SL fijo (% o ATR)
- Trailing stop
- Time-based stops
- TP por R múltiple
- Break-even move
- Partial exits

**Entregables**:
- `app/risk/stops.py`: Stop management
- Tests de lógica

**Criterios de aceptación**:
- SL/TP se ajustan en tiempo real
- Trailing stop funcional
- Multiple exit levels configurables

#### Historia 3.3 — Gestión de Cartera Multi-Símbolo
**Esfuerzo**: 4 días

Portfolio management con correlaciones.

**Tareas**:
- Tracking de exposición total
- Límites por símbolo/sector
- Análisis de correlaciones
- Rebalanceo automático
- Gestión de drawdown de cartera

**Entregables**:
- `app/portfolio/manager.py`: Portfolio manager
- `app/portfolio/correlation.py`: Análisis
- Tests

**Criterios de aceptación**:
- Respeto de límites de exposición
- Diversificación enforced
- Rebalanceo cuando drift > threshold

#### Historia 3.4 — Risk Metrics y Reporting
**Esfuerzo**: 3 días

Dashboard de métricas de riesgo.

**Tareas**:
- VaR (Value at Risk)
- CVaR (Conditional VaR)
- Risk-adjusted returns
- Stress testing
- Scenario analysis

**Entregables**:
- `app/risk/metrics.py`: Cálculo de métricas
- `app/risk/reports.py`: Reportes
- Tests

---

## 📋 Epic 4 — Ejecución y Scheduling

**Status**: PENDIENTE  
**Duración estimada**: 2 semanas  
**Inicio previsto**: Enero 2025

### Objetivo
Sistema de ejecución automática de trades con order management, position tracking y scheduling robusto.

### Historias

#### Historia 4.1 — Order Manager con ccxt
**Esfuerzo**: 5 días

**Tareas**:
- Order lifecycle: create, submit, monitor, cancel
- Tipos de orden: market, limit, stop-limit
- Retry y error handling
- Order status tracking
- Fill tracking

**Entregables**:
- `app/execution/orders.py`
- Tests con mock exchange

#### Historia 4.2 — Position Tracking
**Esfuerzo**: 3 días

**Tareas**:
- Real-time position updates
- P&L tracking (realized + unrealized)
- Sync con exchange
- Position reconciliation

**Entregables**:
- `app/execution/positions.py`
- Tests

#### Historia 4.3 — Scheduler APScheduler
**Esfuerzo**: 4 días

**Tareas**:
- Job scheduling (daily signals)
- Cron-like syntax
- Error recovery
- Job monitoring
- Notification hooks

**Entregables**:
- `app/scheduler/jobs.py`
- Tests

#### Historia 4.4 — Monitoring y Alertas
**Esfuerzo**: 3 días

**Tareas**:
- Health checks
- Performance monitoring
- Alertas (email, Telegram)
- Logging estructurado

**Entregables**:
- `app/monitoring/`
- Integration con alerting

---

## 📋 Epic 5 — UI y Visualización

**Status**: PENDIENTE  
**Duración estimada**: 3 semanas  
**Inicio previsto**: Febrero 2025

### Objetivo
Dashboard interactivo con Streamlit para control, monitoring y análisis.

### Historias

#### Historia 5.1 — Dashboard Principal Streamlit
**Esfuerzo**: 5 días

**Tareas**:
- Layout responsive
- Sidebar navigation
- Real-time updates
- Theming (dark mode)

**Entregables**:
- `ui/app.py`: Main app
- `ui/pages/`: Páginas

#### Historia 5.2 — Gráficos Interactivos (Plotly)
**Esfuerzo**: 5 días

**Tareas**:
- Candlestick charts con indicadores
- Equity curves
- Drawdown charts
- Distribution plots
- Heatmaps de correlación

**Entregables**:
- `ui/charts/`: Componentes de gráficos

#### Historia 5.3 — Control Panel
**Esfuerzo**: 4 días

**Tareas**:
- Start/stop strategies
- Config editor
- Manual trade entry
- Position management

**Entregables**:
- `ui/pages/control.py`

#### Historia 5.4 — Performance Analytics
**Esfuerzo**: 5 días

**Tareas**:
- Trade analysis
- Strategy comparison
- Period analysis
- Attribution analysis

**Entregables**:
- `ui/pages/analytics.py`

---

## 📋 Epic 6 — API y Extensibilidad

**Status**: PENDIENTE  
**Duración estimada**: 2 semanas

### Historias
- API REST con FastAPI
- WebSocket para updates real-time
- Documentación OpenAPI
- Rate limiting
- Authentication/Authorization

---

## 📋 Epic 7 — Deployment y DevOps

**Status**: PENDIENTE  
**Duración estimada**: 2 semanas

### Historias
- Dockerización
- CI/CD con GitHub Actions
- Deployment scripts
- Monitoring (Prometheus/Grafana)
- Backup automático

---

## Resumen del Roadmap

```
Timeline (estimada):

Oct 2024  │ Epic 1 ✅
Nov 2024  │ Epic 2 🔄
Dec 2024  │ Epic 3
Jan 2025  │ Epic 4
Feb 2025  │ Epic 5
Mar 2025  │ Epic 6
Apr 2025  │ Epic 7
          │
          ▼ MVP Production Ready
```

## Prioridades

### Must Have (MVP)
1. ✅ Epic 1: Fundaciones de datos
2. 🔄 Epic 2: Estrategias cuantitativas
3. Epic 3: Gestión de riesgo
4. Epic 4: Ejecución

### Should Have
5. Epic 5: UI y visualización
6. Epic 6: API

### Nice to Have
7. Epic 7: DevOps avanzado

---

**Última actualización**: Octubre 2024  
**Epic actual**: Epic 1 (Completado) ✅  
**Próximo epic**: Epic 2 - Estrategias Cuantitativas


