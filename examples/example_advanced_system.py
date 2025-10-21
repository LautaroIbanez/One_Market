"""Example: Complete Advanced Trading System.

This example demonstrates the full advanced trading system:
1. Multi-strategy engine with auto-selection
2. Advanced risk management (VaR, ES, correlations)
3. Continuous learning pipeline
4. Notification system
5. Stress testing

Usage:
    python examples/example_advanced_system.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime

from app.data.store import DataStore
from app.strategy import MultiStrategyEngine
from app.risk import AdvancedRiskManager
from app.learning import ContinuousLearningPipeline, LearningConfig
from app.simulation import StressTestEngine, ShockScenario, ShockType


def main():
    print("="*80)
    print("ADVANCED TRADING SYSTEM - COMPLETE DEMONSTRATION")
    print("="*80)
    
    # Load data
    print("\n[Step 1] Loading Market Data...")
    store = DataStore()
    bars = store.read_bars("BTC-USDT", "1h")
    
    if not bars:
        print("❌ No data available. Run: python scripts/sync_data.py")
        return
    
    df = pd.DataFrame([{
        'timestamp': bar.timestamp,
        'open': bar.open,
        'high': bar.high,
        'low': bar.low,
        'close': bar.close,
        'volume': bar.volume
    } for bar in bars])
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    print(f"OK - Loaded {len(df)} bars")
    print(f"  Date range: {pd.to_datetime(df['timestamp'].min(), unit='ms')} to {pd.to_datetime(df['timestamp'].max(), unit='ms')}")
    print(f"  Current price: ${df['close'].iloc[-1]:,.2f}")
    
    # Multi-Strategy Engine
    print("\n"+"="*80)
    print("[Step 2] Multi-Strategy Engine")
    print("="*80)
    
    engine = MultiStrategyEngine(
        capital=100000.0,
        auto_select_top_n=5,
        rolling_window_days=90
    )
    
    print("\n2a. Calculating strategy performance...")
    performance = engine.calculate_strategy_performance(df)
    
    print("\nTop Strategies by Sharpe Ratio:")
    sorted_perf = sorted(
        performance.items(),
        key=lambda x: x[1].sharpe_ratio,
        reverse=True
    )
    
    for i, (name, perf) in enumerate(sorted_perf[:5], 1):
        print(f"  {i}. {name:35s} Sharpe: {perf.sharpe_ratio:6.2f}  Win Rate: {perf.win_rate:5.1%}  Trades: {perf.total_trades:3d}")
    
    print("\n2b. Auto-selecting best strategies...")
    best_strategies = engine.auto_select_strategies(metric="sharpe_ratio")
    print(f"OK - Selected: {', '.join(best_strategies)}")
    
    print("\n2c. Generating ensemble signal...")
    ensemble = engine.aggregate_signals(df, method="weighted_vote", auto_select=True)
    print(f"OK - Signal: {ensemble.signal:2d}  Confidence: {ensemble.confidence:.1%}")
    print(f"  Contributing strategies: {len(ensemble.contributing_strategies)}")
    print(f"  Votes: {ensemble.strategy_votes}")
    
    # Advanced Risk Management
    print("\n"+"="*80)
    print("[Step 3] Advanced Risk Management")
    print("="*80)
    
    risk_mgr = AdvancedRiskManager(
        capital=100000.0,
        max_portfolio_var_pct=0.02,
        var_confidence=0.95
    )
    
    returns = df['close'].pct_change()
    
    print("\n3a. Calculating Value at Risk...")
    var_hist = risk_mgr.calculate_var_historical(returns, confidence_level=0.95)
    var_param = risk_mgr.calculate_var_parametric(returns, confidence_level=0.95)
    
    print(f"  Historical VaR (95%): ${var_hist.var_amount:,.2f} ({var_hist.var_pct:.2%})")
    print(f"  Parametric VaR (95%): ${var_param.var_amount:,.2f} ({var_param.var_pct:.2%})")
    
    print("\n3b. Calculating Expected Shortfall...")
    es = risk_mgr.calculate_expected_shortfall(returns)
    print(f"  Expected Shortfall: ${es.es_amount:,.2f} ({es.es_pct:.2%})")
    print(f"  (Average loss if VaR is exceeded)")
    
    print("\n3c. Calculating dynamic stop loss...")
    entry_price = df['close'].iloc[-1]
    signal_direction = ensemble.signal if ensemble.signal != 0 else 1
    
    stop = risk_mgr.calculate_dynamic_stop(
        df,
        entry_price,
        signal_direction,
        atr_period=14,
        base_atr_multiplier=2.0
    )
    
    print(f"  Entry Price: ${entry_price:,.2f}")
    print(f"  Dynamic Stop: ${stop.stop_loss:,.2f}")
    print(f"  ATR: ${stop.atr_value:,.2f}")
    print(f"  Volatility Regime: {stop.volatility_regime}")
    print(f"  Adjustment Factor: {stop.adjustment_factor:.2f}x")
    
    # Continuous Learning
    print("\n"+"="*80)
    print("[Step 4] Continuous Learning Pipeline")
    print("="*80)
    
    config = LearningConfig(
        symbol="BTC-USDT",
        timeframe="1h",
        recalibration_frequency_days=7,
        lookback_days=90
    )
    
    learning = ContinuousLearningPipeline(config)
    
    print("\n4a. Running daily backtest...")
    snapshots = learning.run_daily_backtest(engine)
    print(f"OK - Evaluated {len(snapshots)} strategies")
    
    print("\n4b. Checking system health...")
    health = learning.get_system_health()
    print(f"  Status: {health['status']}")
    if 'should_recalibrate' in health:
        print(f"  Should recalibrate: {health['should_recalibrate']}")
    print(f"  Total recalibrations: {health.get('total_recalibrations', 0)}")
    
    if learning.should_recalibrate():
        print("\n4c. Running recalibration...")
        print("  (This may take a few minutes...)")
        # Commented out to save time in demo
        # recal_result = learning.run_recalibration(force=False)
        # print(f"  ✓ Updated {recal_result.num_strategies_updated} strategies")
        print("  >> Skipped (uncomment to run)")
    
    # Stress Testing
    print("\n"+"="*80)
    print("[Step 5] Stress Testing")
    print("="*80)
    
    stress_engine = StressTestEngine(
        capital=100000.0,
        ruin_threshold=0.5
    )
    
    print("\n5a. Available stress scenarios:")
    for i, scenario in enumerate(stress_engine.standard_scenarios, 1):
        print(f"  {i}. {scenario.name:25s} ({scenario.shock_type.value})")
        print(f"     Price change: {scenario.price_change_pct:+.1%}, Volatility: {scenario.volatility_multiplier:.1f}x")
    
    print("\n5b. Running stress test (sample: 2 strategies × 2 scenarios)...")
    sample_strategies = best_strategies[:2]
    sample_scenarios = stress_engine.standard_scenarios[:2]
    
    stress_report = stress_engine.run_comprehensive_stress_test(
        df=df.tail(200),  # Use recent data only
        strategies=sample_strategies,
        scenarios=sample_scenarios,
        symbol="BTC-USDT",
        timeframe="1h"
    )
    
    print(f"\nOK - Stress test complete:")
    print(f"  Overall survival rate: {stress_report.overall_survival_rate:.1%}")
    print(f"  Best strategy: {stress_report.best_performing_strategy}")
    print(f"  Worst scenario: {stress_report.worst_scenario}")
    
    print("\n  Survival Matrix:")
    matrix = stress_engine.get_survival_matrix(stress_report)
    print(matrix.to_string())
    
    # Portfolio Summary
    print("\n"+"="*80)
    print("[Step 6] Portfolio Summary")
    print("="*80)
    
    portfolio_summary = engine.get_portfolio_summary()
    
    print(f"\nCapital: ${portfolio_summary['capital']:,.2f}")
    print(f"Enabled Strategies: {portfolio_summary['num_strategies_enabled']}/{portfolio_summary['num_strategies_total']}")
    print(f"Average Sharpe: {portfolio_summary['avg_sharpe_ratio']:.2f}")
    print(f"Average Win Rate: {portfolio_summary['avg_win_rate']:.1%}")
    print(f"Should Rebalance: {portfolio_summary['should_rebalance']}")
    
    if portfolio_summary.get('days_since_rebalance') is not None:
        print(f"Days Since Rebalance: {portfolio_summary['days_since_rebalance']}")
    
    # Risk Summary
    print("\n"+"="*80)
    print("[Step 7] Comprehensive Risk Summary")
    print("="*80)
    
    risk_summary = risk_mgr.get_risk_summary(returns)
    
    print(f"\nValue at Risk (95% confidence):")
    print(f"  Historical: ${risk_summary['var_historical_amount']:,.2f} ({risk_summary['var_historical_pct']:.2%})")
    print(f"  Parametric: ${risk_summary['var_parametric_amount']:,.2f} ({risk_summary['var_parametric_pct']:.2%})")
    
    print(f"\nExpected Shortfall:")
    print(f"  Amount: ${risk_summary['expected_shortfall_amount']:,.2f}")
    print(f"  Percentage: {risk_summary['expected_shortfall_pct']:.2%}")
    
    print(f"\nRisk Limits:")
    print(f"  Max Portfolio VaR: ${risk_summary['max_portfolio_var']:,.2f}")
    
    # Final Summary
    print("\n"+"="*80)
    print("SYSTEM DEMONSTRATION COMPLETE")
    print("="*80)
    
    print("\nKey Capabilities Demonstrated:")
    print("  [OK] Multi-strategy ensemble (9 strategies)")
    print("  [OK] Auto-selection of top performers")
    print("  [OK] Advanced risk metrics (VaR, ES)")
    print("  [OK] Dynamic stops adjusted by volatility")
    print("  [OK] Continuous learning pipeline")
    print("  [OK] Stress testing with 6 scenarios")
    print("  [OK] Performance tracking and ranking")
    
    print("\nNext Steps:")
    print("  1. Configure notifications in .env")
    print("  2. Run full stress test: see app/simulation/stress_testing.py")
    print("  3. Set up automated recalibration")
    print("  4. Integrate with live trading")
    
    print("\n"+"="*80)


if __name__ == "__main__":
    main()

