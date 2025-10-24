"""
One Market - UI Simple Test
Simple UI to test if Streamlit works.
"""
import streamlit as st
import requests
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="One Market - Test",
    page_icon="📊",
    layout="wide"
)

st.title("🚀 One Market - Test UI")
st.write("Esta es una UI de prueba para verificar que Streamlit funciona.")

# Test API connection
st.header("🔍 Test de Conexión API")

if st.button("Probar API"):
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            st.success("✅ API conectada correctamente")
            st.json(response.json())
        else:
            st.error(f"❌ API error: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Error conectando API: {e}")

# Test recommendation
st.header("📊 Test de Recomendaciones")

if st.button("Obtener Recomendación"):
    try:
        response = requests.get(
            "http://localhost:8000/recommendation/daily",
            params={
                "symbol": "BTC/USDT",
                "date": datetime.now().strftime("%Y-%m-%d")
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            st.success("✅ Recomendación obtenida")
            
            # Access recommendation data from the correct nested structure
            recommendation = data.get("recommendation", {})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Dirección", recommendation.get("direction", "N/A"))
            with col2:
                st.metric("Confianza", f"{recommendation.get('confidence', 0)}%")
            with col3:
                st.metric("Precio Entrada", recommendation.get("entry_price", "N/A"))
            
            st.write("**Razonamiento:**", recommendation.get("rationale", "N/A"))
            
            # Show additional fields if available
            if recommendation.get("stop_loss"):
                st.metric("Stop Loss", f"${recommendation.get('stop_loss', 0):.2f}")
            if recommendation.get("take_profit"):
                st.metric("Take Profit", f"${recommendation.get('take_profit', 0):.2f}")
            if recommendation.get("strategy_name"):
                st.metric("Estrategia", recommendation.get("strategy_name"))
        else:
            st.error(f"❌ Error en recomendación: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Error obteniendo recomendación: {e}")

st.write("---")
st.write("Si ves este mensaje, Streamlit está funcionando correctamente.")


