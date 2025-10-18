# Epic 3 — Investigación y Señales - Progress

**Estado Actual**: En progreso (3 de 6 historias completadas)
**Fecha**: Octubre 2024

## ✅ Historias Completadas

### ✅ Historia 3.1 — research/indicators.py y features.py

**Objetivo**: Implementar wrappers de indicadores técnicos sin lookahead y features adicionales.

**Implementado en `app/research/indicators.py`** (18 indicadores):
1. `ema()` - Exponential Moving Average
2. `sma()` - Simple Moving Average
3. `rsi()` - Relative Strength Index
4. `atr()` - Average True Range
5. `adx()` - Average Directional Index
6. `donchian_channels()` - Donchian Channels
7. `macd()` - MACD (line, signal, histogram)
8. `bollinger_bands()` - Bollinger Bands
9. `stochastic()` - Stochastic Oscillator
10. `cci()` - Commodity Channel Index
11. `williams_r()` - Williams %R
12. `momentum()` - Momentum
13. `roc()` - Rate of Change
14. `obv()` - On-Balance Volume
15. `vwap_intraday()` - Intraday VWAP
16. `supertrend()` - Supertrend indicator
17. `keltner_channels()` - Keltner Channels
18. `validate_series()` - Series validation utility

**Implementado en `app/research/features.py`** (15 features):
1. `daily_vwap_reconstructed()` - VWAP diaria reconstruida
2. `relative_volatility()` - Volatilidad relativa (short/long)
3. `normalized_atr()` - ATR normalizado (ATR%)
4. `trend_strength()` - Fuerza de tendencia (R²)
5. `volatility_regime()` - Régimen de volatilidad
6. `distance_from_ma()` - Distancia desde MA
7. `rolling_sharpe()` - Sharpe ratio móvil
8. `rolling_sortino()` - Sortino ratio móvil
9. `cumulative_return()` - Retorno acumulado
10. `rolling_max_dd()` - Drawdown máximo móvil
11. `price_zscore()` - Z-score de precio
12. `volume_zscore()` - Z-score de volumen
13. `support_resistance_distance()` - Distancia a sop/res
14. `money_flow_index()` - Money Flow Index
15. `choppy_index()` - Choppiness Index
16. Utilities adicionales: `candle_direction()`, `consecutive_closes()`, `higher_highs_lower_lows()`

**Características**:
- ✅ Sin lookahead bias (todos usan `.shift()` apropiadamente)
- ✅ Validación de series
- ✅ Manejo robusto de NaN
- ✅ Documentación completa

---

### ✅ Historia 3.2 — signals.py

**Objetivo**: Estrategias atómicas tunables con simetría long/short.

**Implementado en `app/research/signals.py`** (6 estrategias):

1. **`ma_crossover()`** - MA Crossover
   - Parámetros: fast_period, slow_period, ma_type
   - Long: Fast > Slow
   - Short: Fast < Slow

2. **`rsi_regime_pullback()`** - RSI Regime + Pullback
   - Parámetros: rsi_period, oversold, overbought, regime_period
   - Long: Uptrend + RSI bounce from oversold
   - Short: Downtrend + RSI reject from overbought

3. **`donchian_breakout_adx()`** - Donchian Breakout + ADX
   - Parámetros: donchian_period, adx_period, adx_threshold
   - Long: Break above upper band + ADX > threshold
   - Short: Break below lower band + ADX > threshold

4. **`macd_histogram_atr_filter()`** - MACD Histogram + ATR Filter
   - Parámetros: fast, slow, signal_period, atr_period, atr_multiplier
   - Long: Histogram turning up + sufficient volatility
   - Short: Histogram turning down + sufficient volatility

5. **`mean_reversion()`** - Bollinger Bands Mean Reversion
   - Parámetros: period, std_dev
   - Long: Price at lower band
   - Short: Price at upper band

6. **`trend_following_ema()`** - Triple EMA Trend Following
   - Parámetros: fast_period, slow_period, trend_period
   - Long: Fast > Slow > Trend
   - Short: Fast < Slow < Trend

**Características**:
- ✅ Todas soportan long/short simétricamente
- ✅ Salidas normalizadas: `SignalOutput` con signal (discrete) y strength (continuous)
- ✅ Metadata completa para cada estrategia
- ✅ Parámetros configurables
- ✅ Hold logic implementado

**Utilities**:
- `get_strategy_list()` - Lista de estrategias disponibles
- `generate_signal()` - Factory function para generar señales por nombre

