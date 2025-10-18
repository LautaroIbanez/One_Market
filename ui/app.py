"""One Market - Streamlit Dashboard.

This is the main UI application providing:
- Symbol and timeframe selection
- Trading mode (paper/live)
- Daily signal panel with entry band, SL/TP
- Performance metrics (12m rolling)
- Interactive charts with entry zones
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.data.store import DataStore
from app.service import DecisionEngine, MarketAdvisor
from app.service.tp_sl_engine import TPSLConfig
from app.research.signals import ma_crossover, rsi_regime_pullback, trend_following_ema
from app.research.combine import combine_signals
from app.config.settings import settings


# Page config
st.set_page_config(
    page_title="One Market - Trading Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("📊 One Market - Daily Trading Platform")
st.markdown("---")


# ============================================================
# SIDEBAR - Configuration
# ============================================================

with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Symbol selection
    available_symbols = settings.DEFAULT_SYMBOLS
    symbol = st.selectbox(
        "Symbol",
        options=available_symbols,
        index=0 if available_symbols else None
    )
    
    # Timeframe selection
    timeframe = st.selectbox(
        "Timeframe",
        options=["15m", "1h", "4h", "1d"],
        index=1  # Default to 1h
    )
    
    # Mode
    mode = st.radio(
        "Trading Mode",
        options=["Paper Trading", "Live Trading"],
        index=0
    )
    
    st.markdown("---")
    
    # Risk parameters
    st.subheader("Risk Management")
    
    risk_pct = st.slider(
        "Risk per Trade (%)",
        min_value=0.5,
        max_value=5.0,
        value=2.0,
        step=0.1
    ) / 100
    
    capital = st.number_input(
        "Capital ($)",
        min_value=1000.0,
        value=100000.0,
        step=1000.0
    )
    
    rr_target = st.slider(
        "Target R/R Ratio",
        min_value=1.0,
        max_value=5.0,
        value=1.5,
        step=0.1
    )
    
    st.markdown("---")
    
    # TP/SL Method
    st.subheader("TP/SL Configuration")
    
    tpsl_method = st.selectbox(
        "TP/SL Method",
        options=["ATR", "Swing", "Hybrid"],
        index=0
    )
    
    atr_multiplier_sl = st.number_input(
        "ATR Multiplier SL",
        min_value=1.0,
        max_value=5.0,
        value=2.0,
        step=0.1
    )
    
    atr_multiplier_tp = st.number_input(
        "ATR Multiplier TP",
        min_value=1.0,
        max_value=10.0,
        value=3.0,
        step=0.1
    )
    
    # Refresh button
    st.markdown("---")
    refresh = st.button("🔄 Refresh Data", use_container_width=True)


# ============================================================
# MAIN AREA
# ============================================================

# Load data
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data(symbol, timeframe):
    """Load OHLCV data."""
    try:
        store = DataStore()
        bars = store.read_bars(symbol, timeframe)
        
        if not bars:
            return None
        
        df = pd.DataFrame([bar.to_dict() for bar in bars])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Take last 500 bars for display
        df = df.tail(500).reset_index(drop=True)
        
        return df
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


# Generate signals
def generate_current_signals(df):
    """Generate signals from strategies."""
    try:
        # Multiple strategies
        sig1 = ma_crossover(df['close'], fast_period=10, slow_period=20)
        sig2 = rsi_regime_pullback(df['close'])
        sig3 = trend_following_ema(df['close'])
        
        # Combine
        returns = df['close'].pct_change()
        combined = combine_signals(
            {
                'ma_cross': sig1.signal,
                'rsi_regime': sig2.signal,
                'triple_ema': sig3.signal
            },
            method='simple_average',
            returns=returns
        )
        
        return combined, {
            'ma_cross': sig1.signal.iloc[-1],
            'rsi_regime': sig2.signal.iloc[-1],
            'triple_ema': sig3.signal.iloc[-1]
        }
    
    except Exception as e:
        st.error(f"Error generating signals: {e}")
        return None, None


# Make decision
def make_decision(df, combined_signal):
    """Make daily trading decision."""
    try:
        # Get advisor recommendation
        advisor = MarketAdvisor(default_risk_pct=risk_pct)
        advice = advisor.get_advice(
            df_intraday=df,
            current_signal=int(combined_signal.signal.iloc[-1]),
            signal_strength=float(combined_signal.confidence.iloc[-1]),
            symbol=symbol
        )
        
        # Make decision
        engine = DecisionEngine()
        decision = engine.make_decision(
            df,
            combined_signal.signal,
            signal_strength=combined_signal.confidence,
            capital=capital,
            risk_pct=advice.recommended_risk_pct
        )
        
        return decision, advice
    
    except Exception as e:
        st.error(f"Error making decision: {e}")
        return None, None


# Load data
df = load_data(symbol, timeframe)

if df is not None and len(df) > 0:
    # Generate signals
    combined, individual_signals = generate_current_signals(df)
    
    if combined is not None:
        # Make decision
        decision, advice = make_decision(df, combined)
        
        # ============================================================
        # TODAY'S SIGNAL PANEL
        # ============================================================
        
        st.header("📍 Today's Signal")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            signal_value = int(combined.signal.iloc[-1])
            if signal_value == 1:
                st.metric("Direction", "🟢 LONG", delta="Buy")
            elif signal_value == -1:
                st.metric("Direction", "🔴 SHORT", delta="Sell")
            else:
                st.metric("Direction", "⚪ FLAT", delta="Wait")
        
        with col2:
            confidence = float(combined.confidence.iloc[-1])
            st.metric("Confidence", f"{confidence:.0%}")
        
        with col3:
            current_price = float(df['close'].iloc[-1])
            st.metric("Market Price", f"${current_price:,.2f}")
        
        with col4:
            if decision and decision.should_execute:
                st.metric("Status", "✅ EXECUTE")
            else:
                st.metric("Status", "⏸️ SKIP")
        
        # Individual signals
        st.subheader("Strategy Breakdown")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("MA Crossover", 
                     "🟢" if individual_signals['ma_cross'] == 1 else ("🔴" if individual_signals['ma_cross'] == -1 else "⚪"))
        with col2:
            st.metric("RSI Regime", 
                     "🟢" if individual_signals['rsi_regime'] == 1 else ("🔴" if individual_signals['rsi_regime'] == -1 else "⚪"))
        with col3:
            st.metric("Triple EMA", 
                     "🟢" if individual_signals['triple_ema'] == 1 else ("🔴" if individual_signals['triple_ema'] == -1 else "⚪"))
        
        st.markdown("---")
        
        # ============================================================
        # TRADING DETAILS
        # ============================================================
        
        if decision and decision.should_execute:
            st.header("💰 Trading Details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Entry")
                st.metric("Entry Price", f"${decision.entry_price:,.2f}")
                st.metric("Entry Mid (VWAP)", f"${decision.entry_mid:,.2f}" if decision.entry_mid else "N/A")
                st.metric("Entry Spread", f"{decision.entry_band_beta:.2%}" if decision.entry_band_beta else "0%")
            
            with col2:
                st.subheader("Stops")
                st.metric("Stop Loss", f"${decision.stop_loss:,.2f}" if decision.stop_loss else "N/A")
                st.metric("Take Profit", f"${decision.take_profit:,.2f}" if decision.take_profit else "N/A")
                if decision.stop_loss and decision.take_profit:
                    risk = abs(decision.entry_price - decision.stop_loss)
                    reward = abs(decision.take_profit - decision.entry_price)
                    rr = reward / risk if risk > 0 else 0
                    st.metric("R/R Ratio", f"{rr:.2f}")
            
            # Position sizing
            st.subheader("Position Sizing")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if decision.position_size:
                    st.metric("Quantity", f"{decision.position_size.quantity:.4f}")
            with col2:
                if decision.position_size:
                    st.metric("Notional", f"${decision.position_size.notional_value:,.2f}")
            with col3:
                if decision.position_size:
                    st.metric("Risk Amount", f"${decision.position_size.risk_amount:,.2f}")
            
        else:
            st.info(f"⏸️ No trade today: {decision.skip_reason if decision else 'No decision available'}")
        
        st.markdown("---")
        
        # ============================================================
        # MULTI-HORIZON ADVICE
        # ============================================================
        
        if advice:
            st.header("🧭 Multi-Horizon Analysis")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("📊 Short-term (Today)")
                st.metric("Signal", advice.short_term.signal)
                st.metric("Entry Timing", advice.short_term.entry_timing)
                st.metric("Volatility", advice.short_term.volatility_state)
                st.metric("Recommended Risk", f"{advice.short_term.recommended_risk_pct:.2%}")
            
            with col2:
                st.subheader("📈 Medium-term (Week)")
                st.metric("Trend", advice.medium_term.trend_direction)
                st.metric("EMA200", advice.medium_term.ema200_position)
                st.metric("Filter", advice.medium_term.filter_recommendation)
                st.metric("RSI Weekly", f"{advice.medium_term.rsi_weekly:.1f}")
            
            with col3:
                st.subheader("🌍 Long-term (Regime)")
                st.metric("Regime", advice.long_term.regime.upper())
                st.metric("Vol Regime", advice.long_term.volatility_regime)
                st.metric("Exposure Rec", f"{advice.long_term.recommended_exposure:.0%}")
                st.metric("Regime Prob", f"{advice.long_term.regime_probability:.0%}")
            
            # Consensus
            st.markdown("---")
            st.subheader("🎯 Consensus")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if advice.consensus_direction == 1:
                    st.success("Direction: LONG")
                elif advice.consensus_direction == -1:
                    st.error("Direction: SHORT")
                else:
                    st.info("Direction: NEUTRAL")
            
            with col2:
                st.metric("Confidence", f"{advice.confidence_score:.0%}")
            
            with col3:
                st.metric("Final Risk Rec", f"{advice.recommended_risk_pct:.2%}")
        
        st.markdown("---")
        
        # ============================================================
        # CHART
        # ============================================================
        
        st.header("📈 Price Chart")
        
        # Prepare chart data
        chart_df = df.tail(60).copy()  # Last 60 bars
        chart_df['datetime'] = pd.to_datetime(chart_df['timestamp'], unit='ms')
        
        # Create candlestick chart
        fig = go.Figure(data=[go.Candlestick(
            x=chart_df['datetime'],
            open=chart_df['open'],
            high=chart_df['high'],
            low=chart_df['low'],
            close=chart_df['close'],
            name="Price"
        )])
        
        # Add entry band if decision exists
        if decision and decision.should_execute:
            # Entry price line
            fig.add_hline(
                y=decision.entry_price,
                line_dash="dash",
                line_color="blue",
                annotation_text=f"Entry: ${decision.entry_price:,.2f}",
                annotation_position="right"
            )
            
            # Stop loss line
            if decision.stop_loss:
                fig.add_hline(
                    y=decision.stop_loss,
                    line_dash="dot",
                    line_color="red",
                    annotation_text=f"SL: ${decision.stop_loss:,.2f}",
                    annotation_position="right"
                )
            
            # Take profit line
            if decision.take_profit:
                fig.add_hline(
                    y=decision.take_profit,
                    line_dash="dot",
                    line_color="green",
                    annotation_text=f"TP: ${decision.take_profit:,.2f}",
                    annotation_position="right"
                )
            
            # Entry band zone (rectangle)
            if decision.entry_mid:
                spread = abs(decision.entry_price - decision.entry_mid)
                fig.add_shape(
                    type="rect",
                    x0=chart_df['datetime'].iloc[0],
                    x1=chart_df['datetime'].iloc[-1],
                    y0=decision.entry_mid - spread,
                    y1=decision.entry_mid + spread,
                    fillcolor="lightblue",
                    opacity=0.2,
                    line_width=0
                )
        
        # Update layout
        fig.update_layout(
            title=f"{symbol} - {timeframe}",
            yaxis_title="Price (USD)",
            xaxis_title="Time",
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # ============================================================
        # PERFORMANCE METRICS (12M ROLLING)
        # ============================================================
        
        st.header("📊 Performance Metrics (12 Months)")
        
        # Calculate simple backtest metrics
        returns = df['close'].pct_change()
        
        # Use last signal for simple calculation
        if combined is not None:
            strategy_returns = combined.signal.shift(1) * returns
            strategy_returns = strategy_returns.dropna()
            
            # Take last 12 months (approx based on timeframe)
            if timeframe == "1h":
                lookback = min(24 * 365, len(strategy_returns))
            elif timeframe == "1d":
                lookback = min(365, len(strategy_returns))
            else:
                lookback = len(strategy_returns)
            
            recent_returns = strategy_returns.tail(lookback)
            
            # Calculate metrics
            total_return = (1 + recent_returns).prod() - 1
            
            # Sharpe
            sharpe = (recent_returns.mean() / recent_returns.std() * np.sqrt(252)) if recent_returns.std() > 0 else 0
            
            # Max DD
            equity = (1 + recent_returns).cumprod()
            running_max = equity.expanding().max()
            drawdown = (equity - running_max) / running_max
            max_dd = abs(drawdown.min())
            
            # Win rate (approximate)
            win_rate = (recent_returns > 0).mean()
            
            # CAGR
            days = lookback / (24 if timeframe == "1h" else 1)
            years = days / 365.25
            cagr = ((1 + total_return) ** (1 / years) - 1) if years > 0 else 0
            
            # Profit Factor (approximate)
            wins = recent_returns[recent_returns > 0].sum()
            losses = abs(recent_returns[recent_returns < 0].sum())
            pf = wins / losses if losses > 0 else 0
            
            # Display metrics
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                st.metric("CAGR", f"{cagr:.1%}")
            
            with col2:
                st.metric("Sharpe", f"{sharpe:.2f}")
            
            with col3:
                st.metric("Max DD", f"{max_dd:.1%}")
            
            with col4:
                st.metric("Win Rate", f"{win_rate:.1%}")
            
            with col5:
                st.metric("Profit Factor", f"{pf:.2f}")
            
            with col6:
                st.metric("Total Return", f"{total_return:.1%}")
            
            # Equity curve
            st.subheader("Equity Curve")
            
            equity_df = pd.DataFrame({
                'datetime': df.tail(lookback)['timestamp'].apply(lambda x: pd.to_datetime(x, unit='ms')),
                'equity': capital * equity
            })
            
            fig_equity = go.Figure()
            fig_equity.add_trace(go.Scatter(
                x=equity_df['datetime'],
                y=equity_df['equity'],
                mode='lines',
                name='Equity',
                line=dict(color='blue', width=2)
            ))
            
            fig_equity.update_layout(
                title="Equity Curve",
                yaxis_title="Capital ($)",
                xaxis_title="Time",
                height=300,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_equity, use_container_width=True)
            
            # Drawdown chart
            st.subheader("Drawdown")
            
            dd_df = pd.DataFrame({
                'datetime': df.tail(lookback)['timestamp'].apply(lambda x: pd.to_datetime(x, unit='ms')),
                'drawdown': drawdown * 100
            })
            
            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(
                x=dd_df['datetime'],
                y=dd_df['drawdown'],
                mode='lines',
                name='Drawdown',
                fill='tozeroy',
                line=dict(color='red', width=1)
            ))
            
            fig_dd.update_layout(
                title="Drawdown (%)",
                yaxis_title="Drawdown (%)",
                xaxis_title="Time",
                height=250,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_dd, use_container_width=True)
        
        # ============================================================
        # DATA STATUS
        # ============================================================
        
        st.markdown("---")
        st.header("ℹ️ Data Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Bars Loaded", len(df))
        
        with col2:
            latest_ts = pd.to_datetime(df['timestamp'].iloc[-1], unit='ms')
            st.metric("Latest Data", latest_ts.strftime('%Y-%m-%d %H:%M'))
        
        with col3:
            data_age = datetime.now() - latest_ts.replace(tzinfo=None)
            st.metric("Data Age", f"{data_age.total_seconds() / 60:.0f} min")

else:
    st.warning(f"No data available for {symbol} {timeframe}")
    st.info("Please run example_fetch_data.py to load data first")


# Footer
st.markdown("---")
st.caption(f"One Market v1.0.0 | Mode: {mode} | Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

