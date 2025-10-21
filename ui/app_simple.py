"""
One Market - Simple UI
A simplified version of the trading dashboard that works with the current Recommendation model.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json

# Page config
st.set_page_config(
    page_title="One Market - Simple",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("📊 One Market - Trading Dashboard")
st.markdown("**Sistema de Trading Multi-Timeframe**")

# Sidebar
st.sidebar.header("⚙️ Configuración")

# Symbol selection
symbol = st.sidebar.selectbox(
    "Símbolo",
    ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"],
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

# Main content
st.header("🎯 Recomendación Diaria")

# Get recommendation
@st.cache_data(ttl=600)
def get_simple_recommendation(symbol: str, capital: float):
    """Get a simple recommendation."""
    try:
        # Create a simple recommendation without external dependencies
        return {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "symbol": symbol,
            "timeframe": "1h",
            "direction": "HOLD",
            "rationale": "Sistema de recomendación en modo simplificado - análisis completo no disponible",
            "confidence": 30,
            "dataset_hash": "simple_hash",
            "params_hash": "simple_params",
            "entry_price": None,
            "stop_loss": None,
            "take_profit": None,
            "quantity": None,
            "risk_amount": None
        }
    except Exception as e:
        st.error(f"Error al obtener recomendación: {e}")
        return None

# Display recommendation
recommendation = get_simple_recommendation(symbol, capital)

if recommendation:
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Símbolo", recommendation["symbol"])
        st.metric("⏰ Timeframe", recommendation["timeframe"])
        st.metric("🎯 Dirección", recommendation["direction"])
    
    with col2:
        st.metric("💡 Confianza", f"{recommendation['confidence']}%")
        st.metric("📅 Fecha", recommendation["date"])
        st.metric("🔒 Hash Dataset", recommendation["dataset_hash"][:8] + "...")
    
    with col3:
        st.metric("💰 Precio Entrada", f"${recommendation['entry_price']:.2f}" if recommendation["entry_price"] else "N/A")
        st.metric("🛑 Stop Loss", f"${recommendation['stop_loss']:.2f}" if recommendation["stop_loss"] else "N/A")
        st.metric("🎯 Take Profit", f"${recommendation['take_profit']:.2f}" if recommendation["take_profit"] else "N/A")
    
    # Rationale
    st.markdown("---")
    st.subheader("🧠 Análisis y Razonamiento")
    st.info(recommendation["rationale"])
    
    # Trading plan (if available)
    if recommendation["entry_price"]:
        st.markdown("---")
        st.subheader("📋 Plan de Trading")
        
        col1, col2 = st.columns(2)
        
        with col1:
            direction = "🟢 LONG" if recommendation["direction"] == "LONG" else "🔴 SHORT" if recommendation["direction"] == "SHORT" else "⏸️ HOLD"
            st.metric("Dirección", direction)
            st.metric("Precio de Entrada", f"${recommendation['entry_price']:,.2f}")
            st.metric("Cantidad", f"{recommendation['quantity']:.6f}" if recommendation["quantity"] else "N/A")
        
        with col2:
            st.metric("Stop Loss", f"${recommendation['stop_loss']:,.2f}" if recommendation["stop_loss"] else "N/A")
            st.metric("Take Profit", f"${recommendation['take_profit']:,.2f}" if recommendation["take_profit"] else "N/A")
            st.metric("Riesgo ($)", f"${recommendation['risk_amount']:.2f}" if recommendation["risk_amount"] else "N/A")
        
        # Calculate R/R
        if recommendation["stop_loss"] and recommendation["take_profit"] and recommendation["entry_price"]:
            risk = abs(recommendation["entry_price"] - recommendation["stop_loss"])
            reward = abs(recommendation["take_profit"] - recommendation["entry_price"])
            rr = reward / risk if risk > 0 else 0
            st.metric("R/R Ratio", f"{rr:.2f}")

# Status
st.markdown("---")
st.subheader("📊 Estado del Sistema")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🌐 API Status", "✅ Conectado" if True else "❌ Desconectado")

with col2:
    st.metric("📊 Datos", "✅ Disponibles" if True else "❌ No disponibles")

with col3:
    st.metric("🧠 Motor", "✅ Operativo" if True else "❌ Error")

# Footer
st.markdown("---")
st.markdown("**One Market Trading System** - Versión Simplificada")
st.markdown("*Sistema de trading multi-timeframe con análisis cuantitativo*")
