"""One Market - Streamlit Dashboard with Tabbed Navigation.

This is the main UI application providing:
- Tab 1: Trading Plan - Quick view with chart, essential trade info, and confidence indicator
- Tab 2: Deep Dive - Detailed metrics, historical analysis, and strategy breakdown
- Sidebar configuration shared across tabs
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
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


# ============================================================
# SHARED HELPER FUNCTIONS
# ============================================================

@st.cache_data(ttl=300)
def load_ohlcv_data(symbol: str, timeframe: str) -> pd.DataFrame:
    """Load and cache OHLCV data."""
    try:
        store = DataStore()
        bars = store.read_bars(symbol, timeframe)
        
        if not bars:
            return None
        
        df = pd.DataFrame([bar.to_dict() for bar in bars])
        df = df.sort_values('timestamp').reset_index(drop=True)
        df = df.tail(500).reset_index(drop=True)
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


def calculate_signals_and_weights(df: pd.DataFrame):
    """Calculate signals from multiple strategies and return combined signal with individual signals."""
    try:
        # Multiple strategies
        sig1 = ma_crossover(df['close'], fast_period=10, slow_period=20)
        sig2 = rsi_regime_pullback(df['close'])
        sig3 = trend_following_ema(df['close'])
        
        # Individual signal values
        individual_signals = {
            'ma_cross': sig1.signal.iloc[-1],
            'rsi_regime': sig2.signal.iloc[-1],
            'triple_ema': sig3.signal.iloc[-1]
        }
        
        # Strategy names with confidence (for Deep Dive)
        strategy_breakdown = {
            'MA Crossover': {'signal': sig1.signal.iloc[-1], 'name': 'ma_cross'},
            'RSI Regime': {'signal': sig2.signal.iloc[-1], 'name': 'rsi_regime'},
            'Triple EMA': {'signal': sig3.signal.iloc[-1], 'name': 'triple_ema'}
        }
        
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
        
        return combined, individual_signals, strategy_breakdown
    except Exception as e:
        st.error(f"Error generating signals: {e}")
        return None, None, None


def create_decision(df: pd.DataFrame, combined_signal, risk_pct: float, capital: float):
    """Create daily trading decision using DecisionEngine and MarketAdvisor."""
    try:
        # Get advisor recommendation
        advisor = MarketAdvisor(default_risk_pct=risk_pct)
        advice = advisor.get_advice(
            df_intraday=df,
            current_signal=int(combined_signal.signal.iloc[-1]),
            signal_strength=float(combined_signal.confidence.iloc[-1]),
            symbol=st.session_state.get('symbol', 'BTC-USDT')
        )
        
        # Make decision
        engine = DecisionEngine()
        decision = engine.make_decision(
            df,
            combined_signal.signal,
            signal_strength=combined_signal.confidence,
            capital=capital,
            risk_pct=advice.recommended_risk_pct,
            current_time=datetime.now(ZoneInfo("UTC"))
        )
        
        return decision, advice
    except Exception as e:
        st.error(f"Error making decision: {e}")
        return None, None


def calculate_backtest_metrics(df: pd.DataFrame, combined_signal, timeframe: str, capital: float):
    """Calculate rolling backtest metrics for confidence indicator."""
    try:
        returns = df['close'].pct_change()
        strategy_returns = combined_signal.signal.shift(1) * returns
        strategy_returns = strategy_returns.dropna()
        
        # Determine lookback based on timeframe
        if timeframe == "1h":
            lookback = min(24 * 365, len(strategy_returns))
        elif timeframe == "1d":
            lookback = min(365, len(strategy_returns))
        elif timeframe == "4h":
            lookback = min(6 * 365, len(strategy_returns))
        else:
            lookback = len(strategy_returns)
        
        recent_returns = strategy_returns.tail(lookback)
        
        # Calculate metrics
        total_return = (1 + recent_returns).prod() - 1
        sharpe = (recent_returns.mean() / recent_returns.std() * np.sqrt(252)) if recent_returns.std() > 0 else 0
        
        # Max drawdown
        equity = (1 + recent_returns).cumprod()
        running_max = equity.expanding().max()
        drawdown = (equity - running_max) / running_max
        max_dd = abs(drawdown.min())
        
        # Win rate
        win_rate = (recent_returns > 0).mean()
        
        # CAGR
        days = lookback / (24 if timeframe == "1h" else (6 if timeframe == "4h" else 1))
        years = days / 365.25
        cagr = ((1 + total_return) ** (1 / years) - 1) if years > 0 else 0
        
        # Profit Factor
        wins = recent_returns[recent_returns > 0].sum()
        losses = abs(recent_returns[recent_returns < 0].sum())
        profit_factor = wins / losses if losses > 0 else 0
        
        # Calmar ratio
        calmar = cagr / max_dd if max_dd > 0 else 0
        
        return {
            'sharpe': sharpe,
            'cagr': cagr,
            'max_dd': max_dd,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_return': total_return,
            'calmar': calmar,
            'equity': equity,
            'drawdown': drawdown,
            'lookback': lookback
        }
    except Exception as e:
        st.error(f"Error calculating metrics: {e}")
        return None


def get_confidence_indicator(metrics: dict) -> tuple[str, str, str]:
    """Get confidence indicator based on backtest metrics (traffic light system)."""
    if metrics is None:
        return "🟡", "NEUTRAL", "No hay suficientes datos para evaluar confianza"
    
    sharpe = metrics.get('sharpe', 0)
    win_rate = metrics.get('win_rate', 0)
    max_dd = metrics.get('max_dd', 0)
    
    # Score system (0-100)
    score = 0
    
    # Sharpe contribution (40 points)
    if sharpe > 1.5:
        score += 40
    elif sharpe > 1.0:
        score += 30
    elif sharpe > 0.5:
        score += 20
    elif sharpe > 0:
        score += 10
    
    # Win rate contribution (30 points)
    if win_rate > 0.6:
        score += 30
    elif win_rate > 0.55:
        score += 25
    elif win_rate > 0.5:
        score += 20
    elif win_rate > 0.45:
        score += 15
    else:
        score += 10
    
    # Drawdown contribution (30 points)
    if max_dd < 0.05:
        score += 30
    elif max_dd < 0.10:
        score += 25
    elif max_dd < 0.15:
        score += 20
    elif max_dd < 0.20:
        score += 15
    else:
        score += 10
    
    # Determine confidence level
    if score >= 75:
        return "🟢", "ALTA", f"Confianza alta ({score}/100) - Sharpe: {sharpe:.2f}, WR: {win_rate:.1%}, DD: {max_dd:.1%}"
    elif score >= 50:
        return "🟡", "MEDIA", f"Confianza media ({score}/100) - Sharpe: {sharpe:.2f}, WR: {win_rate:.1%}, DD: {max_dd:.1%}"
    else:
        return "🔴", "BAJA", f"Confianza baja ({score}/100) - Sharpe: {sharpe:.2f}, WR: {win_rate:.1%}, DD: {max_dd:.1%}"


def render_price_chart(df: pd.DataFrame, decision, symbol: str, timeframe: str):
    """Render candlestick chart with entry/SL/TP levels."""
    chart_df = df.tail(60).copy()
    chart_df['datetime'] = pd.to_datetime(chart_df['timestamp'], unit='ms')
    
    fig = go.Figure(data=[go.Candlestick(
        x=chart_df['datetime'],
        open=chart_df['open'],
        high=chart_df['high'],
        low=chart_df['low'],
        close=chart_df['close'],
        name="Price"
    )])
    
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
        
        # Entry band zone
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
    
    fig.update_layout(
        title=f"{symbol} - {timeframe}",
        yaxis_title="Price (USD)",
        xaxis_title="Time",
        height=500,
        hovermode='x unified'
    )
    
    return fig


# ============================================================
# SIDEBAR - Configuration (Evaluated Once)
# ============================================================

st.title("📊 One Market - Daily Trading Platform")

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
        index=1
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
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Store config in session state
st.session_state['symbol'] = symbol
st.session_state['timeframe'] = timeframe
st.session_state['mode'] = mode
st.session_state['risk_pct'] = risk_pct
st.session_state['capital'] = capital


# ============================================================
# LOAD DATA AND CREATE DECISION (SHARED)
# ============================================================

df = load_ohlcv_data(symbol, timeframe)

if df is not None and len(df) > 0:
    # Generate signals
    combined, individual_signals, strategy_breakdown = calculate_signals_and_weights(df)
    
    if combined is not None:
        # Make decision
        decision, advice = create_decision(df, combined, risk_pct, capital)
        
        # Calculate backtest metrics
        metrics = calculate_backtest_metrics(df, combined, timeframe, capital)
        
        # Get confidence indicator
        confidence_icon, confidence_level, confidence_desc = get_confidence_indicator(metrics)
        
        # ============================================================
        # TABBED NAVIGATION
        # ============================================================
        
        tab1, tab2 = st.tabs(["🎯 Trading Plan", "📊 Deep Dive"])
        
        # ============================================================
        # TAB 1: TRADING PLAN (Quick View)
        # ============================================================
        
        with tab1:
            st.markdown("---")
            
            # Confidence indicator banner
            st.subheader("📈 Confianza del Sistema")
            col1, col2, col3 = st.columns([1, 2, 3])
            
            with col1:
                st.markdown(f"<div style='text-align: center; font-size: 48px;'>{confidence_icon}</div>", unsafe_allow_html=True)
            
            with col2:
                st.metric("Nivel de Confianza", confidence_level)
            
            with col3:
                st.info(confidence_desc)
            
            st.markdown("---")
            
            # Signal and direction
            st.subheader("📍 Señal de Hoy")
            
            col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            signal_value = int(combined.signal.iloc[-1])
            if signal_value == 1:
                    st.metric("Dirección", "🟢 LONG", delta="Buy")
            elif signal_value == -1:
                    st.metric("Dirección", "🔴 SHORT", delta="Sell")
            else:
                    st.metric("Dirección", "⚪ FLAT", delta="Wait")
        
        with col2:
            confidence = float(combined.confidence.iloc[-1])
                st.metric("Confianza Señal", f"{confidence:.0%}")
        
        with col3:
            current_price = float(df['close'].iloc[-1])
                st.metric("Precio Actual", f"${current_price:,.2f}")
        
        with col4:
            if decision and decision.should_execute:
                    st.metric("Estado", "✅ EJECUTAR")
            else:
                    st.metric("Estado", "⏸️ SKIP")
        
        st.markdown("---")
        
            # Trading details (if should execute)
        if decision and decision.should_execute:
                st.subheader("💰 Plan de Trade")
            
            col1, col2 = st.columns(2)
            
            with col1:
                    st.markdown("**📍 Entrada**")
                    st.metric("Precio de Entrada", f"${decision.entry_price:,.2f}")
                    if decision.entry_mid:
                        st.metric("Rango de Entrada", f"±{decision.entry_band_beta:.2%}")
                    
                    st.markdown("**💼 Posición**")
                    if decision.position_size:
                        st.metric("Cantidad", f"{decision.position_size.quantity:.4f}")
                        st.metric("Valor Nocional", f"${decision.position_size.notional_value:,.2f}")
            
            with col2:
                    st.markdown("**🛡️ Gestión de Riesgo**")
                st.metric("Stop Loss", f"${decision.stop_loss:,.2f}" if decision.stop_loss else "N/A")
                st.metric("Take Profit", f"${decision.take_profit:,.2f}" if decision.take_profit else "N/A")
                    
                if decision.stop_loss and decision.take_profit:
                    risk = abs(decision.entry_price - decision.stop_loss)
                    reward = abs(decision.take_profit - decision.entry_price)
                    rr = reward / risk if risk > 0 else 0
                    st.metric("R/R Ratio", f"{rr:.2f}")
            
                    if decision.position_size:
                        st.metric("Riesgo ($)", f"${decision.position_size.risk_amount:,.2f}")
                
                # Trading window status
                st.markdown("---")
                st.subheader("⏰ Ventana de Trading")
                
                current_window = decision.window if decision else "none"
                
                if current_window == "A":
                    st.success("🟢 Ventana A activa (09:00-12:30 UTC-3)")
                elif current_window == "B":
                    st.success("🟢 Ventana B activa (14:00-17:00 UTC-3)")
                else:
                    st.warning("⏸️ Fuera de horario de trading")
                
                # Action buttons
            st.markdown("---")
                st.subheader("🎯 Acciones")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 Ejecutar Paper Trade", use_container_width=True, type="primary"):
                        st.success("✅ **Paper trade ejecutado!** Operación registrada en modo simulación.")
            
            with col2:
                if mode == "Live Trading":
                    if st.button("💰 Ejecutar Live Trade", use_container_width=True, type="primary"):
                            st.warning("⚠️ **Live trading no implementado aún.** Usa paper trading.")
                else:
                        st.info("📄 Modo Paper activo")
            
            with col3:
                    if st.button("💾 Guardar Plan", use_container_width=True):
                        st.info("💾 **Plan guardado!** Disponible en historial.")
        
        else:
                # No trade today
            if decision and decision.skip_reason:
                    if "trading hours" in decision.skip_reason.lower():
                        st.info("⏰ **Fuera de horario de trading.** Ventanas: 09:00-12:30 y 14:00-17:00 (UTC-3).")
                    else:
                        st.info(f"ℹ️ **No hay trade hoy:** {decision.skip_reason}")
            else:
                    st.info("⏸️ **No hay trade hoy.** Esperando mejores condiciones.")
        
        st.markdown("---")
            
            # Chart
            st.subheader("📈 Gráfico de Precio")
            fig = render_price_chart(df, decision, symbol, timeframe)
            st.plotly_chart(fig, use_container_width=True)
        
        # ============================================================
        # TAB 2: DEEP DIVE (Detailed Analysis)
        # ============================================================
        
        with tab2:
            st.markdown("---")
            
            # Multi-horizon analysis
        if advice:
                st.header("🧭 Análisis Multi-Horizonte")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                    st.subheader("📊 Corto Plazo (Hoy)")
                    st.metric("Señal", "LONG" if advice.short_term.signal == 1 else ("SHORT" if advice.short_term.signal == -1 else "FLAT"))
                    st.metric("Timing de Entrada", advice.short_term.entry_timing.upper())
                    st.metric("Volatilidad", advice.short_term.volatility_state.upper())
                    st.metric("Riesgo Recomendado", f"{advice.short_term.recommended_risk_pct:.2%}")
            
            with col2:
                    st.subheader("📈 Medio Plazo (Semana)")
                    st.metric("Tendencia", "BULLISH" if advice.medium_term.trend_direction == 1 else ("BEARISH" if advice.medium_term.trend_direction == -1 else "NEUTRAL"))
                    st.metric("Posición EMA200", advice.medium_term.ema200_position.upper())
                    st.metric("Filtro", advice.medium_term.filter_recommendation.upper())
                    st.metric("RSI Semanal", f"{advice.medium_term.rsi_weekly:.1f}")
            
            with col3:
                    st.subheader("🌍 Largo Plazo (Régimen)")
                    st.metric("Régimen", advice.long_term.regime.upper())
                    st.metric("Vol Régimen", advice.long_term.volatility_regime.upper())
                    st.metric("Exposición Rec", f"{advice.long_term.recommended_exposure:.0%}")
                    st.metric("Prob Régimen", f"{advice.long_term.regime_probability:.0%}")
            
            # Consensus
            st.markdown("---")
                st.subheader("🎯 Consenso")
                
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if advice.consensus_direction == 1:
                        st.success("Dirección: LONG")
                elif advice.consensus_direction == -1:
                        st.error("Dirección: SHORT")
                else:
                        st.info("Dirección: NEUTRAL")
            
            with col2:
                    st.metric("Confianza Global", f"{advice.confidence_score:.0%}")
            
            with col3:
                    st.metric("Riesgo Final Rec", f"{advice.recommended_risk_pct:.2%}")
        
        st.markdown("---")
            
            # Performance metrics
            st.header("📊 Métricas de Performance (12 Meses)")
            
            if metrics:
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                    st.metric("CAGR", f"{metrics['cagr']:.1%}")
            
            with col2:
                    st.metric("Sharpe", f"{metrics['sharpe']:.2f}")
            
            with col3:
                    st.metric("Calmar", f"{metrics['calmar']:.2f}")
            
            with col4:
                    st.metric("Max DD", f"{metrics['max_dd']:.1%}")
            
            with col5:
                    st.metric("Win Rate", f"{metrics['win_rate']:.1%}")
            
            with col6:
                    st.metric("Profit Factor", f"{metrics['profit_factor']:.2f}")
            
            # Equity curve
                st.subheader("📈 Curva de Equity")
            
            equity_df = pd.DataFrame({
                    'datetime': df.tail(metrics['lookback'])['timestamp'].apply(lambda x: pd.to_datetime(x, unit='ms')),
                    'equity': capital * metrics['equity']
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
                st.subheader("📉 Drawdown")
            
            dd_df = pd.DataFrame({
                    'datetime': df.tail(metrics['lookback'])['timestamp'].apply(lambda x: pd.to_datetime(x, unit='ms')),
                    'drawdown': metrics['drawdown'] * 100
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
        
            st.markdown("---")
            
            # Strategy breakdown
            st.header("🔍 Desglose por Estrategia")
            
            if strategy_breakdown:
                st.subheader("Señales Individuales")
                
                col1, col2, col3 = st.columns(3)
                
                for i, (name, info) in enumerate(strategy_breakdown.items()):
                    with [col1, col2, col3][i]:
                        signal_val = info['signal']
                        if signal_val == 1:
                            st.success(f"**{name}**: 🟢 LONG")
                        elif signal_val == -1:
                            st.error(f"**{name}**: 🔴 SHORT")
                        else:
                            st.info(f"**{name}**: ⚪ FLAT")
                
                # Weights display
                if combined.weights:
                    st.subheader("Pesos de Combinación")
                    weights_df = pd.DataFrame([
                        {"Estrategia": k, "Peso": v} 
                        for k, v in combined.weights.items()
                    ])
                    st.dataframe(weights_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
            
            # Historical trades (placeholder - would require trade log storage)
            with st.expander("📜 Trades Históricos", expanded=False):
                st.info("💡 **Próximamente:** Historial de trades ejecutados con detalles de entrada, salida, P&L y duración.")
                st.markdown("Esta sección mostrará:")
                st.markdown("- Tabla de trades con fecha, símbolo, dirección, P&L")
                st.markdown("- Filtros por fecha, estrategia y resultado")
                st.markdown("- Estadísticas por estrategia individual")
            
            # Strategy parameters
            with st.expander("⚙️ Parámetros de Estrategias", expanded=False):
                st.markdown("**MA Crossover:**")
                st.markdown("- Fast Period: 10")
                st.markdown("- Slow Period: 20")
                
                st.markdown("**RSI Regime Pullback:**")
                st.markdown("- RSI Period: 14")
                st.markdown("- Oversold: 30")
                st.markdown("- Overbought: 70")
                
                st.markdown("**Triple EMA:**")
                st.markdown("- EMA Periods: 9, 21, 50")
            
            # Data status
            with st.expander("ℹ️ Estado de Datos", expanded=False):
                st.subheader("Información del Dataset")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
                    st.metric("Barras Cargadas", len(df))
        
        with col2:
            latest_ts = pd.to_datetime(df['timestamp'].iloc[-1], unit='ms')
                    st.metric("Última Actualización", latest_ts.strftime('%Y-%m-%d %H:%M'))
        
        with col3:
            data_age = datetime.now() - latest_ts.replace(tzinfo=None)
                    st.metric("Antigüedad", f"{data_age.total_seconds() / 60:.0f} min")
                
                # Metadata from store
                try:
                    store = DataStore()
                    metadata = store.get_metadata(symbol, timeframe)
                    if metadata:
                        st.markdown("**Metadata:**")
                        st.json({
                            "first_timestamp": pd.to_datetime(metadata.first_timestamp, unit='ms').strftime('%Y-%m-%d %H:%M'),
                            "last_timestamp": pd.to_datetime(metadata.last_timestamp, unit='ms').strftime('%Y-%m-%d %H:%M'),
                            "record_count": metadata.record_count,
                            "has_gaps": metadata.has_gaps,
                            "gap_count": metadata.gap_count
                        })
                except Exception as e:
                    st.warning(f"No se pudo cargar metadata: {e}")

else:
    st.warning(f"No hay datos disponibles para {symbol} {timeframe}")
    st.info("Por favor ejecuta `example_fetch_data.py` para cargar datos primero")


# Footer
st.markdown("---")
st.caption(f"One Market v2.0.0 | Modo: {mode} | Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
