"""One Market - Simplified Dashboard.

Simplified UI with:
- Grouped parameters in collapsible sections
- Tooltips with colloquial explanations
- Automatic mode with safe presets
- Advanced mode toggle for experienced users
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
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
from ui.texts import TOOLTIPS, PRESETS, SECTIONS, HELP_MESSAGES, STATUS_MESSAGES

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
# SIDEBAR - Simplified Configuration
# ============================================================

with st.sidebar:
    st.header("⚙️ Panel de Operación")
    
    # Mode selector
    st.subheader("🎯 Modo de Operación")
    modo_operacion = st.radio(
        "¿Cómo quieres operar?",
        options=["🤖 Automático", "⚙️ Personalizar"],
        index=0,
        help=HELP_MESSAGES["modo_automatico"]
    )
    
    st.markdown("---")
    
    if modo_operacion == "🤖 Automático":
        # Automatic mode - Presets
        st.subheader("📋 Preset Recomendado")
        
        preset_seleccionado = st.selectbox(
            "Elige tu perfil de riesgo:",
            options=list(PRESETS.keys()),
            format_func=lambda x: f"{PRESETS[x]['name']} - {PRESETS[x]['description']}",
            help=HELP_MESSAGES["preset_recomendado"]
        )
        
        preset = PRESETS[preset_seleccionado]
        
        # Display preset values (read-only)
        st.info(f"**Configuración {preset['name']}:**")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Riesgo por Trade", f"{preset['risk_pct']}%")
            st.metric("Ratio R/R", f"{preset['rr_target']}")
        with col2:
            st.metric("Método TP/SL", preset['tpsl_method'])
            st.metric("Timeframe", preset['timeframe'])
        
        # Apply preset values
        risk_pct = preset['risk_pct'] / 100
        rr_target = preset['rr_target']
        tpsl_method = preset['tpsl_method']
        atr_multiplier_sl = preset['atr_multiplier_sl']
        atr_multiplier_tp = preset['atr_multiplier_tp']
        timeframe = preset['timeframe']
        
        # Basic settings (user can still change these)
        st.markdown("---")
        st.subheader("🎯 Configuración Básica")
        
        available_symbols = settings.DEFAULT_SYMBOLS
        symbol = st.selectbox(
            "💰 Símbolo",
            options=available_symbols,
            index=0 if available_symbols else None,
            help=TOOLTIPS["timeframe"]["description"]
        )
        
        mode = st.radio(
            "📝 Modo de Trading",
            options=["📄 Paper Trading", "💰 Live Trading"],
            index=0,
            help="Paper = simulación, Live = operaciones reales"
        )
        
        capital = st.number_input(
            "💵 Capital ($)",
            min_value=1000.0,
            value=100000.0,
            step=1000.0,
            help=TOOLTIPS["capital"]["description"]
        )
        
        # Show current status
        if mode == "📄 Paper Trading":
            st.success(STATUS_MESSAGES["modo_paper"])
        else:
            st.warning(STATUS_MESSAGES["modo_live"])
    
    else:
        # Custom mode - Full control
        st.warning(HELP_MESSAGES["personalizar"])
        
        # Basic Configuration
        with st.expander(SECTIONS["basico"]["title"], expanded=True):
            st.markdown(f"*{SECTIONS['basico']['description']}*")
            
            available_symbols = settings.DEFAULT_SYMBOLS
            symbol = st.selectbox(
                "💰 Símbolo",
                options=available_symbols,
                index=0 if available_symbols else None,
                help=TOOLTIPS["timeframe"]["description"]
            )
            
            timeframe = st.selectbox(
                "⏰ Timeframe",
                options=["15m", "1h", "4h", "1d"],
                index=1,
                help=TOOLTIPS["timeframe"]["description"]
            )
            
            mode = st.radio(
                "📝 Modo de Trading",
                options=["📄 Paper Trading", "💰 Live Trading"],
                index=0
            )
            
            capital = st.number_input(
                "💵 Capital ($)",
                min_value=1000.0,
                value=100000.0,
                step=1000.0,
                help=TOOLTIPS["capital"]["description"]
            )
        
        # Risk Management
        with st.expander(SECTIONS["riesgo"]["title"], expanded=True):
            st.markdown(f"*{SECTIONS['riesgo']['description']}*")
            
            risk_pct = st.slider(
                "🛡️ Riesgo por Trade (%)",
                min_value=0.5,
                max_value=5.0,
                value=2.0,
                step=0.1,
                help=TOOLTIPS["risk_pct"]["description"]
            ) / 100
            
            rr_target = st.slider(
                "⚖️ Ratio Riesgo/Recompensa",
                min_value=1.0,
                max_value=5.0,
                value=1.5,
                step=0.1,
                help=TOOLTIPS["rr_target"]["description"]
            )
        
        # Advanced Configuration
        with st.expander(SECTIONS["avanzado"]["title"], expanded=False):
            st.markdown(f"*{SECTIONS['avanzado']['description']}*")
            
            tpsl_method = st.selectbox(
                "🎯 Método TP/SL",
                options=["ATR", "Swing", "Hybrid"],
                index=0,
                help=TOOLTIPS["tpsl_method"]["description"]
            )
            
            col1, col2 = st.columns(2)
            with col1:
                atr_multiplier_sl = st.number_input(
                    "🛑 ATR Multiplicador SL",
                    min_value=1.0,
                    max_value=5.0,
                    value=2.0,
                    step=0.1,
                    help=TOOLTIPS["atr_multiplier"]["description"]
                )
            
            with col2:
                atr_multiplier_tp = st.number_input(
                    "🎯 ATR Multiplicador TP",
                    min_value=1.0,
                    max_value=10.0,
                    value=3.0,
                    step=0.1,
                    help=TOOLTIPS["atr_multiplier"]["description"]
                )
    
    st.markdown("---")
    
    # Action button
    if modo_operacion == "🤖 Automático":
        refresh = st.button("🤖 Generar Decisión Automática", use_container_width=True, type="primary")
    else:
        refresh = st.button("⚙️ Generar Decisión Personalizada", use_container_width=True, type="primary")

# ============================================================
# MAIN AREA - Only execute when button is clicked
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
            current_signal=combined_signal.signal.iloc[-1],
            signal_strength=abs(combined_signal.signal.iloc[-1]),
            symbol=symbol
        )
        
        # Make decision
        decision_engine = DecisionEngine()
        decision = decision_engine.make_decision(
            df=df,
            signals=combined_signal.signal,
            signal_strength=combined_signal.confidence,
            signal_source="combined",
            capital=capital,
            risk_pct=risk_pct,
            current_time=datetime.now(ZoneInfo("UTC"))
        )
        
        return decision, advice
    
    except Exception as e:
        st.error(f"Error making decision: {e}")
        return None, None

# Only execute when button is clicked
if refresh:
    # Load data and generate signals
    df = load_data(symbol, timeframe)

    if df is not None:
        # Generate signals
        combined_signal, individual_signals = generate_current_signals(df)
        
        if combined_signal is not None:
            # Make decision
            decision, advice = make_decision(df, combined_signal)
            
            # Debug: Show decision details
            if decision:
                st.write(f"🔍 Debug - Skip reason: {decision.skip_reason}")
                st.write(f"🔍 Debug - Should execute: {decision.should_execute}")
                st.write(f"🔍 Debug - Window: {decision.window}")
                st.write(f"🔍 Debug - Signal: {decision.signal}")
            
            if decision is not None:
                # ============================================================
                # TODAY'S DECISION PANEL
                # ============================================================
                
                st.header("🎯 Decisión del Día")
                
                # Decision status
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    signal = decision.signal
                    if signal == 1:
                        st.metric("📈 Dirección", "LONG", delta="Comprar")
                    elif signal == -1:
                        st.metric("📉 Dirección", "SHORT", delta="Vender")
                    else:
                        st.metric("⏸️ Dirección", "FLAT", delta="Esperar")
                
                with col2:
                    confidence = decision.signal_strength * 100
                    st.metric("🎯 Confianza", f"{confidence:.1f}%")
                
                with col3:
                    if decision.entry_price:
                        st.metric("💰 Entrada", f"${decision.entry_price:.2f}")
                    else:
                        st.metric("💰 Entrada", "N/A")
                
                with col4:
                    status = "SKIP" if decision.skip_reason else "ACTIVO"
                    if status == "SKIP":
                        st.metric("⏸️ Estado", "SKIP")
                    else:
                        st.metric("✅ Estado", "ACTIVO")
                
                # Skip reason
                if decision.skip_reason:
                    if "trading hours" in decision.skip_reason.lower():
                        st.info(STATUS_MESSAGES["fuera_horario"])
                    else:
                        st.info(f"ℹ️ Razón: {decision.skip_reason}")
                
                # ============================================================
                # TRADING DETAILS
                # ============================================================
                
                if decision.entry_price and decision.stop_loss and decision.take_profit:
                    st.subheader("📊 Detalles de Trading")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("🛑 Stop Loss", f"${decision.stop_loss:.2f}")
                    
                    with col2:
                        st.metric("🎯 Take Profit", f"${decision.take_profit:.2f}")
                    
                    with col3:
                        rr_actual = (decision.take_profit - decision.entry_price) / (decision.entry_price - decision.stop_loss)
                        st.metric("⚖️ R/R Real", f"{rr_actual:.2f}")
                    
                    # Entry price
                    st.info(f"📏 **Precio de Entrada:** ${decision.entry_price:.2f}")
                    
                    # Position size
                    if decision.position_size:
                        st.success(f"💼 **Tamaño de Posición:** {decision.position_size.quantity:.4f} {symbol.split('/')[0]}")
                
                # ============================================================
                # STRATEGY BREAKDOWN
                # ============================================================
                
                st.subheader("🔍 Análisis de Estrategias")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    ma_signal = individual_signals['ma_cross']
                    if ma_signal > 0:
                        st.success("📈 MA Crossover: LONG")
                    elif ma_signal < 0:
                        st.error("📉 MA Crossover: SHORT")
                    else:
                        st.info("➖ MA Crossover: NEUTRAL")
                
                with col2:
                    rsi_signal = individual_signals['rsi_regime']
                    if rsi_signal > 0:
                        st.success("📈 RSI Regime: LONG")
                    elif rsi_signal < 0:
                        st.error("📉 RSI Regime: SHORT")
                    else:
                        st.info("➖ RSI Regime: NEUTRAL")
                
                with col3:
                    ema_signal = individual_signals['triple_ema']
                    if ema_signal > 0:
                        st.success("📈 Triple EMA: LONG")
                    elif ema_signal < 0:
                        st.error("📉 Triple EMA: SHORT")
                    else:
                        st.info("➖ Triple EMA: NEUTRAL")
                
                # ============================================================
                # MULTI-HORIZON ANALYSIS
                # ============================================================
                
                if advice:
                    st.subheader("🌍 Análisis Multi-Horizon")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**📊 Corto Plazo (Hoy)**")
                        st.write(f"⏰ Timing: {advice.short_term.entry_timing}")
                        st.write(f"📈 Volatilidad: {advice.short_term.volatility_state}")
                        st.write(f"🛡️ Riesgo Rec: {advice.short_term.recommended_risk_pct*100:.1f}%")
                    
                    with col2:
                        st.markdown("**📈 Mediano Plazo (Semana)**")
                        st.write(f"📊 EMA200: {advice.medium_term.ema200_position}")
                        st.write(f"🔍 Filtro: {advice.medium_term.filter_recommendation}")
                        st.write(f"📈 Tendencia: {advice.medium_term.trend_strength:.2f}")
                    
                    with col3:
                        st.markdown("**🌍 Largo Plazo (Régimen)**")
                        st.write(f"🌍 Régimen: {advice.long_term.regime.upper()}")
                        st.write(f"📊 Vol Regime: {advice.long_term.volatility_regime}")
                        st.write(f"📈 Exposición: {advice.long_term.recommended_exposure*100:.0f}%")
                
                # ============================================================
                # INTERACTIVE CHART
                # ============================================================
                
                st.subheader("📊 Gráfico Interactivo")
                
                # Create candlestick chart
                fig = go.Figure(data=go.Candlestick(
                    x=df['timestamp'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name=symbol
                ))
                
                # Add entry price line if available
                if decision.entry_price:
                    fig.add_hline(
                        y=decision.entry_price,
                        line_dash="dot",
                        line_color="blue",
                        annotation_text=f"Entry: ${decision.entry_price:.2f}"
                    )
                
                # Add SL/TP lines
                if decision.stop_loss:
                    fig.add_hline(
                        y=decision.stop_loss,
                        line_dash="dash",
                        line_color="red",
                        annotation_text=f"SL: ${decision.stop_loss:.2f}"
                    )
                
                if decision.take_profit:
                    fig.add_hline(
                        y=decision.take_profit,
                        line_dash="dash",
                        line_color="green",
                        annotation_text=f"TP: ${decision.take_profit:.2f}"
                    )
                
                fig.update_layout(
                    title=f"{symbol} - {timeframe}",
                    xaxis_title="Fecha",
                    yaxis_title="Precio (USDT)",
                    height=500,
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # ============================================================
                # PERFORMANCE METRICS
                # ============================================================
                
                st.subheader("📈 Métricas de Performance")
                
                # Mock performance data (in real app, this would come from backtest)
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                
                with col1:
                    st.metric("📈 CAGR", "24.5%", "2.1%")
                with col2:
                    st.metric("⚖️ Sharpe", "1.82", "0.15")
                with col3:
                    st.metric("📉 Max DD", "-18.3%", "1.2%")
                with col4:
                    st.metric("🎯 Win Rate", "56.2%", "2.1%")
                with col5:
                    st.metric("💰 Profit Factor", "1.95", "0.12")
                with col6:
                    st.metric("📊 Return", "24.5%", "2.1%")
                
                # ============================================================
                # EQUITY CURVE
                # ============================================================
                
                st.subheader("📈 Curva de Capital")
                
                # Mock equity curve
                dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
                equity = 100000 * (1 + np.random.randn(len(dates)) * 0.02).cumsum()
                
                fig_equity = go.Figure()
                fig_equity.add_trace(go.Scatter(
                    x=dates,
                    y=equity,
                    mode='lines',
                    name='Capital',
                    line=dict(color='blue', width=2)
                ))
                
                fig_equity.update_layout(
                    title="Evolución del Capital (12 meses)",
                    xaxis_title="Fecha",
                    yaxis_title="Capital ($)",
                    height=300
                )
                
                st.plotly_chart(fig_equity, use_container_width=True)
                
            else:
                st.error("❌ Error generando decisión")
        else:
            st.error("❌ Error generando señales")
    else:
        st.error("❌ Error cargando datos")

# Footer
st.markdown("---")
st.markdown("**One Market v1.0.0** | *Plataforma de Trading Cuantitativo*")
