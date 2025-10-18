# Backtest Engine Design - One Market

## Arquitectura

### Componentes Principales

```
app/research/backtest/
├── __init__.py           # Exports principales
├── engine.py             # BacktestEngine principal
├── metrics.py            # Cálculo de métricas
├── rules.py              # Reglas de trading (1/día, ventanas, etc)
├── walk_forward.py       # Walk-forward optimization
└── monte_carlo.py        # Monte Carlo analysis
```

## Motor de Backtesting

### Justificación: ¿Por qué vectorbt?

**Ventajas**:
1. ✅ **Vectorizado**: 100-1000x más rápido que backtesting loop-based
2. ✅ **Walk-forward nativo**: Soporte integrado para walk-forward analysis
3. ✅ **Flexible**: Soporta custom indicators y señales
4. ✅ **Métricas completas**: Sharpe, Sortino, Calmar, etc. out-of-the-box
5. ✅ **Visualizaciones**: Plots integrados para equity curves, drawdown, etc.
6. ✅ **Portfolio**: Soporte multi-símbolo y multi-estrategia

**Alternativas consideradas**:
- **backtrader**: Más lento (loop-based), menos moderno
- **zipline**: Deprecated, poca mantenimiento
- **bt**: Menos features que vectorbt
- **Custom**: Reinventar la rueda, propenso a bugs

**Decisión**: vectorbt por su balance entre performance, features y mantenibilidad.

## Reglas de Trading

### 1. Una operación por día
```python
def enforce_one_trade_per_day(signals: pd.Series, timestamp: pd.Series) -> pd.Series:
    """
    Si hay múltiples señales en un día, solo toma la primera.
    """
    dates = pd.to_datetime(timestamp).dt.date
    
    # Group by date, keep only first signal
    daily_signals = signals.groupby(dates).first()
    
    return daily_signals
```

### 2. Ventanas de Trading (A/B)
```python
def filter_by_trading_windows(
    signals: pd.Series,
    timestamp: pd.Series,
    calendar: TradingCalendar
) -> pd.Series:
    """
    Solo permite señales dentro de ventanas A o B.
    """
    valid_hours = signals.copy()
    
    for i, ts in enumerate(timestamp):
        if not calendar.is_trading_hours(ts):
            valid_hours.iloc[i] = 0  # Neutralizar señal
    
    return valid_hours
```

### 3. Cierre Forzado
```python
def apply_forced_close(
    positions: pd.Series,
    timestamp: pd.Series,
    calendar: TradingCalendar
) -> pd.Series:
    """
    Cierra todas las posiciones al final del día (16:45 local).
    """
    for i, ts in enumerate(timestamp):
        if calendar.should_force_close(ts) and positions.iloc[i] != 0:
            positions.iloc[i] = 0  # Force exit
    
    return positions
```

### 4. OCO Orders (TP/SL)
```python
# Usar vectorbt.Portfolio con:
sl_stop = 0.02  # 2% stop loss
tp_stop = 0.03  # 3% take profit

portfolio = vbt.Portfolio.from_signals(
    close=close,
    entries=entries,
    exits=exits,
    sl_stop=sl_stop,
    tp_stop=tp_stop,
    sl_trail=False  # No trailing stop por defecto
)
```

## Métricas de Performance

### Básicas
- **CAGR**: Compound Annual Growth Rate
- **Total Return**: Retorno total del período
- **Max Drawdown**: Pérdida máxima desde peak
- **Win Rate**: % de trades ganadores
- **Profit Factor**: Total wins / Total losses

### Risk-Adjusted
- **Sharpe Ratio**: (Return - RF) / Std Dev
- **Sortino Ratio**: (Return - RF) / Downside Dev
- **Calmar Ratio**: CAGR / Max Drawdown
- **MAR Ratio**: CAGR / Avg Drawdown

### Trade Analysis
- **Average Trade**: PnL promedio por trade
- **Average Win / Loss**: Separado por winners/losers
- **Max Consecutive Wins/Losses**: Rachas
- **Expectancy**: Win Rate * Avg Win - (1 - Win Rate) * Avg Loss
- **Exposure**: % del tiempo en el mercado

### Advanced
- **Recovery Factor**: Total Return / Max Drawdown
- **Ulcer Index**: Medida de profundidad y duración de drawdowns
- **Omega Ratio**: Probability-weighted ratio de gains vs losses

## Walk-Forward Analysis

