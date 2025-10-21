"""
One Market - Complete UI
Full-featured trading dashboard with real API integration.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import json
import time

# Page config
st.set_page_config(
    page_title="One Market - Complete",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("📊 One Market - Complete Trading System")
st.markdown("**Sistema de Trading Multi-Timeframe con Análisis Cuantitativo Avanzado**")

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Sidebar
st.sidebar.header("⚙️ Configuración del Sistema")

# Symbol selection
symbol = st.sidebar.selectbox(
    "Símbolo",
    ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"],
    index=0
)

# Capital
capital = st.sidebar.number_input(
    "Capital Disponible ($)",
    min_value=1000.0,
    max_value=1000000.0,
    value=10000.0,
    step=1000.0
)

# Risk percentage
risk_pct = st.sidebar.slider(
    "Riesgo por Trade (%)",
    min_value=0.5,
    max_value=5.0,
    value=2.0,
    step=0.1
)

# Timeframes
timeframes = st.sidebar.multiselect(
    "Timeframes a Analizar",
    ["15m", "1h", "4h", "1d"],
    default=["1h", "4h", "1d"]
)

# API Status Check
@st.cache_data(ttl=60)
def check_api_status():
    """Check if API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

# Data sync function
@st.cache_data(ttl=300)
def sync_data(symbol: str, timeframes: list):
    """Sync data for symbol and timeframes."""
    try:
        results = {}
        for tf in timeframes:
            response = requests.post(
                f"{API_BASE_URL}/data/sync",
                json={
                    "symbol": symbol,
                    "tf": tf,
                    "force_refresh": False
                },
                timeout=30
            )
            if response.status_code == 200:
                results[tf] = response.json()
            else:
                results[tf] = {"error": f"HTTP {response.status_code}"}
        return results
    except Exception as e:
        return {"error": str(e)}