---

### ✅ Historia 3.3 — combine.py

**Objetivo**: Métodos de blending de señales múltiples.

**Implementado en `app/research/combine.py`** (5 métodos):

1. **`simple_average()`** - Promedio simple
   - Pesos iguales para todas las estrategias
   - Señal final es el signo del promedio

2. **`weighted_average()`** - Promedio ponderado
   - Pesos personalizados
   - Normalización automática

3. **`sharpe_weighted()`** - Ponderación por Sharpe móvil (90d)
   - Estrategias con mayor Sharpe reciben mayor peso
   - Pesos dinámicos recalculados en rolling window
   - Clip de Sharpe negativo

4. **`majority_vote()`** - Votación mayoritaria
   - Señal generada cuando min_agreement alcanzado
   - Confidence basado en fracción de acuerdo

5. **`logistic_model()`** - Modelo logístico (scikit-learn)
   - Entrena modelo para predecir señales rentables
   - Soporta features agregadas
   - Refit periódico
   - Walk-forward training

**Características**:
- ✅ `CombinedSignal` output estandarizado
- ✅ Confidence scores
- ✅ Feature importance/weights reporting
- ✅ `resolve_ties()` - Resolución de empates (flat/previous/random)
- ✅ `combine_signals()` - Factory function unificada

---

## 🔄 Historias En Progreso

### 🔄 Historia 3.4 — backtest.py

**Objetivo**: Pipeline completo de backtesting con vectorbt.

**Estado**: Estructura creada, implementación pendiente

**Requerimientos**:
- Motor vectorbt para backtesting vectorizado
- Walk-forward optimization
- 1 trade/día enforcement
- Trading windows (ventanas A/B)
- OCO TP/SL orders
- Comisiones y slippage
- Cierre forzado

**Métricas a implementar**:
- CAGR, Sharpe, Sortino
- Max Drawdown, Calmar, MAR
- Win Rate, Profit Factor
- Expectancy, Average Trade
- Exposure, Recovery Factor

---

## ⏳ Historias Pendientes

### ⏳ Historia 3.5 — Monte Carlo y estabilidad

**Requerimientos**:
- Permutación de retornos por bloques
- Estimación de riesgo de ruina
- Drawdown esperado
- Confidence intervals
- Stability metrics

### ⏳ Historia 3.6 — Tests

**Requerimientos**:
- `tests/test_indicators.py`
- `tests/test_features.py`
- `tests/test_signals.py`
- `tests/test_combine.py`
- `tests/test_backtest_detailed.py`
- Validar reglas específicas (1 trade/día, cierre forzado)

---

## 📊 Estadísticas Actuales

| Componente | Líneas | Tests | Estado |
|------------|--------|-------|--------|
| indicators.py | ~650 | Pendiente | ✅ |
| features.py | ~450 | Pendiente | ✅ |
| signals.py | ~550 | Pendiente | ✅ |
| combine.py | ~450 | Pendiente | ✅ |
| backtest/ | 0 | Pendiente | 🔄 |
| monte_carlo.py | 0 | Pendiente | ⏳ |
| Tests | 0 | N/A | ⏳ |

**Total completado**: ~2,100 líneas de código (50% de Epic 3)

---

## 📦 Dependencias Añadidas

```txt
# Technical analysis
ta==0.11.0
pandas-ta==0.3.14b0

# Backtesting and ML
vectorbt==0.26.2
scikit-learn==1.3.2
```

---

## 🎯 Próximos Pasos

1. **Completar Historia 3.4** - Implementar engine de backtest completo
2. **Historia 3.5** - Monte Carlo analysis
3. **Historia 3.6** - Suite completa de tests
4. **Integración** - Ejemplo end-to-end
5. **Documentación** - EPIC3_SUMMARY.md completo

---

## 💡 Notas de Implementación

### Prevención de Lookahead
Todos los indicadores y features usan apropiadamente:
- `.shift()` para acceder a valores pasados
- Rolling windows con `min_periods`
- No acceso a datos futuros en ningún punto

### Modularidad
Cada estrategia es independiente y puede:
- Ejecutarse standalone
- Combinarse con otras
- Optimizarse individualmente
- Activar/desactivar long/short

### Performance
- Indicadores vectorizados con pandas/numpy
- Evita loops cuando es posible
- Caching de cálculos intermedios (donde aplica)

---

**Última actualización**: Octubre 2024
**Autor**: One Market Development Team

