"""Onboarding Guide - How to execute trades on Binance.

This module provides step-by-step guidance for users to execute recommended trades.
"""
import streamlit as st
from typing import Optional


def render_onboarding_guide(
    symbol: str,
    direction: int,  # 1 (long), -1 (short)
    entry_price: float,
    stop_loss: Optional[float],
    take_profit: Optional[float],
    quantity: float,
    risk_amount: float
):
    """Render complete onboarding guide for trade execution."""
    
    st.header("📚 Guía de Ejecución - Paso a Paso")
    st.markdown("---")
    
    # Step 1: Login to Binance
    with st.expander("🔐 Paso 1: Acceso a Binance", expanded=True):
        st.markdown("""
        ### Acceder a tu Cuenta
        
        1. **Ir a** [Binance.com](https://www.binance.com) o abrir la app móvil
        2. **Iniciar sesión** con tu email y contraseña
        3. **Completar 2FA** si está habilitado (recomendado)
        4. **Navegar a** la sección de **Spot Trading**
        
        ✅ **Verificación**: Deberías ver el panel de trading con el gráfico de precios
        """)
    
    # Step 2: Find the pair
    with st.expander("🔍 Paso 2: Buscar el Par de Trading", expanded=True):
        st.markdown(f"""
        ### Buscar {symbol}
        
        1. En la esquina superior izquierda, hacer click en el selector de par
        2. En el buscador, escribir: **{symbol.split('-')[0]}**
        3. Seleccionar el par **{symbol.replace('-', '/')}**
        4. Verificar que estás en el mercado **Spot** (no Futures)
        
        ✅ **Verificación**: El título debe mostrar {symbol.replace('-', '/')}
        """)
    
    # Step 3: Place order
    direction_str = "COMPRA (BUY)" if direction == 1 else "VENTA (SELL)"
    side_color = "🟢" if direction == 1 else "🔴"
    
    with st.expander(f"💰 Paso 3: Colocar Orden {direction_str}", expanded=True):
        st.markdown(f"""
        ### Configurar Orden Limit
        
        1. En el panel derecho, seleccionar tipo de orden: **Limit**
        2. Seleccionar lado: **{side_color} {direction_str}**
        3. **Precio**: Ingresar `{entry_price:,.2f}` USD
        4. **Cantidad**: Ingresar `{quantity:.6f}` {symbol.split('-')[0]}
        5. **Verificar** el valor total de la orden
        
        ⚠️ **IMPORTANTE**: Usar orden LIMIT, NO Market (para mejor precio)
        
        💡 **TIP**: Puedes ajustar el precio ±0.1% para mejorar probabilidad de ejecución
        """)
        
        # Show summary box
        st.info(f"""
        📋 **Resumen de la Orden**:
        - Par: {symbol}
        - Lado: {direction_str}
        - Precio: ${entry_price:,.2f}
        - Cantidad: {quantity:.6f}
        - Valor: ${entry_price * quantity:,.2f}
        """)
    
    # Step 4: Set Stop Loss
    if stop_loss:
        with st.expander("🛡️ Paso 4: Configurar Stop Loss", expanded=True):
            st.markdown(f"""
            ### Proteger tu Posición con SL
            
            **Opción A: Stop-Limit Order (Recomendado)**
            
            1. Después de que tu orden se ejecute, ir a "Órdenes Abiertas"
            2. Click en "Stop-Limit"
            3. **Stop Price**: `{stop_loss:,.2f}` USD
            4. **Limit Price**: `{stop_loss * 0.999 if direction == 1 else stop_loss * 1.001:,.2f}` USD
            5. **Cantidad**: `{quantity:.6f}` (misma cantidad que la posición)
            6. Confirmar orden
            
            **Opción B: OCO Order (One-Cancels-Other)**
            
            1. Al colocar la orden inicial, seleccionar "OCO"
            2. Configurar precio límite (TP) y stop (SL) simultáneamente
            3. Ambas órdenes se activan al ejecutarse la orden principal
            
            ⚠️ **Riesgo si no usas SL**: ${risk_amount:.2f} ({risk_amount:,.2f})
            
            ✅ **Beneficio**: Limita pérdidas automáticamente
            """)
    
    # Step 5: Set Take Profit
    if take_profit:
        with st.expander("🎯 Paso 5: Configurar Take Profit", expanded=True):
            profit_potential = abs(take_profit - entry_price) * quantity
            st.markdown(f"""
            ### Asegurar Ganancias con TP
            
            **Opción A: Limit Sell/Buy Order**
            
            1. Crear una orden Limit {'SELL' if direction == 1 else 'BUY'}
            2. **Precio**: `{take_profit:,.2f}` USD
            3. **Cantidad**: `{quantity:.6f}` (toda la posición)
            4. Tipo: "Post Only" (opcional, para mejor fee)
            5. Confirmar orden
            
            **Opción B: Usar OCO con Stop Loss**
            
            Si usaste OCO en el paso 4, el TP ya está configurado.
            
            💰 **Ganancia Potencial**: ${profit_potential:.2f}
            
            ✅ **Beneficio**: Toma ganancias automáticamente
            """)
    
    # Step 6: Monitor
    with st.expander("👁️ Paso 6: Monitoreo y Seguimiento", expanded=False):
        st.markdown("""
        ### Monitorear tu Posición
        
        **Durante el día**:
        1. Revisar el gráfico cada 2-4 horas
        2. Verificar que SL y TP siguen activos en "Órdenes Abiertas"
        3. NO modificar los niveles a menos que sea absolutamente necesario
        
        **Fin del día**:
        1. Si la posición sigue abierta al cierre de mercado, evaluar:
           - Mantener overnight (riesgo de gap)
           - Cerrar manualmente
        2. Registrar el resultado en tu journal de trading
        
        **Cierre de Posición**:
        1. Automático: Se ejecuta SL o TP
        2. Manual: Click en la posición > "Cerrar Posición"
        
        📊 **Dashboard Binance**: Puedes ver tu P&L en tiempo real en "Portafolio" > "Spot"
        """)
    
    # Step 7: Record results
    with st.expander("📝 Paso 7: Registrar Resultados (Opcional)", expanded=False):
        st.markdown("""
        ### Llevar un Journal de Trading
        
        Después de cada trade, registra:
        
        **Datos Básicos**:
        - Fecha y hora de entrada/salida
        - Precio de entrada/salida
        - P&L realizado
        
        **Análisis**:
        - ¿La estrategia funcionó como esperabas?
        - ¿Respetaste el SL y TP?
        - ¿Qué mejorarías?
        
        **Tools recomendadas**:
        - Google Sheets / Excel
        - TradingView (con notas en el gráfico)
        - Notion / Obsidian
        
        💡 **Beneficio**: Aprendes de tus trades y mejoras continuamente
        """)
    
    # Safety checklist
    st.markdown("---")
    st.subheader("✅ Checklist de Seguridad")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Antes de Ejecutar**:
        - [ ] Verificar precio actual del mercado
        - [ ] Confirmar que es el par correcto
        - [ ] Revisar saldo disponible
        - [ ] Calcular el riesgo en $
        - [ ] Preparar SL y TP
        """)
    
    with col2:
        st.markdown("""
        **Después de Ejecutar**:
        - [ ] Verificar que la orden se ejecutó
        - [ ] Confirmar que SL está activo
        - [ ] Confirmar que TP está activo
        - [ ] Tomar screenshot (opcional)
        - [ ] Configurar alertas de precio
        """)


def render_quick_execution_summary(
    symbol: str,
    direction: int,
    entry_price: float,
    stop_loss: Optional[float],
    take_profit: Optional[float],
    quantity: float
):
    """Render a quick summary for experienced traders."""
    
    st.subheader("⚡ Resumen Rápido (Para Traders Experimentados)")
    
    direction_str = "BUY" if direction == 1 else "SELL"
    
    code = f"""
