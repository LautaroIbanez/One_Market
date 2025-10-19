"""One Market - Enhanced UI with Strategy Selection and Trade History.

This version includes:
- Automatic strategy selection based on performance
- Trade history visualization
- Strategy comparison
- Risk profile selection
- Real vs simulated comparison
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
from app.service import DecisionEngine, MarketAdvisor, PaperTradingDB
from app.service.strategy_ranking import StrategyRankingService
from app.config.settings import settings, RISK_PROFILES, get_risk_profile_for_capital


# Page config
st.set_page_config(
    page_title="One Market Enhanced - Auto Strategy Selection",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# HELPER FUNCTIONS
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


@st.cache_data(ttl=600)
def get_best_strategy_recommendation(symbol: str, timeframe: str, capital: float):
    """Get best strategy recommendation for today."""
    try:
        service = StrategyRankingService(capital=capital, max_risk_pct=0.02, lookback_days=90)
        recommendation = service.get_daily_recommendation(
            symbol=symbol,
            timeframe=timeframe,
            capital=capital,
            ranking_method="composite"
        )
        return recommendation
    except Exception as e:
        st.error(f"Error getting recommendation: {e}")
        return None


@st.cache_data(ttl=600)
def compare_all_strategies(symbol: str, timeframe: str, capital: float):
    """Compare all strategies performance."""
    try:
        service = StrategyRankingService(capital=capital)
        comparison_df = service.compare_strategies(symbol, timeframe)
        return comparison_df
    except Exception as e:
        st.error(f"Error comparing strategies: {e}")
        return pd.DataFrame()


# ============================================================
# SIDEBAR - Configuration
# ============================================================

st.title("🏆 One Market Enhanced - Auto Strategy Selection")

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
    
    # Risk Profile Selection (NEW)
    st.subheader("💼 Risk Profile")
    
    profile_options = {
        "Automático (Basado en capital)": "auto",
        **{p.display_name: k for k, p in RISK_PROFILES.items()}
    }
    
    selected_profile_display = st.selectbox(
        "Perfil de Riesgo",
        options=list(profile_options.keys())
    )
    
    selected_profile_key = profile_options[selected_profile_display]
    
    # Capital input
    capital = st.number_input(
        "Capital ($)",
        min_value=500.0,
        value=1000.0,
        step=100.0
    )
    
    # Get profile based on selection
    if selected_profile_key == "auto":
        risk_profile = get_risk_profile_for_capital(capital)
        st.info(f"✨ Perfil auto-seleccionado: {risk_profile.display_name}")
    else:
        risk_profile = RISK_PROFILES[selected_profile_key]
    
    # Show profile details
    with st.expander("📋 Detalles del Perfil", expanded=False):
        st.markdown(f"**{risk_profile.description}**")
        st.markdown(f"- Riesgo por trade: {risk_profile.default_risk_pct:.1%}")
        st.markdown(f"- Comisión: {risk_profile.commission_pct:.2%}")
        st.markdown(f"- ATR SL: {risk_profile.default_atr_multiplier_sl:.1f}x")
        st.markdown(f"- ATR TP: {risk_profile.default_atr_multiplier_tp:.1f}x")
    
    st.markdown("---")
    
    # Refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ============================================================
# MAIN CONTENT - TABS
# ============================================================

tab1, tab2, tab3 = st.tabs([
    "🏆 Auto Strategy",
    "📊 Strategy Comparison",
    "📜 Trade History"
])

# ============================================================
# TAB 1: AUTO STRATEGY SELECTION
# ============================================================

with tab1:
    st.markdown("---")
    st.header("🏆 Best Strategy for Today")
    
    # Get recommendation
    recommendation = get_best_strategy_recommendation(symbol, timeframe, capital)
    
    if recommendation:
        # Display best strategy
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🥇 Mejor Estrategia", recommendation.best_strategy_name)
            st.metric("Score", f"{recommendation.composite_score:.1f}/100")
        
        with col2:
            st.metric("Sharpe Ratio", f"{recommendation.sharpe_ratio:.2f}")
            st.metric("Win Rate", f"{recommendation.win_rate:.1%}")
        
        with col3:
            st.metric("Max Drawdown", f"{abs(recommendation.max_drawdown):.1%}")
            st.metric("Expectancy", f"${recommendation.expectancy:.2f}")
        
        # Confidence indicator
        st.markdown("---")
        st.subheader("📊 Nivel de Confianza")
        
        if recommendation.confidence_level == "HIGH":
            st.success(f"🟢 {recommendation.confidence_description}")
        elif recommendation.confidence_level == "MEDIUM":
            st.warning(f"🟡 {recommendation.confidence_description}")
        else:
            st.error(f"🔴 {recommendation.confidence_description}")
        
        # Trade plan
        st.markdown("---")
        st.subheader("💰 Plan de Trade Recomendado")
        
        if recommendation.signal_direction != 0 and recommendation.entry_price:
            col1, col2 = st.columns(2)
            
            with col1:
                direction = "🟢 LONG" if recommendation.signal_direction == 1 else "🔴 SHORT"
                st.metric("Dirección", direction)
                st.metric("Precio de Entrada", f"${recommendation.entry_price:,.2f}")
                st.metric("Cantidad", f"{recommendation.quantity:.6f}" if recommendation.quantity else "N/A")
            
            with col2:
                st.metric("Stop Loss", f"${recommendation.stop_loss:,.2f}" if recommendation.stop_loss else "N/A")
                st.metric("Take Profit", f"${recommendation.take_profit:,.2f}" if recommendation.take_profit else "N/A")
                st.metric("Riesgo ($)", f"${recommendation.risk_amount:.2f}" if recommendation.risk_amount else "N/A")
            
            # Calculate R/R
            if recommendation.stop_loss and recommendation.take_profit:
                risk = abs(recommendation.entry_price - recommendation.stop_loss)
                reward = abs(recommendation.take_profit - recommendation.entry_price)
                rr = reward / risk if risk > 0 else 0
                st.metric("R/R Ratio", f"{rr:.2f}")
        else:
            st.info("⏸️ No hay trade recomendado hoy para esta estrategia")
    
    else:
        st.warning("⚠️ No se pudo generar recomendación. Verifica que hay datos disponibles.")


# ============================================================
# TAB 2: STRATEGY COMPARISON
# ============================================================

with tab2:
    st.markdown("---")
    st.header("📊 Comparación de Estrategias")
    
    comparison_df = compare_all_strategies(symbol, timeframe, capital)
    
    if not comparison_df.empty:
        # Summary metrics
        st.subheader("🎯 Resumen General")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            best_sharpe = comparison_df['Sharpe'].max()
            best_strat_sharpe = comparison_df.loc[comparison_df['Sharpe'].idxmax(), 'Strategy']
            st.metric("Mejor Sharpe", f"{best_sharpe:.2f}")
            st.caption(f"📌 {best_strat_sharpe}")
        
        with col2:
            best_wr = comparison_df['Win Rate'].max()
            best_strat_wr = comparison_df.loc[comparison_df['Win Rate'].idxmax(), 'Strategy']
            st.metric("Mejor Win Rate", f"{best_wr:.1%}")
            st.caption(f"📌 {best_strat_wr}")
        
        with col3:
            best_dd = comparison_df['Max DD'].max()  # Closest to 0
            best_strat_dd = comparison_df.loc[comparison_df['Max DD'].idxmax(), 'Strategy']
            st.metric("Menor Drawdown", f"{abs(best_dd):.1%}")
            st.caption(f"📌 {best_strat_dd}")
        
        with col4:
            best_pf = comparison_df['Profit Factor'].max()
            best_strat_pf = comparison_df.loc[comparison_df['Profit Factor'].idxmax(), 'Strategy']
            st.metric("Mejor PF", f"{best_pf:.2f}")
            st.caption(f"📌 {best_strat_pf}")
        
        st.markdown("---")
        
        # Detailed comparison table
        st.subheader("📋 Tabla Comparativa")
        
        # Format for display
        display_df = comparison_df.copy()
        display_df['Win Rate'] = display_df['Win Rate'].apply(lambda x: f"{x:.1%}")
        display_df['Max DD'] = display_df['Max DD'].apply(lambda x: f"{x:.1%}")
        display_df['CAGR'] = display_df['CAGR'].apply(lambda x: f"{x:.1%}")
        display_df['Sharpe'] = display_df['Sharpe'].apply(lambda x: f"{x:.2f}")
        display_df['Profit Factor'] = display_df['Profit Factor'].apply(lambda x: f"{x:.2f}")
        display_df['Expectancy'] = display_df['Expectancy'].apply(lambda x: f"${x:.2f}")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Download button
        csv = comparison_df.to_csv(index=False)
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name=f"strategy_comparison_{symbol}_{timeframe}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
        # Visualization
        st.markdown("---")
        st.subheader("📈 Visualización Comparativa")
        
        # Sharpe comparison chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=comparison_df['Strategy'],
            y=comparison_df['Sharpe'],
            name='Sharpe Ratio',
            marker_color='lightblue'
        ))
        
        fig.update_layout(
            title="Sharpe Ratio por Estrategia",
            yaxis_title="Sharpe Ratio",
            xaxis_title="Estrategia",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Win Rate comparison
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=comparison_df['Strategy'],
            y=comparison_df['Win Rate'] * 100,
            name='Win Rate (%)',
            marker_color='lightgreen'
        ))
        
        fig2.update_layout(
            title="Win Rate por Estrategia",
            yaxis_title="Win Rate (%)",
            xaxis_title="Estrategia",
            height=400
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    else:
        st.warning("No hay datos de comparación disponibles")


# ============================================================
# TAB 3: TRADE HISTORY
# ============================================================

with tab3:
    st.markdown("---")
    st.header("📜 Historial de Trades")
    
    # Load trade history from database
    try:
        db = PaperTradingDB()
        all_trades = db.get_all_trades(symbol=symbol)
        
        if all_trades:
            # Convert to DataFrame
            trades_data = []
            for trade in all_trades:
                trades_data.append({
                    'Fecha Entrada': datetime.fromisoformat(trade.entry_time).strftime('%Y-%m-%d %H:%M'),
                    'Fecha Salida': datetime.fromisoformat(trade.exit_time).strftime('%Y-%m-%d %H:%M') if trade.exit_time else "Abierto",
                    'Símbolo': trade.symbol,
                    'Lado': trade.side.upper(),
                    'Precio Entrada': trade.entry_price,
                    'Precio Salida': trade.exit_price if trade.exit_price else "-",
                    'Stop Loss': trade.stop_loss,
                    'Take Profit': trade.take_profit,
                    'Cantidad': trade.quantity,
                    'PnL ($)': trade.realized_pnl if trade.realized_pnl else 0,
                    'PnL (%)': trade.realized_pnl_pct if trade.realized_pnl_pct else 0,
                    'Estado': trade.status.upper(),
                    'Razón Salida': trade.exit_reason if trade.exit_reason else "-"
                })
            
            trades_df = pd.DataFrame(trades_data)
            
            # Summary stats
            st.subheader("📊 Estadísticas Generales")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Trades", len(trades_df))
            
            with col2:
                closed = trades_df[trades_df['Estado'] == 'CLOSED']
                wins = len(closed[closed['PnL ($)'] > 0])
                win_rate = wins / len(closed) if len(closed) > 0 else 0
                st.metric("Win Rate", f"{win_rate:.1%}")
            
            with col3:
                total_pnl = trades_df['PnL ($)'].sum()
                st.metric("PnL Total", f"${total_pnl:.2f}")
            
            with col4:
                avg_pnl = trades_df[trades_df['Estado'] == 'CLOSED']['PnL ($)'].mean()
                st.metric("PnL Promedio", f"${avg_pnl:.2f}" if not pd.isna(avg_pnl) else "$0.00")
            
            st.markdown("---")
            
            # Filters
            st.subheader("🔍 Filtros")
            
            col1, col2 = st.columns(2)
            
            with col1:
                status_filter = st.multiselect(
                    "Estado",
                    options=trades_df['Estado'].unique(),
                    default=list(trades_df['Estado'].unique())
                )
            
            with col2:
                side_filter = st.multiselect(
                    "Lado",
                    options=trades_df['Lado'].unique(),
                    default=list(trades_df['Lado'].unique())
                )
            
            # Apply filters
            filtered_df = trades_df[
                (trades_df['Estado'].isin(status_filter)) &
                (trades_df['Lado'].isin(side_filter))
            ]
            
            st.markdown("---")
            
            # Display table
            st.subheader("📋 Tabla de Trades")
            
            # Format for display
            display_df = filtered_df.copy()
            display_df['Precio Entrada'] = display_df['Precio Entrada'].apply(lambda x: f"${x:,.2f}")
            display_df['Precio Salida'] = display_df['Precio Salida'].apply(lambda x: f"${x:,.2f}" if x != "-" else "-")
            display_df['Stop Loss'] = display_df['Stop Loss'].apply(lambda x: f"${x:,.2f}")
            display_df['Take Profit'] = display_df['Take Profit'].apply(lambda x: f"${x:,.2f}")
            display_df['Cantidad'] = display_df['Cantidad'].apply(lambda x: f"{x:.6f}")
            display_df['PnL ($)'] = display_df['PnL ($)'].apply(lambda x: f"${x:.2f}")
            display_df['PnL (%)'] = display_df['PnL (%)'].apply(lambda x: f"{x:.2%}" if x != 0 else "0%")
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Download button
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Descargar Historial CSV",
                data=csv,
                file_name=f"trade_history_{symbol.replace('/', '-')}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
            # PnL Chart
            st.markdown("---")
            st.subheader("📈 P&L Acumulado")
            
            pnl_chart_df = filtered_df[filtered_df['Estado'] == 'CLOSED'].copy()
            if len(pnl_chart_df) > 0:
                pnl_chart_df = pnl_chart_df.sort_values('Fecha Entrada')
                pnl_chart_df['PnL Acumulado'] = pnl_chart_df['PnL ($)'].cumsum()
                
                fig_pnl = go.Figure()
                fig_pnl.add_trace(go.Scatter(
                    x=list(range(len(pnl_chart_df))),
                    y=pnl_chart_df['PnL Acumulado'],
                    mode='lines+markers',
                    name='PnL Acumulado',
                    line=dict(color='blue', width=2),
                    fill='tozeroy'
                ))
                
                fig_pnl.update_layout(
                    title="P&L Acumulado por Trade",
                    yaxis_title="P&L ($)",
                    xaxis_title="Número de Trade",
                    height=400
                )
                
                st.plotly_chart(fig_pnl, use_container_width=True)
            
            else:
                st.info("No hay trades cerrados para mostrar P&L acumulado")
        
        else:
            st.warning("No hay historial de trades disponible")
            st.info("Los trades aparecerán aquí una vez que ejecutes operaciones en Paper Trading")
    
    except Exception as e:
        st.error(f"Error al cargar trades: {e}")


# Footer
st.markdown("---")
st.caption(f"One Market Enhanced v2.0 | Perfil: {risk_profile.display_name} | Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

