## Advanced Features: Signal Library, Optimization & Volatility Ranges

### Overview

This document describes the advanced features implemented in the One Market trading system:

1. **Extended Signal Library**: New atomic trading strategies (breakout, mean reversion, multi-timeframe momentum)
2. **Systematic Optimization**: Grid search and Bayesian optimization for parameter tuning
3. **Volatility-Based Ranges**: Dynamic entry/SL/TP ranges based on market volatility
4. **Strategy Ranking**: Automatic strategy selection based on performance metrics

---

## 1. Extended Signal Library

### New Atomic Strategies

#### ATR Channel Breakout with Volume Filter
**Location**: `app/research/signals.py::atr_channel_breakout_volume()`

Trades breakouts of ATR-based channels confirmed by high volume.

**Signals**:
- **Long**: Price breaks above upper ATR band + volume > threshold
- **Short**: Price breaks below lower ATR band + volume > threshold

**Parameters**:
```python
ATRChannelBreakoutConfig(
    atr_period=14,           # ATR calculation period
    atr_multiplier=2.0,      # Channel width (ATR multiplier)
    volume_ma_period=20,     # Volume MA for filter
    volume_threshold=1.5     # Minimum volume vs MA (1.5x)
)
```

**Usage**:
```python
from app.research.signals import atr_channel_breakout_volume

signal = atr_channel_breakout_volume(
    high=df['high'],
    low=df['low'],
    close=df['close'],
    volume=df['volume'],
    atr_period=14,
    atr_multiplier=2.0
)

print(f"Signal: {signal.signal.iloc[-1]}")  # 1, -1, or 0
print(f"Strength: {signal.strength.iloc[-1]}")
```

#### VWAP Z-Score Mean Reversion
**Location**: `app/research/signals.py::vwap_zscore_reversion()`

Trades mean reversion when price deviates significantly from VWAP (measured by z-score).

**Signals**:
- **Long**: Z-score < -2.0 (oversold vs VWAP)
- **Short**: Z-score > +2.0 (overbought vs VWAP)
- **Exit**: Z-score returns to neutral zone

**Parameters**:
```python
VWAPZScoreConfig(
    vwap_period=20,      # Rolling VWAP period
    zscore_entry=2.0,    # Entry threshold (std devs)
    zscore_exit=0.5      # Exit threshold
)
```

**Usage**:
```python
from app.research.signals import vwap_zscore_reversion

signal = vwap_zscore_reversion(
    high=df['high'],
    low=df['low'],
    close=df['close'],
    volume=df['volume'],
    vwap_period=20,
    zscore_entry=2.0
)
```

#### Triple EMA + RSI Regime Momentum
**Location**: `app/research/signals.py::ema_triple_momentum()`

Combines three EMA alignment with RSI regime filter for momentum trades.

**Signals**:
- **Long**: Fast > Mid > Slow EMAs + RSI > 50
- **Short**: Fast < Mid < Slow EMAs + RSI < 50

**Parameters**:
```python
EMATripleMomentumConfig(
    fast_period=8,              # Fast EMA
    mid_period=21,              # Mid EMA
    slow_period=55,             # Slow EMA (trend)
    rsi_period=14,              # RSI for regime
    rsi_bull_threshold=50,      # Long regime threshold
    rsi_bear_threshold=50       # Short regime threshold
)
```

**Usage**:
```python
from app.research.signals import ema_triple_momentum

signal = ema_triple_momentum(
    close=df['close'],
    fast_period=8,
    mid_period=21,
    slow_period=55
)
```

### Using New Strategies in Backtest

```python
from app.research.backtest.engine import BacktestEngine, BacktestConfig

config = BacktestConfig(
    initial_capital=100000.0,
    risk_per_trade=0.02,
    commission_pct=0.001
)

engine = BacktestEngine(config)

# Backtest new strategy
result = engine.run(
    df=df,
    strategy_name="atr_channel_breakout_volume",
    strategy_params={
        'atr_period': 14,
        'atr_multiplier': 2.0,
        'volume_threshold': 1.5
    },
    timeframe="1h"
)

print(f"Total Return: {result.total_return:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
```