# Get recommendation
@st.cache_data(ttl=600)
def get_complete_recommendation(symbol: str, capital: float, risk_pct: float):
    """Get complete recommendation from API."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/recommendation/daily",
            params={
                "symbol": symbol,
                "date": datetime.now().strftime('%Y-%m-%d')
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error al obtener recomendación: {e}")
        return None

# Run backtest
@st.cache_data(ttl=300)
def run_backtest(symbol: str, strategy: str, timeframe: str, capital: float):
    """Run backtest via API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/backtest/run",
            json={
                "symbol": symbol,
                "strategy": strategy,
                "timeframe": timeframe,
                "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
                "end_date": datetime.now().isoformat(),
                "initial_capital": capital,
                "risk_per_trade": 0.02
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error en backtest: {e}")
        return None

# Main content
st.header("🎯 Análisis Multi-Timeframe Completo")

# Check API status
api_status = check_api_status()
if not api_status:
    st.error("❌ API no disponible. Ejecuta EJECUTAR_API.bat primero.")
    st.stop()

st.success("✅ API conectada correctamente")

# Data sync section
st.subheader("📊 Sincronización de Datos")
if st.button("🔄 Sincronizar Datos", type="primary"):
    with st.spinner("Sincronizando datos..."):
        sync_results = sync_data(symbol, timeframes)
        
        for tf, result in sync_results.items():
            if "error" in result:
                st.error(f"❌ Error en {tf}: {result['error']}")
            else:
                st.success(f"✅ {tf}: {result.get('stored_count', 0)} barras sincronizadas")

# Recommendation section
st.subheader("🧠 Recomendación Diaria Inteligente")

recommendation = get_complete_recommendation(symbol, capital, risk_pct)

if recommendation:
    # Display recommendation metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Símbolo", recommendation.get("symbol", "N/A"))
        st.metric("⏰ Timeframe", recommendation.get("timeframe", "N/A"))
        st.metric("🎯 Dirección", recommendation.get("direction", "N/A"))
    
    with col2:
        st.metric("💡 Confianza", f"{recommendation.get('confidence', 0)}%")
        st.metric("📅 Fecha", recommendation.get("date", "N/A"))
        st.metric("🔒 Hash Dataset", recommendation.get("dataset_hash", "N/A")[:8] + "...")
    
    with col3:
        entry_price = recommendation.get("entry_price")
        st.metric("💰 Precio Entrada", f"${entry_price:.2f}" if entry_price else "N/A")
        stop_loss = recommendation.get("stop_loss")
        st.metric("🛑 Stop Loss", f"${stop_loss:.2f}" if stop_loss else "N/A")
        take_profit = recommendation.get("take_profit")
        st.metric("🎯 Take Profit", f"${take_profit:.2f}" if take_profit else "N/A")
    
    with col4:
        quantity = recommendation.get("quantity")
        st.metric("📦 Cantidad", f"{quantity:.6f}" if quantity else "N/A")
        risk_amount = recommendation.get("risk_amount")
        st.metric("💸 Riesgo ($)", f"${risk_amount:.2f}" if risk_amount else "N/A")
        risk_pct_actual = recommendation.get("risk_percentage")
        st.metric("📊 Riesgo (%)", f"{risk_pct_actual:.1f}%" if risk_pct_actual else "N/A")
    
    # Rationale
    st.markdown("---")
    st.subheader("🧠 Análisis y Razonamiento")
    rationale = recommendation.get("rationale", "Análisis no disponible")
    st.info(rationale)
    
    # Risk/Reward analysis
    if entry_price and stop_loss and take_profit:
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        rr_ratio = reward / risk if risk > 0 else 0
        
        st.markdown("---")
        st.subheader("📈 Análisis de Riesgo/Recompensa")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Riesgo", f"${risk:.2f}")
        with col2:
            st.metric("Recompensa", f"${reward:.2f}")
        with col3:
            st.metric("R/R Ratio", f"{rr_ratio:.2f}")

else:
    st.warning("⚠️ No se pudo obtener recomendación")

# Backtesting section
st.markdown("---")
st.subheader("🔬 Análisis de Estrategias")

# Strategy selection
strategies = [
    "MA Crossover",
    "RSI Regime Pullback", 
    "Trend Following EMA",
    "Donchian Breakout",
    "MACD Histogram",
    "Mean Reversion"
]

selected_strategy = st.selectbox("Seleccionar Estrategia", strategies)
selected_timeframe = st.selectbox("Seleccionar Timeframe", timeframes)

if st.button("🚀 Ejecutar Backtest", type="primary"):
    with st.spinner("Ejecutando backtest..."):
        backtest_result = run_backtest(symbol, selected_strategy, selected_timeframe, capital)
        
        if backtest_result:
            st.success("✅ Backtest completado")
            
            # Display backtest metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📈 CAGR", f"{backtest_result.get('cagr', 0):.1%}")
                st.metric("📊 Sharpe", f"{backtest_result.get('sharpe_ratio', 0):.2f}")
            
            with col2:
                st.metric("🎯 Win Rate", f"{backtest_result.get('win_rate', 0):.1%}")
                st.metric("📉 Max DD", f"{backtest_result.get('max_drawdown', 0):.1%}")
            
            with col3:
                st.metric("💰 Profit Factor", f"{backtest_result.get('profit_factor', 0):.2f}")
                st.metric("📊 Expectancy", f"${backtest_result.get('expectancy', 0):.2f}")
            
            with col4:
                st.metric("🔄 Trades", f"{backtest_result.get('total_trades', 0)}")
                st.metric("📈 Profit", f"${backtest_result.get('profit', 0):.2f}")
            
            # Display trades if available
            if "trades" in backtest_result and backtest_result["trades"]:
                st.markdown("---")
                st.subheader("📋 Historial de Trades")
                trades_df = pd.DataFrame(backtest_result["trades"])
                st.dataframe(trades_df, use_container_width=True)
        else:
            st.error("❌ Error en el backtest")

# System status
st.markdown("---")
st.subheader("📊 Estado del Sistema Completo")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🌐 API Status", "✅ Conectado" if api_status else "❌ Desconectado")

with col2:
    st.metric("📊 Datos", "✅ Disponibles" if api_status else "❌ No disponibles")

with col3:
    st.metric("🧠 Motor", "✅ Operativo" if api_status else "❌ Error")

with col4:
    st.metric("📈 Estrategias", f"{len(strategies)} disponibles")

# Footer
st.markdown("---")
st.markdown("**One Market Complete Trading System** - Sistema Completo")
st.markdown("*Análisis multi-timeframe con backtesting avanzado y recomendaciones inteligentes*")
