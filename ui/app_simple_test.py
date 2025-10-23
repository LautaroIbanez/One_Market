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
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Dirección", data.get("direction", "N/A"))
            with col2:
                st.metric("Confianza", f"{data.get('confidence', 0)}%")
            with col3:
                st.metric("Precio Entrada", data.get("entry_price", "N/A"))
            
            st.write("**Razonamiento:**", data.get("rationale", "N/A"))
        else:
            st.error(f"❌ Error en recomendación: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Error obteniendo recomendación: {e}")

st.write("---")
st.write("Si ves este mensaje, Streamlit está funcionando correctamente.")