---

## 2. Systematic Optimization

### Grid Search Optimization
**Location**: `app/research/optimization/grid_search.py`

Exhaustive search through all parameter combinations.

**When to use**:
- Small parameter spaces (< 1000 combinations)
- Want to explore full space systematically
- Need reproducible results

**Usage**:
```python
from app.research.optimization import grid_search_optimize, GridSearchConfig

config = GridSearchConfig(
    strategy_name="ema_triple_momentum",
    symbol="BTC-USDT",
    timeframe="1h",
    param_grid={
        'fast_period': [5, 8, 10],
        'mid_period': [15, 21, 30],
        'slow_period': [40, 55, 70]
    },
    scoring_metric="sharpe_ratio",
    maximize=True,
    save_all_results=True
)

results = grid_search_optimize(
    df=df,
    config=config,
    verbose=True
)

# Best result
best = results[0]
print(f"Best parameters: {best.parameters}")
print(f"Sharpe ratio: {best.score:.4f}")
```

### Bayesian Optimization
**Location**: `app/research/optimization/bayesian.py`

Intelligent search using Gaussian Process to predict promising parameter regions.

**When to use**:
- Large parameter spaces (> 1000 combinations)
- Limited computational budget
- Want efficient optimization

**Requirements**:
```bash
pip install scikit-optimize
```

**Usage**:
```python
from app.research.optimization import bayesian_optimize, BayesianConfig

config = BayesianConfig(
    strategy_name="atr_channel_breakout_volume",
    symbol="BTC-USDT",
    timeframe="1h",
    param_space={
        'atr_period': {'type': 'integer', 'low': 10, 'high': 20},
        'atr_multiplier': {'type': 'real', 'low': 1.5, 'high': 3.0},
        'volume_ma_period': {'type': 'integer', 'low': 15, 'high': 30},
        'volume_threshold': {'type': 'real', 'low': 1.2, 'high': 2.0}
    },
    scoring_metric="sharpe_ratio",
    maximize=True,
    n_calls=50,              # 50 iterations
    n_initial_points=10      # 10 random points first
)

results = bayesian_optimize(
    df=df,
    config=config,
    verbose=True
)
```

### Optimization Storage
**Location**: `app/research/optimization/storage.py`

Results are stored in SQLite database and can be exported to Parquet.

```python
from app.research.optimization import OptimizationStorage

storage = OptimizationStorage()

# Get best parameters for a strategy
best_params = storage.get_best_parameters(
    strategy_name="ema_triple_momentum",
    symbol="BTC-USDT",
    timeframe="1h",
    top_n=5  # Top 5 results
)

# Export to Parquet
storage.export_to_parquet("storage/optimization/results.parquet")
```

### Automated Optimization CLI
**Location**: `scripts/optimize_strategies.py`

Command-line tool for automated optimization runs.

```bash
# Optimize all strategies with Bayesian method
python scripts/optimize_strategies.py \
    --symbol BTC-USDT \
    --timeframe 1h \
    --method bayesian \
    --n-calls 50 \
    --update-weights \
    --verbose

# Optimize specific strategies
python scripts/optimize_strategies.py \
    --symbol BTC-USDT \
    --timeframe 4h \
    --method grid \
    --strategies ema_triple_momentum vwap_zscore_reversion

# Schedule with cron for nightly optimization
# Add to crontab:
# 0 2 * * * cd /path/to/project && python scripts/optimize_strategies.py --update-weights
```

---

## 3. Volatility-Based Ranges

### Entry Range Calculation
**Location**: `app/service/entry_band.py::calculate_entry_band()`

Entry prices now include volatility-based ranges (low/high bounds).

**Features**:
- Dynamic range width based on ATR
- Percentage-based range representation
- Fallback to fixed percentage if ATR unavailable

