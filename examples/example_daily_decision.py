"""Complete daily decision workflow example.

This example demonstrates:
1. Load data
2. Generate signals from multiple strategies
3. Combine signals
4. Get multi-horizon advice
5. Make daily trading decision
6. Save to paper trading DB
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Data
from app.data.store import DataStore

# Signals
from app.research.signals import ma_crossover, rsi_regime_pullback, trend_following_ema
from app.research.combine import combine_signals

# Service
from app.service import (
    DecisionEngine,
    MarketAdvisor,
    calculate_entry_band,
    calculate_tp_sl,
    TPSLConfig,
    PaperTradingDB
)
from app.data.schema import DecisionRecord


def load_data():
    """Load data for decision."""
    print("\n" + "="*60)
    print("LOADING DATA")
    print("="*60)
    
    try:
        store = DataStore()
        symbols = store.list_stored_symbols()
        
        if symbols:
            symbol, timeframe = symbols[0]
            print(f"Loading: {symbol} {timeframe}")
            bars = store.read_bars(symbol, timeframe)
            
            if len(bars) >= 100:
                df = pd.DataFrame([bar.to_dict() for bar in bars])
                df = df.sort_values('timestamp').reset_index(drop=True)
                df = df.tail(500).reset_index(drop=True)
                print(f"✓ Loaded {len(df)} bars")
                return df
    
    except Exception as e:
        print(f"Error: {e}")
    
    # Generate synthetic
    print("Using synthetic data...")
    return generate_synthetic_data()


def generate_synthetic_data():
    """Generate synthetic data."""
    np.random.seed(42)
    n_bars = 300
    
    start_time = datetime.now() - timedelta(hours=n_bars)
    timestamps = [(start_time + timedelta(hours=i)).timestamp() * 1000 for i in range(n_bars)]
    
    close = 50000 * (1 + np.random.randn(n_bars) * 0.01).cumprod()
    high = close * (1 + abs(np.random.randn(n_bars)) * 0.005)
    low = close * (1 - abs(np.random.randn(n_bars)) * 0.005)
    open_price = close + np.random.randn(n_bars) * 100
    volume = abs(np.random.randn(n_bars)) * 1000000 + 500000
    
    return pd.DataFrame({
        'timestamp': timestamps,
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
        'symbol': 'BTC/USDT',
        'timeframe': '1h'
    })


def generate_signals(df):
    """Generate and combine signals."""
    print("\n" + "="*60)
    print("GENERATING SIGNALS")
    print("="*60)
    
    # Generate from strategies
    sig1 = ma_crossover(df['close'], fast_period=10, slow_period=20)
    sig2 = rsi_regime_pullback(df['close'])
    sig3 = trend_following_ema(df['close'])
    
    print(f"  ✓ MA Crossover: Signal = {sig1.signal.iloc[-1]}")
    print(f"  ✓ RSI Regime: Signal = {sig2.signal.iloc[-1]}")
    print(f"  ✓ Triple EMA: Signal = {sig3.signal.iloc[-1]}")
    
    # Combine
    returns = df['close'].pct_change()
    combined = combine_signals(
        {'ma': sig1.signal, 'rsi': sig2.signal, 'ema': sig3.signal},
        method='simple_average',
        returns=returns
    )
    
    print(f"\n  ✓ Combined Signal: {combined.signal.iloc[-1]}")
    print(f"  ✓ Confidence: {combined.confidence.iloc[-1]:.2f}")
    
    return combined


def get_market_advice(df, combined):
    """Get multi-horizon market advice."""
    print("\n" + "="*60)
    print("MULTI-HORIZON ADVICE")
    print("="*60)
    
    advisor = MarketAdvisor()
    advice = advisor.get_advice(
        df_intraday=df,
        current_signal=int(combined.signal.iloc[-1]),
        signal_strength=float(combined.confidence.iloc[-1]),
        symbol=df['symbol'].iloc[0]
    )
    
    print(f"\n📊 Short-term (Today):")
    print(f"  Signal: {advice.short_term.signal}")
    print(f"  Entry Timing: {advice.short_term.entry_timing}")
    print(f"  Volatility: {advice.short_term.volatility_state}")
    print(f"  Recommended Risk: {advice.short_term.recommended_risk_pct:.2%}")
    
    print(f"\n📈 Medium-term (Week):")
    print(f"  Trend: {advice.medium_term.trend_direction}")
    print(f"  EMA200: {advice.medium_term.ema200_position}")
    print(f"  Filter: {advice.medium_term.filter_recommendation}")
    
    print(f"\n🌍 Long-term (Regime):")
    print(f"  Regime: {advice.long_term.regime}")
    print(f"  Volatility Regime: {advice.long_term.volatility_regime}")
    print(f"  Recommended Exposure: {advice.long_term.recommended_exposure:.0%}")
    
    print(f"\n🎯 Consensus:")
    print(f"  Direction: {advice.consensus_direction}")
    print(f"  Confidence: {advice.confidence_score:.2%}")
    print(f"  Final Risk Recommendation: {advice.recommended_risk_pct:.2%}")
    
    return advice


def make_daily_decision(df, combined, advice):
    """Make daily trading decision."""
    print("\n" + "="*60)
    print("DAILY DECISION")
    print("="*60)
    
    engine = DecisionEngine()
    
    decision = engine.make_decision(
        df=df,
        signals=combined.signal,
        signal_strength=combined.confidence,
        signal_source="combined_ensemble",
        capital=100000.0,
        risk_pct=advice.recommended_risk_pct
    )
    
    print(f"\n📅 Decision for {decision.trading_day}:")
    print(f"  Window: {decision.window}")
    print(f"  Signal: {decision.signal}")
    print(f"  Should Execute: {decision.should_execute}")
    
    if decision.should_execute:
        print(f"\n💰 Trade Details:")
        print(f"  Entry: ${decision.entry_price:,.2f}")
        print(f"  Entry Mid (VWAP): ${decision.entry_mid:,.2f}")
        print(f"  Stop Loss: ${decision.stop_loss:,.2f}")
        print(f"  Take Profit: ${decision.take_profit:,.2f}")
        print(f"  Position Size: {decision.position_size.quantity:.4f} units")
        print(f"  Notional: ${decision.position_size.notional_value:,.2f}")
        print(f"  Risk: ${decision.position_size.risk_amount:,.2f} ({decision.position_size.risk_pct:.2%})")
    else:
        print(f"\n⏸️  Skip Reason: {decision.skip_reason}")
    
    return decision


def save_to_database(decision, df):
    """Save decision to paper trading database."""
    if not decision.should_execute:
        return
    
    print("\n" + "="*60)
    print("SAVING TO DATABASE")
    print("="*60)
    
    try:
        db = PaperTradingDB()
        
        # Create decision record
        record = DecisionRecord(
            decision_id=f"DEC_{decision.trading_day}_{df['symbol'].iloc[0].replace('/', '')}",
            trading_day=decision.trading_day,
            symbol=df['symbol'].iloc[0],
            timeframe=df['timeframe'].iloc[0],
            signal=decision.signal,
            signal_strength=decision.signal_strength,
            signal_source=decision.signal_source,
            entry_price=decision.entry_price,
            entry_mid=decision.entry_mid,
            stop_loss=decision.stop_loss,
            take_profit=decision.take_profit,
            position_size=decision.position_size.quantity if decision.position_size else 0,
            risk_amount=decision.position_size.risk_amount if decision.position_size else 0,
            risk_pct=decision.position_size.risk_pct if decision.position_size else 0,
            executed=True,
            window=decision.window
        )
        
        db.save_decision(record)
        print(f"  ✅ Decision saved to database")
        print(f"  Decision ID: {record.decision_id}")
        
    except Exception as e:
        print(f"  ⚠️  Error saving to DB: {e}")


def main():
    """Run complete daily decision workflow."""
    print("="*60)
    print("ONE MARKET - Daily Decision Workflow")
    print("Epic 4: Complete Decision Pipeline")
    print("="*60)
    
    try:
        # 1. Load data
        df = load_data()
        
        # 2. Generate and combine signals
        combined = generate_signals(df)
        
        # 3. Get multi-horizon advice
        advice = get_market_advice(df, combined)
        
        # 4. Make daily decision
        decision = make_daily_decision(df, combined, advice)
        
        # 5. Save to database
        save_to_database(decision, df)
        
        print("\n" + "="*60)
        print("WORKFLOW COMPLETED! ✅")
        print("="*60)
        
        print("\n📚 What This Demo Showed:")
        print("  ✅ Multi-strategy signal generation")
        print("  ✅ Signal combination (ensemble)")
        print("  ✅ Multi-horizon market analysis")
        print("  ✅ Daily decision with all rules")
        print("  ✅ Entry band optimization (VWAP)")
        print("  ✅ TP/SL calculation")
        print("  ✅ Position sizing with risk management")
        print("  ✅ Database persistence")
        
        print("\n📖 Documentation:")
        print("  - EPIC4_SUMMARY.md: Complete Epic 4 documentation")
        print("  - PROJECT_STATUS.md: Overall project status")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

