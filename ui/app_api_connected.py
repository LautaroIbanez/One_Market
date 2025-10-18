"""One Market - Streamlit Dashboard (API Connected).

This version connects to the FastAPI backend for real-time data.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests


# Page config
st.set_page_config(
    page_title="One Market - Trading Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_URL = st.sidebar.text_input("API URL", value="http://localhost:8000")

# Title
st.title("📊 One Market - Daily Trading Platform")
st.markdown("---")


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Health Check
    try:
        health_response = requests.get(f"{API_URL}/health", timeout=2)
        if health_response.status_code == 200:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Error")
    except:
        st.warning("⚠️ API Not Reachable")
    
    st.markdown("---")
    
    # Get symbols from API
    try:
        symbols_response = requests.get(f"{API_URL}/symbols", timeout=5)
        if symbols_response.status_code == 200:
            symbols_data = symbols_response.json()
            available_symbols = symbols_data.get('symbols', ['BTC/USDT'])
        else:
            available_symbols = ['BTC/USDT', 'ETH/USDT']
    except:
        available_symbols = ['BTC/USDT', 'ETH/USDT']
    
    symbol = st.selectbox("Symbol", options=available_symbols)
    
    timeframe = st.selectbox(
        "Timeframe",
        options=["15m", "1h", "4h", "1d"],
        index=1
    )
    
    mode = st.radio(
        "Mode",
        options=["Paper", "Live"],
        index=0
    )
    
    st.markdown("---")
    
    # Get strategies from API
    try:
        strategies_response = requests.get(f"{API_URL}/strategies", timeout=5)
        if strategies_response.status_code == 200:
            strategies_data = strategies_response.json()
            available_strategies = strategies_data.get('strategies', [])
        else:
            available_strategies = ["ma_crossover", "rsi_regime_pullback"]
    except:
        available_strategies = ["ma_crossover", "rsi_regime_pullback"]
    
    selected_strategies = st.multiselect(
        "Strategies",
        options=available_strategies,
        default=available_strategies[:2] if len(available_strategies) >= 2 else available_strategies
    )
    
    st.markdown("---")
    
    capital = st.number_input("Capital ($)", value=100000.0, step=1000.0)
    
    # Generate button
    generate_btn = st.button("🎯 Generate Decision", use_container_width=True)


# ============================================================
# MAIN AREA
# ============================================================

if generate_btn and selected_strategies:
    with st.spinner("Generating decision..."):
        try:
            # Call decision endpoint
            decision_request = {
                "symbol": symbol,
                "timeframe": timeframe,
                "strategies": selected_strategies,
                "combination_method": "simple_average",
                "capital": capital
            }
            
            response = requests.post(
                f"{API_URL}/decision",
                json=decision_request,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                decision = data.get('decision', {})
                advice = data.get('advice', {})
                
                # ============================================================
                # TODAY'S DECISION
                # ============================================================
                
                st.header("📍 Today's Decision")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    signal = decision.get('signal', 0)
                    if signal == 1:
                        st.metric("Direction", "🟢 LONG", delta="Buy")
                    elif signal == -1:
                        st.metric("Direction", "🔴 SHORT", delta="Sell")
                    else:
                        st.metric("Direction", "⚪ FLAT", delta="Wait")
                
                with col2:
                    confidence = advice.get('confidence', 0)
                    st.metric("Confidence", f"{confidence:.0%}")
                
                with col3:
                    entry_price = decision.get('entry_price')
                    if entry_price:
                        st.metric("Entry", f"${entry_price:,.2f}")
                    else:
                        st.metric("Entry", "N/A")
                
                with col4:
                    should_execute = decision.get('should_execute', False)
                    if should_execute:
                        st.metric("Status", "✅ EXECUTE")
                    else:
                        st.metric("Status", "⏸️ SKIP")
                
                # Details
                if should_execute:
                    st.subheader("Trading Details")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Stop Loss", f"${decision.get('stop_loss', 0):,.2f}")
                    with col2:
                        st.metric("Take Profit", f"${decision.get('take_profit', 0):,.2f}")
                    with col3:
                        st.metric("Position Size", f"{decision.get('position_size', 0):.4f}")
                else:
                    st.info(f"⏸️ Reason: {decision.get('skip_reason', 'Unknown')}")
                
                # Multi-horizon advice
                st.markdown("---")
                st.header("🧭 Multi-Horizon Analysis")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    short_term = advice.get('short_term', {})
                    st.subheader("📊 Short-term")
                    st.write(f"Entry Timing: {short_term.get('entry_timing', 'N/A')}")
                    st.write(f"Volatility: {short_term.get('volatility_state', 'N/A')}")
                    st.write(f"Risk Rec: {short_term.get('recommended_risk_pct', 0):.2%}")
                
                with col2:
                    medium_term = advice.get('medium_term', {})
                    st.subheader("📈 Medium-term")
                    st.write(f"EMA200: {medium_term.get('ema200_position', 'N/A')}")
                    st.write(f"Filter: {medium_term.get('filter_recommendation', 'N/A')}")
                    st.write(f"Trend: {medium_term.get('trend_strength', 0):.2f}")
                
                with col3:
                    long_term = advice.get('long_term', {})
                    st.subheader("🌍 Long-term")
                    st.write(f"Regime: {long_term.get('regime', 'N/A').upper()}")
                    st.write(f"Vol Regime: {long_term.get('volatility_regime', 'N/A')}")
                    st.write(f"Exposure: {long_term.get('recommended_exposure', 0):.0%}")
                
                # Consensus
                st.subheader("🎯 Consensus")
                consensus = advice.get('consensus', 0)
                if consensus == 1:
                    st.success("Direction: LONG")
                elif consensus == -1:
                    st.error("Direction: SHORT")
                else:
                    st.info("Direction: NEUTRAL")
                
                st.metric("Final Risk Recommendation", f"{advice.get('recommended_risk', 0):.2%}")
                
                st.success("✅ Decision generated successfully!")
            
            else:
                st.error(f"API Error: {response.status_code}")
                st.error(response.text)
        
        except requests.exceptions.Timeout:
            st.error("⏱️ API request timed out. Is the server running?")
            st.info("Start the API with: python main.py")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")

else:
    st.info("Configure settings in sidebar and click 'Generate Decision'")
    
    st.markdown("""
    ### 🚀 Getting Started
    
    1. **Start the API server**:
       ```bash
       python main.py
       ```
    
    2. **Ensure you have data**:
       ```bash
       python examples/example_fetch_data.py
       ```
    
    3. **Select symbol and strategies** in the sidebar
    
    4. **Click "Generate Decision"** to get trading signal
    
    ### 📖 Features
    
    - **Real-time signal generation** from multiple strategies
    - **Multi-horizon analysis** (short/medium/long-term)
    - **Entry band optimization** with VWAP
    - **TP/SL calculation** with multiple methods
    - **Risk management** with dynamic adjustments
    - **Performance metrics** (12-month rolling)
    
    ### 📊 Available Strategies
    
    - MA Crossover (trend following)
    - RSI Regime + Pullback (mean reversion)
    - Donchian Breakout + ADX (breakout)
    - MACD Histogram + ATR (momentum)
    - Mean Reversion (Bollinger Bands)
    - Triple EMA (multi-timeframe)
    """)

# Footer
st.markdown("---")
st.caption(f"One Market v1.0.0 | Connected to: {API_URL} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