**Usage**:
```python
from app.service.entry_band import calculate_entry_band

result = calculate_entry_band(
    df=df,
    current_price=50000.0,
    signal_direction=1,  # LONG
    beta=0.001,
    use_volatility_range=True,
    atr_period=14,
    atr_multiplier=0.5
)

print(f"Entry Price: ${result.entry_price:,.2f}")
print(f"Entry Range: ${result.entry_low:,.2f} - ${result.entry_high:,.2f}")
print(f"Range Width: {result.range_pct:.2%}")
```

**Output**:
```
Entry Price: $49,950.00
Entry Range: $49,700.00 - $50,200.00
Range Width: 1.00%
```

### SL/TP Range Calculation
**Location**: `app/service/tp_sl_engine.py::calculate_tp_sl()`

Stop Loss and Take Profit levels now include ranges for flexibility.

**Features**:
- ATR-based range bounds
- Configurable range width multiplier
- Maintains R/R ratio across range

**Usage**:
```python
from app/service/tp_sl_engine import calculate_tp_sl, TPSLConfig

config = TPSLConfig(
    method="atr",
    atr_period=14,
    atr_multiplier_sl=2.0,
    atr_multiplier_tp=3.0,
    min_rr_ratio=1.5
)

result = calculate_tp_sl(
    df=df,
    entry_price=50000.0,
    signal_direction=1,  # LONG
    config=config,
    calculate_ranges=True,
    atr_range_multiplier=0.25
)

print(f"Stop Loss: ${result.stop_loss:,.2f}")
print(f"SL Range: ${result.sl_low:,.2f} - ${result.sl_high:,.2f}")
print(f"Take Profit: ${result.take_profit:,.2f}")
print(f"TP Range: ${result.tp_low:,.2f} - ${result.tp_high:,.2f}")
```

### Daily Decision with Ranges
**Location**: `app/service/decision.py::DailyDecision`

The `DailyDecision` model now includes all range fields.

**New Fields**:
```python
class DailyDecision(BaseModel):
    # Entry ranges
    entry_low: Optional[float]
    entry_high: Optional[float]
    entry_range_pct: Optional[float]
    
    # SL ranges
    sl_low: Optional[float]
    sl_high: Optional[float]
    sl_range_pct: Optional[float]
    
    # TP ranges
    tp_low: Optional[float]
    tp_high: Optional[float]
    tp_range_pct: Optional[float]
```

**Usage**:
```python
from app.service.decision import DecisionEngine

engine = DecisionEngine()
decision = engine.make_decision(
    df=df,
    signals=signals,
    signal_strength=confidence,
    capital=100000.0,
    risk_pct=0.02
)

if decision.should_execute:
    print(f"Entry: ${decision.entry_price:,.2f}")
    print(f"  Range: ${decision.entry_low:,.2f} - ${decision.entry_high:,.2f}")
    print(f"  Width: {decision.entry_range_pct:.2%}")
```

---

## 4. Integration Examples

### Complete Workflow

```python
# 1. Load data
from app.data.store import DataStore
store = DataStore()
df = store.read_dataframe("BTC-USDT", "1h")

# 2. Optimize strategies
from app.research.optimization import bayesian_optimize, BayesianConfig

config = BayesianConfig(
    strategy_name="ema_triple_momentum",
    symbol="BTC-USDT",
    timeframe="1h",
    param_space={
        'fast_period': {'type': 'integer', 'low': 5, 'high': 12},
        'mid_period': {'type': 'integer', 'low': 15, 'high': 30},
        'slow_period': {'type': 'integer', 'low': 40, 'high': 70}
    },
    n_calls=30
)

results = bayesian_optimize(df=df, config=config, verbose=True)
best_params = results[0].parameters

# 3. Generate signals with optimized parameters
from app.research.signals import ema_triple_momentum

signals = ema_triple_momentum(
    close=df['close'],
    **best_params
)

# 4. Make decision with volatility ranges
from app.service.decision import DecisionEngine

engine = DecisionEngine()
decision = engine.make_decision(
    df=df,
    signals=signals.signal,
    signal_strength=signals.strength,
    capital=100000.0
)

# 5. Display results
if decision.should_execute:
    print(f"Signal: {'LONG' if decision.signal > 0 else 'SHORT'}")
    print(f"Entry: ${decision.entry_price:,.2f}")
    print(f"  Range: {decision.entry_range_pct:.2%}")
    print(f"Stop: ${decision.stop_loss:,.2f}")
    print(f"Target: ${decision.take_profit:,.2f}")
    print(f"Position: {decision.position_size.quantity:.6f} BTC")
```