### Esquema
```python
# Train: 6 meses
# Test: 1 mes
# Anchored: False (rolling window)

train_period = 180  # días
test_period = 30    # días
step = 30           # días (overlap)

for start in range(0, len(data) - train_period - test_period, step):
    train_start = start
    train_end = start + train_period
    test_start = train_end
    test_end = test_start + test_period
    
    # Train
    train_data = data[train_start:train_end]
    optimal_params = optimize(train_data)
    
    # Test
    test_data = data[test_start:test_end]
    results = backtest(test_data, optimal_params)
    
    walk_forward_results.append(results)
```

### Métricas Walk-Forward
- **In-Sample vs Out-Sample**: Comparación de performance
- **Efficiency Ratio**: OOS_Return / IS_Return
- **Consistency**: % de períodos OOS positivos
- **Degradation**: Pérdida de performance OOS

## Comisiones y Slippage

### Comisiones
```python
# Binance spot
commission = 0.001  # 0.1% maker/taker

# Binance futures
commission_futures = 0.0004  # 0.04% maker, 0.03% taker (promedio)
```

### Slippage
```python
# Market orders - slippage conservador
slippage = 0.0005  # 0.05% (5 bps)

# Durante alta volatilidad
slippage_high_vol = 0.001  # 0.1%
```

### Aplicación en vectorbt
```python
portfolio = vbt.Portfolio.from_signals(
    close=close,
    entries=entries,
    exits=exits,
    fees=commission,
    slippage=slippage,
    direction='both'  # Long y short
)
```

## Pipeline Completo

```python
def run_backtest(
    df: pd.DataFrame,
    strategy: str,
    params: dict,
    calendar: TradingCalendar,
    commission: float = 0.001,
    slippage: float = 0.0005,
    capital: float = 100000
) -> BacktestResult:
    """
    1. Generar señales
    2. Aplicar reglas (1/día, ventanas, cierre forzado)
    3. Calcular TP/SL con ATR
    4. Ejecutar backtest con vectorbt
    5. Calcular métricas
    6. Retornar resultados estructurados
    """
    
    # 1. Generate signals
    signals = generate_signal(strategy, df, params)
    
    # 2. Apply rules
    signals = enforce_one_trade_per_day(signals.signal, df['timestamp'])
    signals = filter_by_trading_windows(signals, df['timestamp'], calendar)
    
    # 3. Calculate TP/SL
    atr_val = calculate_atr_from_bars(df.to_dict('records'))
    tp_pct = (atr_val * 3) / df['close'].iloc[-1]  # 3x ATR
    sl_pct = (atr_val * 2) / df['close'].iloc[-1]  # 2x ATR
    
    # 4. Backtest
    portfolio = vbt.Portfolio.from_signals(
        close=df['close'],
        entries=signals == 1,
        exits=signals == -1,
        tp_stop=tp_pct,
        sl_stop=sl_pct,
        fees=commission,
        slippage=slippage,
        init_cash=capital
    )
    
    # 5. Apply forced close
    # TODO: Implement custom exit logic for forced close
    
    # 6. Calculate metrics
    metrics = calculate_metrics(portfolio)
    
    return BacktestResult(
        portfolio=portfolio,
        metrics=metrics,
        trades=portfolio.trades.records_readable,
        equity_curve=portfolio.value()
    )
```

## Output Structure

```python
class BacktestResult(BaseModel):
    """Structured backtest results."""
    
    # Portfolio
    portfolio: Any  # vectorbt Portfolio object
    
    # Performance
    total_return: float
    cagr: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    
    # Trade stats
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    avg_trade: float
    avg_win: float
    avg_loss: float
    
    # Risk metrics
    volatility: float
    downside_deviation: float
    max_consecutive_losses: int
    exposure_time: float
    
    # Data
    equity_curve: pd.Series
    drawdown_curve: pd.Series
    trades: pd.DataFrame
    
    # Metadata
    strategy: str
    params: dict
    period: tuple  # (start_date, end_date)
```

## Testing Strategy

### Unit Tests
- Test cada regla individualmente
- Test métricas calculation
- Test walk-forward logic

### Integration Tests
- Test pipeline completo
- Test con datos sintéticos
- Test casos edge (sin trades, todos ganadores, etc.)

### Validation Tests
- Comparar con backtest manual
- Verificar 1 trade/día enforcement
- Verificar cierre forzado
- Verificar TP/SL execution

---

**Siguiente paso**: Implementar engine.py y metrics.py