# Binance Spot {direction_str}
Pair: {symbol}
Type: LIMIT
Price: ${entry_price:,.2f}
Quantity: {quantity:.6f}
Stop Loss: ${stop_loss:,.2f if stop_loss else 'N/A'}
Take Profit: ${take_profit:,.2f if take_profit else 'N/A'}
"""
    
    st.code(code, language="python")
    
    # Copy to clipboard button
    st.markdown("💡 **TIP**: Copia estos valores y úsalos en Binance")


def render_binance_fees_calculator(
    entry_price: float,
    quantity: float,
    commission_pct: float = 0.001
):
    """Render fees calculator."""
    
    with st.expander("💸 Calculadora de Comisiones Binance", expanded=False):
        st.markdown("### Estimación de Fees")
        
        notional = entry_price * quantity
        maker_fee = notional * commission_pct
        taker_fee = notional * commission_pct
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Valor Nocional", f"${notional:,.2f}")
        
        with col2:
            st.metric("Maker Fee (0.1%)", f"${maker_fee:.2f}")
        
        with col3:
            st.metric("Taker Fee (0.1%)", f"${taker_fee:.2f}")
        
        st.info(f"""
        💡 **Tips para reducir fees**:
        - Usar órdenes LIMIT (maker) en vez de MARKET (taker)
        - Holdear BNB para descuento del 25%
        - Alcanzar VIP levels con mayor volumen
        """)