### API Integration

The new features are accessible via FastAPI endpoints:

```python
# main.py additions

@app.post("/optimization/grid")
async def run_grid_optimization(config: GridSearchConfig):
    """Run grid search optimization."""
    # Implementation

@app.post("/optimization/bayesian")
async def run_bayesian_optimization(config: BayesianConfig):
    """Run Bayesian optimization."""
    # Implementation

@app.get("/optimization/best/{strategy}/{symbol}/{timeframe}")
async def get_best_parameters(strategy: str, symbol: str, timeframe: str):
    """Get best parameters for a strategy."""
    storage = OptimizationStorage()
    results = storage.get_best_parameters(strategy, symbol, timeframe, top_n=1)
    return results[0] if results else None
```

---

## 5. Best Practices

### Strategy Development
1. Create new strategy functions in `app/research/signals.py`
2. Define Pydantic config classes for parameters
3. Add to `get_strategy_list()` and `generate_signal()`
4. Write unit tests in `tests/test_research_signals.py`

### Optimization Workflow
1. Start with grid search on coarse grid (3-5 values per parameter)
2. Identify promising regions
3. Run Bayesian optimization for fine-tuning
4. Validate on out-of-sample data
5. Monitor performance in production
6. Re-optimize periodically (weekly/monthly)

### Parameter Selection
- **Sharpe Ratio**: Best for risk-adjusted returns
- **Win Rate**: For high-frequency strategies
- **Profit Factor**: For maximizing gross returns
- **Max Drawdown**: For risk-sensitive portfolios

### Range Interpretation
- **Narrow ranges** (< 0.5%): Low volatility, tight execution
- **Medium ranges** (0.5-1.5%): Normal market conditions
- **Wide ranges** (> 1.5%): High volatility, flexible orders

---

## 6. Performance Considerations

### Optimization Time
- **Grid Search**: O(n^k) where n = values per param, k = parameters
  - Example: 5^4 = 625 combinations
- **Bayesian**: O(n) where n = n_calls
  - Typically 30-100 calls sufficient

### Storage Requirements
- SQLite database: ~1KB per result
- Parquet export: ~50% smaller than CSV
- Recommended: Store top 100 results per strategy

### Computational Resources
- Single optimization: 1-10 minutes (depends on data size)
- Full strategy suite: 30-60 minutes (9 strategies)
- Recommended: Run during off-hours or weekends

---

## 7. Troubleshooting

### Common Issues

**Issue**: `ImportError: scikit-optimize not found`
**Solution**: Install with `pip install scikit-optimize`

**Issue**: Optimization returns no results
**Solution**: Check data quality, reduce parameter ranges, increase n_calls

**Issue**: Ranges are None
**Solution**: Ensure `calculate_ranges=True` and sufficient data for ATR calculation

**Issue**: Weights file not found
**Solution**: Run `python scripts/optimize_strategies.py --update-weights` first

---

## 8. Future Enhancements

- [ ] Walk-forward optimization
- [ ] Multi-objective optimization (Sharpe + drawdown)
- [ ] Online learning for dynamic parameter adjustment
- [ ] Ensemble methods for strategy combination
- [ ] Real-time range adjustment based on market regime

---

## References

- Example script: `examples/example_new_strategies_optimization.py`
- Optimization CLI: `scripts/optimize_strategies.py`
- Tests: `tests/test_research_signals.py`
- API: `main.py`

