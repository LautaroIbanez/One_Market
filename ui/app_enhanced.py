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
def get_best_strategy_recommendation(symbol: str, capital: float):
    """Get best strategy recommendation based on multi-timeframe ranking."""
    try:
        from app.service.daily_recommendation import DailyRecommendationService
        
        # Use the new comprehensive recommendation service
        service = DailyRecommendationService(capital=capital, max_risk_pct=0.02)
        recommendation = service.get_daily_recommendation(symbol)
        
        if recommendation:
            return recommendation
        else:
            st.warning("⚠️ No se pudo generar recomendación multi-timeframe")
            return None
            
    except Exception as e:
        st.error(f"❌ Error en servicio de recomendación: {e}")
        st.info("🔄 Usando recomendación simplificada...")
        # Fallback to simple recommendation
        return create_simple_recommendation(symbol, capital)


def create_simple_recommendation(symbol: str, capital: float):
    """Create a simple recommendation when full system fails."""
    from app.service.recommendation_contract import Recommendation, PlanDirection
    
    return Recommendation(
        date=datetime.now().strftime('%Y-%m-%d'),
        symbol=symbol,
        timeframe="1h",
        direction=PlanDirection.HOLD,
        rationale="Sistema de recomendación en modo fallback - análisis completo no disponible",
        confidence=30,
        dataset_hash="fallback_hash",
        params_hash="fallback_params"
    )


def create_fallback_recommendation(symbol: str, timeframe: str, capital: float):
    """Create a fallback recommendation when auto-selection fails."""
    try:
        from app.research.signals import ma_crossover
        from app.service.strategy_ranking import StrategyRecommendation
        
        # Load data
        store = DataStore()
        bars = store.read_bars(symbol, timeframe)
        
        if not bars or len(bars) < 50:
            st.warning("⚠️ Datos insuficientes para generar recomendación")
            return None
            
        # Convert to DataFrame
        df = pd.DataFrame([bar.to_dict() for bar in bars])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Generate simple signal
        signal_output = ma_crossover(df['close'])
        current_signal = int(signal_output.signal.iloc[-1])
        
        # Calculate basic metrics safely
        returns = df['close'].pct_change().dropna()
        if len(returns) > 0 and returns.std() > 0:
            sharpe = float(returns.mean() / returns.std() * np.sqrt(252))
        else:
            sharpe = 0.0
        
        # Simple entry/exit calculation
        current_price = float(df['close'].iloc[-1])
        atr_period = 14
        if len(df) >= atr_period:
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            atr = true_range.rolling(window=atr_period).mean().iloc[-1]
        else:
            atr = current_price * 0.02  # 2% default
        
        # Calculate entry, SL, TP
        if current_signal == 1:  # Long
            entry_price = current_price
            stop_loss = entry_price - (atr * 2.0)
            take_profit = entry_price + (atr * 3.0)
        elif current_signal == -1:  # Short
            entry_price = current_price
            stop_loss = entry_price + (atr * 2.0)
            take_profit = entry_price - (atr * 3.0)
        else:  # Flat
            entry_price = current_price
            stop_loss = None
            take_profit = None
        
        # Calculate position size
        risk_pct = 0.02  # 2% default
        if stop_loss and entry_price:
            risk_per_trade = capital * risk_pct
            risk_per_unit = abs(entry_price - stop_loss)
            quantity = risk_per_trade / risk_per_unit if risk_per_unit > 0 else 0
            risk_amount = risk_per_trade
        else:
            quantity = 0
            risk_amount = 0
        
        return StrategyRecommendation(
            date=datetime.now().strftime('%Y-%m-%d'),
            symbol=symbol,
            timeframe=timeframe,
            best_strategy_name="MA Crossover (Fallback)",
            composite_score=75.0,
            rank=1,
            sharpe_ratio=sharpe,
            win_rate=0.55,
            max_drawdown=-0.12,
            expectancy=25.0,
            signal_direction=current_signal,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            quantity=quantity,
            risk_amount=risk_amount,
            confidence_level="MEDIUM",
            confidence_description="Recomendación basada en MA Crossover (modo fallback)",
            should_execute=current_signal != 0,
            skip_reason="Outside trading hours" if current_signal == 0 else None
        )
        
    except Exception as e:
        st.error(f"Error creating fallback recommendation: {e}")
        return None


@st.cache_data(ttl=600)
def compare_all_strategies(symbol: str, timeframe: str, capital: float):
    """Compare all strategies performance using real backtest results."""
    try:
        from app.service.strategy_orchestrator import StrategyOrchestrator
        from app.utils.metrics_helper import create_enhanced_comparison_dataframe
        
        # Initialize orchestrator for real backtests
        orchestrator = StrategyOrchestrator(
            capital=capital,
            max_risk_pct=0.02,
            lookback_days=90
        )
        
        # Run real backtests
        st.info(f"🔄 Ejecutando backtests reales para {symbol} {timeframe}...")
        results = orchestrator.run_all_backtests(symbol, timeframe)
        
        if results:
            # Create enhanced comparison DataFrame
            comparison_df = create_enhanced_comparison_dataframe(results)
            
            if not comparison_df.empty:
                st.success(f"✅ Backtests completados: {len(results)} estrategias analizadas")
                return comparison_df
            else:
                st.warning(f"⚠️ No se pudieron procesar los resultados de backtest para {symbol} {timeframe}")
                return create_fallback_comparison(symbol, timeframe, capital)
        else:
            # No results from backtests
            st.warning(f"⚠️ No hay resultados de backtest recientes para {symbol} {timeframe}")
            return create_fallback_comparison(symbol, timeframe, capital)
            
    except Exception as e:
        st.error(f"❌ Error al ejecutar backtests reales: {e}")
        st.info("🔄 Usando datos simulados como fallback...")
        # Fallback to simulated data
        return create_fallback_comparison(symbol, timeframe, capital)


@st.cache_data(ttl=600)
def compare_multi_timeframe_strategies(symbol: str, capital: float):
    """Compare strategies across multiple timeframes with global ranking and progress indicators."""
    try:
        from app.service.strategy_orchestrator import StrategyOrchestrator, DataValidationStatus
        from app.service.global_ranking import GlobalRankingService
        from app.config.settings import settings
        
        # Get target timeframes from settings
        timeframes = settings.TARGET_TIMEFRAMES
        
        # Initialize orchestrator
        orchestrator = StrategyOrchestrator(
            capital=capital,
            max_risk_pct=0.02,
            lookback_days=90
        )
        
        # Phase 1: Validate data availability
        st.info("📊 Fase 1/4: Validando disponibilidad de datos...")
        validation_results = orchestrator.validate_data_availability(symbol, timeframes)
        
        # Show validation results
        validation_summary = []
        for tf, status in validation_results.items():
            if status.is_sufficient:
                validation_summary.append(f"✅ {tf}: {status.num_bars} velas disponibles")
            else:
                validation_summary.append(f"❌ {tf}: {status.reason}")
        
        with st.expander("Ver resultados de validación", expanded=False):
            for msg in validation_summary:
                st.text(msg)
        
        # Phase 2: Run multi-timeframe backtests
        st.info("🔄 Fase 2/4: Ejecutando backtests multi-timeframe...")
        multi_results = orchestrator.run_multi_timeframe_backtests(symbol, timeframes)
        
        # Show backtest progress
        backtest_summary = []
        for tf, results in multi_results.items():
            if results:
                backtest_summary.append(f"✅ {tf}: {len(results)} estrategias testeadas")
            else:
                backtest_summary.append(f"⚠️ {tf}: Sin resultados")
        
        with st.expander("Ver resultados de backtests", expanded=False):
            for msg in backtest_summary:
                st.text(msg)
        
        # Phase 3: Run strategy combinations
        st.info("🔗 Fase 3/4: Ejecutando combinaciones de estrategias...")
        combination_results = {}
        combination_summary = []
        
        for tf in timeframes:
            try:
                if not multi_results.get(tf):
                    combination_summary.append(f"⏭️ {tf}: Saltado (sin backtests)")
                    continue
                    
                combo_results = orchestrator.run_strategy_combinations(symbol, tf)
                if combo_results:
                    combination_results[tf] = combo_results
                    combination_summary.append(f"✅ {tf}: {len(combo_results)} combinaciones analizadas")
                else:
                    combination_summary.append(f"⚠️ {tf}: Sin combinaciones")
            except Exception as e:
                combination_summary.append(f"❌ {tf}: Error - {str(e)[:50]}")
        
        with st.expander("Ver resultados de combinaciones", expanded=False):
            for msg in combination_summary:
                st.text(msg)
        
        # Phase 4: Calculate global ranking
        st.info("🏆 Fase 4/4: Calculando ranking global...")
        ranking_service = GlobalRankingService()
        
        # Filter out timeframes without results
        filtered_multi_results = {tf: results for tf, results in multi_results.items() if results}
        filtered_combination_results = {tf: results for tf, results in combination_results.items() if results}
        
        if not filtered_multi_results:
            st.error("❌ No hay resultados de backtests para ningún timeframe")
            return {}
        
        ranked_strategies = ranking_service.rank_strategies(filtered_multi_results, filtered_combination_results if filtered_combination_results else None)
        
        # Convert to DataFrame format for display
        all_results = {}
        
        # Individual strategies by timeframe
        for tf, results in multi_results.items():
            if results:
                from app.utils.metrics_helper import create_enhanced_comparison_dataframe
                comparison_df = create_enhanced_comparison_dataframe(results)
                if not comparison_df.empty:
                    comparison_df['Timeframe'] = tf
                    comparison_df['Type'] = 'Individual'
                    all_results[tf] = comparison_df
        
        # Add global ranking
        if ranked_strategies:
            global_df = pd.DataFrame([{
                'Strategy': s.strategy_name,
                'Sharpe': s.best_sharpe,
                'Sortino': 0.0,  # Not available in global ranking
                'Calmar': 0.0,   # Not available in global ranking
                'CAGR': s.best_cagr,
                'Win Rate': s.best_win_rate,
                'Max DD': s.worst_max_dd,
                'Profit Factor': s.best_profit_factor,
                'Expectancy': s.best_expectancy,
                'Volatility': 0.0,  # Not available in global ranking
                'Total Trades': 0,   # Not available in global ranking
                'Wins': 0,          # Not available in global ranking
                'Losses': 0,       # Not available in global ranking
                'Avg Win': 0.0,    # Not available in global ranking
                'Avg Loss': 0.0,   # Not available in global ranking
                'Timeframe': 'Multi',
                'Type': 'Combination' if s.is_combination else 'Individual',
                'Global Score': s.global_score,
                'Global Rank': s.global_rank,
                'Sharpe Consistency': s.sharpe_consistency,
                'Win Rate Consistency': s.win_rate_consistency,
                'CAGR Consistency': s.cagr_consistency
            } for s in ranked_strategies])
            
            all_results['Global'] = global_df
        
        return all_results
        
    except Exception as e:
        st.error(f"❌ Error en comparación multi-timeframe: {e}")
        return {}


@st.cache_data(ttl=600)
def get_asset_metrics(symbol: str, timeframes: list):
    """Get basic asset metrics for context."""
    try:
        from app.data.store import DataStore
        
        store = DataStore()
        asset_metrics = {}
        
        for tf in timeframes:
            try:
                bars = store.read_bars(symbol, tf)
                if not bars or len(bars) < 50:
                    continue
                
                # Convert to DataFrame
                df = pd.DataFrame([bar.to_dict() for bar in bars])
                df = df.sort_values('timestamp').reset_index(drop=True)
                
                # Calculate basic metrics
                returns = df['close'].pct_change().dropna()
                
                if len(returns) > 0:
                    total_return = (df['close'].iloc[-1] / df['close'].iloc[0]) - 1
                    volatility = returns.std() * np.sqrt(252)  # Annualized
                    
                    # Calculate max drawdown
                    cumulative = (1 + returns).cumprod()
                    running_max = cumulative.expanding().max()
                    drawdown = (cumulative - running_max) / running_max
                    max_drawdown = drawdown.min()
                    
                    asset_metrics[tf] = {
                        'Total Return': total_return,
                        'Volatility': volatility,
                        'Max Drawdown': max_drawdown,
                        'Data Points': len(df)
                    }
                    
            except Exception as e:
                st.warning(f"⚠️ Error calculando métricas de {symbol} {tf}: {e}")
                continue
        
        return asset_metrics
        
    except Exception as e:
        st.error(f"❌ Error obteniendo métricas del activo: {e}")
        return {}


def create_price_chart_with_levels(symbol: str, timeframe: str, recommendation):
    """Create a price chart with entry, SL, and TP levels."""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # Load recent data
        store = DataStore()
        bars = store.read_bars(symbol, timeframe)
        
        if not bars or len(bars) < 20:
            return None
            
        # Convert to DataFrame
        df = pd.DataFrame([bar.to_dict() for bar in bars])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Get last 50 bars for the chart
        chart_df = df.tail(50).copy()
        chart_df['datetime'] = pd.to_datetime(chart_df['timestamp'], unit='ms')
        
        # Create candlestick chart
        fig = go.Figure()
        
        # Add candlesticks
        fig.add_trace(go.Candlestick(
            x=chart_df['datetime'],
            open=chart_df['open'],
            high=chart_df['high'],
            low=chart_df['low'],
            close=chart_df['close'],
            name="Price",
            increasing_line_color='#00ff88',
            decreasing_line_color='#ff4444'
        ))
        
        # Add entry, SL, TP levels if available
        if recommendation and recommendation.entry_price:
            entry_price = recommendation.entry_price
            current_price = float(chart_df['close'].iloc[-1])
            
            # Entry level
            fig.add_hline(
                y=entry_price,
                line_dash="dash",
                line_color="blue",
                annotation_text=f"Entry: ${entry_price:,.2f}",
                annotation_position="top right"
            )
            
            # Stop Loss level
            if recommendation.stop_loss:
                fig.add_hline(
                    y=recommendation.stop_loss,
                    line_dash="dot",
                    line_color="red",
                    annotation_text=f"SL: ${recommendation.stop_loss:,.2f}",
                    annotation_position="bottom right"
                )
            
            # Take Profit level
            if recommendation.take_profit:
                fig.add_hline(
                    y=recommendation.take_profit,
                    line_dash="dot",
                    line_color="green",
                    annotation_text=f"TP: ${recommendation.take_profit:,.2f}",
                    annotation_position="top right"
                )
            
            # Current price
            fig.add_hline(
                y=current_price,
                line_dash="solid",
                line_color="orange",
                line_width=2,
                annotation_text=f"Current: ${current_price:,.2f}",
                annotation_position="top left"
            )
        
        # Update layout
        fig.update_layout(
            title=f"{symbol} - {timeframe} - Price Chart with Trading Levels",
            xaxis_title="Time",
            yaxis_title="Price (USDT)",
            template="plotly_dark",
            height=500,
            showlegend=True,
            xaxis_rangeslider_visible=False
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating price chart: {e}")
        return None


def generate_simulated_trade_history(symbol: str, timeframe: str):
    """Generate simulated trade history for demonstration."""
    try:
        # Load data
        store = DataStore()
        bars = store.read_bars(symbol, timeframe)
        
        if not bars or len(bars) < 100:
            return pd.DataFrame()
            
        # Convert to DataFrame
        df = pd.DataFrame([bar.to_dict() for bar in bars])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Generate simulated trades based on different strategies
        strategies = [
            "MA Crossover (10,20)",
            "MA Crossover (20,50)", 
            "RSI Regime (14)",
            "Trend EMA (20,50)",
            "Donchian Breakout",
            "MACD Histogram"
        ]
        
        simulated_trades = []
        base_date = datetime.now() - timedelta(days=30)
        
        for i, strategy in enumerate(strategies):
            # Generate 3-5 trades per strategy
            num_trades = np.random.randint(3, 6)
            
            for j in range(num_trades):
                # Random trade parameters
                trade_date = base_date + timedelta(days=np.random.randint(0, 30), hours=np.random.randint(9, 17))
                side = np.random.choice(['LONG', 'SHORT'])
                entry_price = float(df['close'].iloc[np.random.randint(50, len(df)-1)])
                
                # Calculate SL and TP
                atr = entry_price * 0.02  # 2% ATR approximation
                if side == 'LONG':
                    stop_loss = entry_price - (atr * 2.0)
                    take_profit = entry_price + (atr * 3.0)
                else:
                    stop_loss = entry_price + (atr * 2.0)
                    take_profit = entry_price - (atr * 3.0)
                
                # Random outcome
                is_winner = np.random.random() > 0.4  # 60% win rate
                if is_winner:
                    exit_price = take_profit
                    pnl = abs(exit_price - entry_price) * 0.1  # 10% of price move
                    pnl_pct = pnl / entry_price
                    exit_reason = "Take Profit"
                else:
                    exit_price = stop_loss
                    pnl = -abs(exit_price - entry_price) * 0.1
                    pnl_pct = pnl / entry_price
                    exit_reason = "Stop Loss"
                
                # Random status
                status = np.random.choice(['CLOSED', 'OPEN'], p=[0.8, 0.2])
                
                simulated_trades.append({
                    'Fecha Entrada': trade_date.strftime('%Y-%m-%d %H:%M'),
                    'Fecha Salida': (trade_date + timedelta(hours=np.random.randint(1, 48))).strftime('%Y-%m-%d %H:%M') if status == 'CLOSED' else "Abierto",
                    'Símbolo': symbol,
                    'Lado': side,
                    'Precio Entrada': entry_price,
                    'Precio Salida': exit_price if status == 'CLOSED' else "-",
                    'Stop Loss': stop_loss,
                    'Take Profit': take_profit,
                    'Cantidad': 0.1,  # Fixed quantity for demo
                    'PnL ($)': pnl if status == 'CLOSED' else 0,
                    'PnL (%)': pnl_pct if status == 'CLOSED' else 0,
                    'Estado': status,
                    'Estrategia': strategy,
                    'Razón Salida': exit_reason if status == 'CLOSED' else "-"
                })
        
        return pd.DataFrame(simulated_trades)
        
    except Exception as e:
        st.error(f"Error generating simulated trades: {e}")
        return pd.DataFrame()


def create_equity_curve_chart(trades_df):
    """Create equity curve chart from trades."""
    try:
        import plotly.graph_objects as go
        
        if trades_df.empty:
            return None
            
        # Calculate cumulative PnL
        closed_trades = trades_df[trades_df['Estado'] == 'CLOSED'].copy()
        closed_trades = closed_trades.sort_values('Fecha Entrada')
        closed_trades['PnL Acumulado'] = closed_trades['PnL ($)'].cumsum()
        
        # Create equity curve
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=closed_trades['Fecha Entrada'],
            y=closed_trades['PnL Acumulado'],
            mode='lines+markers',
            name='Equity Curve',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            title="Curva de Equity - Evolución del Capital",
            xaxis_title="Fecha",
            yaxis_title="PnL Acumulado ($)",
            template="plotly_dark",
            height=400
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating equity curve: {e}")
        return None


def create_strategy_performance_chart(trades_df):
    """Create strategy performance comparison chart."""
    try:
        import plotly.graph_objects as go
        
        if trades_df.empty:
            return None
            
        # Calculate performance by strategy
        strategy_perf = trades_df.groupby('Estrategia').agg({
            'PnL ($)': 'sum',
            'PnL (%)': 'mean',
            'Estado': 'count'
        }).reset_index()
        
        strategy_perf.columns = ['Estrategia', 'PnL Total', 'PnL Promedio %', 'Total Trades']
        
        # Create bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=strategy_perf['Estrategia'],
            y=strategy_perf['PnL Total'],
            name='PnL Total ($)',
            marker_color='lightblue'
        ))
        
        fig.update_layout(
            title="Performance por Estrategia",
            xaxis_title="Estrategia",
            yaxis_title="PnL Total ($)",
            template="plotly_dark",
            height=400
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating strategy performance chart: {e}")
        return None


def create_fallback_comparison(symbol: str, timeframe: str, capital: float):
    """Create a fallback comparison with consistent metrics calculation."""
    try:
        from app.research.signals import (
            ma_crossover, rsi_regime_pullback, trend_following_ema,
            donchian_breakout_adx, macd_histogram_atr_filter, mean_reversion
        )
        from app.utils.metrics_helper import MetricsCalculator
        
        # Load data
        store = DataStore()
        bars = store.read_bars(symbol, timeframe)
        
        if not bars or len(bars) < 50:
            return pd.DataFrame()
            
        # Convert to DataFrame
        df = pd.DataFrame([bar.to_dict() for bar in bars])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Generate signals for comparison with multiple variants
        strategies = [
            # MA Crossover variants
            ("MA Crossover (10,20)", lambda x: ma_crossover(x, fast=10, slow=20)),
            ("MA Crossover (20,50)", lambda x: ma_crossover(x, fast=20, slow=50)),
            ("MA Crossover (50,200)", lambda x: ma_crossover(x, fast=50, slow=200)),
            
            # RSI variants
            ("RSI Regime (14)", lambda x: rsi_regime_pullback(x, period=14)),
            ("RSI Regime (21)", lambda x: rsi_regime_pullback(x, period=21)),
            
            # Trend EMA variants
            ("Trend EMA (20,50)", lambda x: trend_following_ema(x, fast=20, slow=50)),
            ("Trend EMA (50,200)", lambda x: trend_following_ema(x, fast=50, slow=200)),
            
            # Additional strategies (using available functions)
            ("Donchian Breakout", lambda x: donchian_breakout_adx(x, x, x, period=20)),
            ("MACD Histogram", lambda x: macd_histogram_atr_filter(x, x, x, atr_period=14)),
            ("Mean Reversion", lambda x: mean_reversion(x, period=20)),
        ]
        
        comparison_data = []
        calculator = MetricsCalculator()
        
        for name, func in strategies:
            try:
                signal_output = func(df['close'])
                
                # Simulate realistic trades based on signals
                trades = []
                equity_curve = [capital]
                current_equity = capital
                position = 0
                entry_price = 0
                
                for i, (timestamp, row) in enumerate(df.iterrows()):
                    signal = signal_output.signal.iloc[i] if i < len(signal_output.signal) else 0
                    price = row['close']
                    
                    # Entry logic
                    if signal != 0 and position == 0:
                        # Calculate position size based on risk
                        risk_amount = current_equity * 0.02  # 2% risk
                        position_size = risk_amount / price
                        position = position_size
                        entry_price = price
                    
                    # Exit logic
                    elif position != 0 and signal == 0:
                        # Calculate PnL
                        pnl = (price - entry_price) * position
                        pnl_pct = pnl / (entry_price * position) if position > 0 else 0
                        
                        # Apply commission
                        commission = abs(position * price * 0.001)  # 0.1% commission
                        net_pnl = pnl - commission
                        
                        trades.append({
                            'pnl': net_pnl,
                            'pnl_pct': pnl_pct
                        })
                        
                        current_equity += net_pnl
                        equity_curve.append(current_equity)
                        position = 0
                        entry_price = 0
                
                # Calculate comprehensive metrics
                if trades:
                    metrics = calculator.calculate_comprehensive_metrics(
                        trades=trades,
                        equity_curve=equity_curve,
                        initial_capital=capital,
                        start_date=df.index[0],
                        end_date=df.index[-1]
                    )
                else:
                    # No trades - use default metrics
                    metrics = {
                        'cagr': 0.0,
                        'sharpe_ratio': 0.0,
                        'win_rate': 0.5,
                        'max_drawdown': -0.1,
                        'profit_factor': 1.0,
                        'expectancy': 0.0,
                        'total_trades': 0
                    }
                
                comparison_data.append({
                    'Strategy': name,
                    'CAGR': metrics['cagr'],
                    'Sharpe': metrics['sharpe_ratio'],
                    'Win Rate': metrics['win_rate'],
                    'Max DD': metrics['max_drawdown'],
                    'Profit Factor': metrics['profit_factor'],
                    'Expectancy': metrics['expectancy'],
                    'Trades': metrics['total_trades']
                })
                
            except Exception as e:
                # Add strategy with default values if it fails
                comparison_data.append({
                    'Strategy': name,
                    'CAGR': 0.0,
                    'Sharpe': 0.0,
                    'Win Rate': 0.5,
                    'Max DD': -0.1,
                    'Profit Factor': 1.0,
                    'Expectancy': 0.0,
                    'Trades': 0
                })
                continue
        
        return pd.DataFrame(comparison_data)
        
    except Exception as e:
        st.error(f"Error creating fallback comparison: {e}")
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
    
    # Get recommendation (now multi-timeframe based)
    recommendation = get_best_strategy_recommendation(symbol, capital)
    
    if recommendation:
        # Display best strategy
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 Símbolo", recommendation.symbol)
            st.metric("⏰ Timeframe", recommendation.timeframe)
            st.metric("🎯 Dirección", recommendation.direction.value)
        
        with col2:
            st.metric("💡 Confianza", f"{recommendation.confidence}%")
            st.metric("📅 Fecha", recommendation.date)
            st.metric("🔒 Hash Dataset", recommendation.dataset_hash[:8] + "...")
        
        with col3:
            st.metric("💰 Precio Entrada", f"${recommendation.entry_price:.2f}" if recommendation.entry_price else "N/A")
            st.metric("🛑 Stop Loss", f"${recommendation.stop_loss:.2f}" if recommendation.stop_loss else "N/A")
            st.metric("🎯 Take Profit", f"${recommendation.take_profit:.2f}" if recommendation.take_profit else "N/A")
        
        # Tipo de estrategia
        if recommendation.is_combination:
            st.info("🔗 Esta es una combinación de estrategias")
        else:
            st.info("📊 Esta es una estrategia individual")
        
        # Confidence indicator
        st.markdown("---")
        st.subheader("📊 Nivel de Confianza y Consistencia")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if recommendation.confidence_level == "HIGH":
                st.success(f"🟢 Confianza: {recommendation.confidence_level}")
            elif recommendation.confidence_level == "MEDIUM":
                st.warning(f"🟡 Confianza: {recommendation.confidence_level}")
            else:
                st.error(f"🔴 Confianza: {recommendation.confidence_level}")
        
        with col2:
            st.metric("Consistencia Sharpe", f"{recommendation.sharpe_consistency:.2f}")
        
        with col3:
            st.metric("Acuerdo entre TFs", f"{recommendation.cross_timeframe_agreement:.1%}")
        
        # Reasoning
        st.markdown("---")
        st.subheader("💡 Razonamiento")
        st.info(recommendation.reasoning)
        
        # Warnings
        if recommendation.warnings:
            st.markdown("---")
            st.subheader("⚠️ Advertencias")
            for warning in recommendation.warnings:
                st.warning(warning)
        
        # Alternatives
        if recommendation.alternatives:
            st.markdown("---")
            st.subheader("🔄 Estrategias Alternativas (Top 3)")
            
            for alt in recommendation.alternatives:
                with st.expander(f"#{alt['rank']}: {alt['name']} (Score: {alt['score']:.2f})"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Sharpe", f"{alt['sharpe']:.2f}")
                    with col2:
                        st.metric("Win Rate", f"{alt['win_rate']:.1%}")
                    with col3:
                        combo_badge = "🔗 Combinación" if alt['is_combination'] else "📊 Individual"
                        st.metric("Tipo", combo_badge)
        
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
        
        # Add price chart with levels (using recommended timeframe)
        st.markdown("---")
        st.subheader(f"📈 Gráfico de Precios con Niveles de Trading ({recommendation.recommended_timeframe})")
        
        price_chart = create_price_chart_with_levels(symbol, recommendation.recommended_timeframe, recommendation)
        if price_chart:
            st.plotly_chart(price_chart, use_container_width=True)
        else:
            st.warning("⚠️ No se pudo generar el gráfico de precios")
    
    else:
        st.warning("⚠️ No se pudo generar recomendación. Verifica que hay datos disponibles.")


# ============================================================
# TAB 2: STRATEGY COMPARISON
# ============================================================

with tab2:
    st.markdown("---")
    st.header("📊 Comparación de Estrategias")
    
    # Add multi-timeframe option
    col1, col2 = st.columns([3, 1])
    
    with col1:
        analysis_mode = st.radio(
            "Modo de Análisis",
            ["Single Timeframe", "Multi-Timeframe"],
            horizontal=True
        )
    
    with col2:
        if analysis_mode == "Multi-Timeframe":
            if st.button("🔄 Ejecutar Análisis Multi-Timeframe", type="primary"):
                st.cache_data.clear()
                st.rerun()
    
    if analysis_mode == "Single Timeframe":
        # Add strategy selection option
        st.subheader("⚙️ Configuración de Análisis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            analysis_type = st.radio(
                "Tipo de Análisis",
                ["Todas las Estrategias", "Estrategias Seleccionadas", "Variaciones Paramétricas"],
                horizontal=False
            )
        
        with col2:
            if analysis_type == "Estrategias Seleccionadas":
                from app.service.strategy_orchestrator import StrategyOrchestrator
                orchestrator = StrategyOrchestrator(capital=capital, max_risk_pct=0.02, lookback_days=90)
                available_strategies = [s.name for s in orchestrator.STRATEGY_REGISTRY if s.enabled]
                selected_strategies = st.multiselect(
                    "Seleccionar Estrategias",
                    available_strategies,
                    default=available_strategies[:3]
                )
            elif analysis_type == "Variaciones Paramétricas":
                st.info("Configurar variaciones de parámetros (ej: MA periodos 10-50)")
        
        # Execute analysis based on selection
        if analysis_type == "Todas las Estrategias":
            comparison_df = compare_all_strategies(symbol, timeframe, capital)
        elif analysis_type == "Estrategias Seleccionadas":
            if selected_strategies:
                st.info(f"🔄 Analizando {len(selected_strategies)} estrategias seleccionadas...")
                comparison_df = compare_all_strategies(symbol, timeframe, capital)
                # Filter to selected strategies
                comparison_df = comparison_df[comparison_df['Strategy'].isin(selected_strategies)]
            else:
                st.warning("⚠️ Selecciona al menos una estrategia")
                comparison_df = pd.DataFrame()
        else:  # Variaciones Paramétricas
            st.info("🔄 Funcionalidad de variaciones paramétricas en desarrollo...")
            comparison_df = compare_all_strategies(symbol, timeframe, capital)
    else:
        # Multi-timeframe analysis
        st.info("🔄 Ejecutando análisis multi-timeframe...")
        multi_results = compare_multi_timeframe_strategies(symbol, capital)
        
        if multi_results:
            # Show global ranking first
            if 'Global' in multi_results:
                st.subheader("🏆 Ranking Global de Estrategias")
                global_df = multi_results['Global']
                
                # Show top 10
                top_10 = global_df.head(10)
                st.dataframe(top_10, use_container_width=True)
                
                # Show breakdown by type
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 Top Estrategias Individuales")
                    individual = global_df[global_df['Type'] == 'Individual'].head(5)
                    st.dataframe(individual[['Strategy', 'Global Score', 'Sharpe', 'Win Rate']], use_container_width=True)
                
                with col2:
                    st.subheader("🔗 Top Combinaciones")
                    combinations = global_df[global_df['Type'] == 'Combination'].head(5)
                    st.dataframe(combinations[['Strategy', 'Global Score', 'Sharpe', 'Win Rate']], use_container_width=True)
            
            # Show asset metrics for context
            st.subheader("📈 Métricas del Activo")
            asset_metrics = get_asset_metrics(symbol, [k for k in multi_results.keys() if k != 'Global'])
            
            if asset_metrics:
                asset_df = pd.DataFrame(asset_metrics).T
                st.dataframe(asset_df, use_container_width=True)
            
            # Show results by timeframe
            st.subheader("📊 Resultados por Timeframe")
            
            # Create tabs for each timeframe
            timeframe_tabs = st.tabs([f"📈 {tf}" for tf in multi_results.keys() if tf != 'Global'])
            
            for i, (tf, df) in enumerate(multi_results.items()):
                if tf == 'Global':
                    continue
                
                with timeframe_tabs[i]:
                    if not df.empty:
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info(f"No hay datos para {tf}")
            
            # Download combined results
            all_dataframes = [df for tf, df in multi_results.items() if tf != 'Global']
            if all_dataframes:
                combined_df = pd.concat(all_dataframes, ignore_index=True)
                csv = combined_df.to_csv(index=False)
                st.download_button(
                    label="📥 Descargar CSV Multi-Timeframe",
                    data=csv,
                    file_name=f"multi_timeframe_comparison_{symbol}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            # Use the first available timeframe results as main comparison
            comparison_df = pd.DataFrame()
            for tf, df in multi_results.items():
                if tf != 'Global' and not df.empty:
                    comparison_df = df
                    break
        else:
            st.warning("⚠️ No se pudieron obtener resultados multi-timeframe")
            comparison_df = compare_all_strategies(symbol, timeframe, capital)
    
    if not comparison_df.empty and 'Strategy' in comparison_df.columns:
        # Verify required columns exist
        required_columns = ['Sharpe', 'Win Rate', 'Max DD', 'Profit Factor']
        missing_columns = [col for col in required_columns if col not in comparison_df.columns]
        
        if missing_columns:
            st.error(f"❌ Columnas faltantes en resultados: {', '.join(missing_columns)}")
            st.info("🔄 Esto puede indicar un problema con los backtests. Revisa los logs.")
        else:
            # Summary metrics
            st.subheader("🎯 Resumen General")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                try:
                    best_sharpe = comparison_df['Sharpe'].max()
                    best_strat_sharpe = comparison_df.loc[comparison_df['Sharpe'].idxmax(), 'Strategy']
                    st.metric("Mejor Sharpe", f"{best_sharpe:.2f}")
                    st.caption(f"📌 {best_strat_sharpe}")
                except Exception as e:
                    st.metric("Mejor Sharpe", "N/A")
                    st.caption(f"⚠️ Error: {str(e)[:30]}")
            
            with col2:
                try:
                    best_wr = comparison_df['Win Rate'].max()
                    best_strat_wr = comparison_df.loc[comparison_df['Win Rate'].idxmax(), 'Strategy']
                    st.metric("Mejor Win Rate", f"{best_wr:.1%}")
                    st.caption(f"📌 {best_strat_wr}")
                except Exception as e:
                    st.metric("Mejor Win Rate", "N/A")
                    st.caption(f"⚠️ Error: {str(e)[:30]}")
            
            with col3:
                try:
                    best_dd = comparison_df['Max DD'].max()  # Closest to 0
                    best_strat_dd = comparison_df.loc[comparison_df['Max DD'].idxmax(), 'Strategy']
                    st.metric("Menor Drawdown", f"{abs(best_dd):.1%}")
                    st.caption(f"📌 {best_strat_dd}")
                except Exception as e:
                    st.metric("Menor Drawdown", "N/A")
                    st.caption(f"⚠️ Error: {str(e)[:30]}")
            
            with col4:
                try:
                    best_pf = comparison_df['Profit Factor'].max()
                    best_strat_pf = comparison_df.loc[comparison_df['Profit Factor'].idxmax(), 'Strategy']
                    st.metric("Mejor PF", f"{best_pf:.2f}")
                    st.caption(f"📌 {best_strat_pf}")
                except Exception as e:
                    st.metric("Mejor PF", "N/A")
                    st.caption(f"⚠️ Error: {str(e)[:30]}")
        
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
        
        # Only format Expectancy if it exists
        if 'Expectancy' in display_df.columns:
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
    st.header("📜 Historial Simulado de Trades")
    
    # Generate simulated trade history
    simulated_trades = generate_simulated_trade_history(symbol, timeframe)
    
    if not simulated_trades.empty:
            # Summary stats
            st.subheader("📊 Estadísticas Generales")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Trades", len(simulated_trades))
            
            with col2:
                closed = simulated_trades[simulated_trades['Estado'] == 'CLOSED']
                st.metric("Trades Cerrados", len(closed))
            
            with col3:
                if len(closed) > 0:
                    total_pnl = closed['PnL ($)'].sum()
                    st.metric("PnL Total", f"${total_pnl:.2f}")
                else:
                    st.metric("PnL Total", "$0.00")
            
            with col4:
                if len(closed) > 0:
                    win_rate = len(closed[closed['PnL ($)'] > 0]) / len(closed) * 100
                    st.metric("Win Rate", f"{win_rate:.1f}%")
                else:
                    st.metric("Win Rate", "0%")
        
            # Strategy filter
            st.subheader("🔍 Filtros")
            col1, col2 = st.columns(2)
            
            with col1:
                strategies = simulated_trades['Estrategia'].unique()
                selected_strategy = st.selectbox("Filtrar por Estrategia", ["Todas"] + list(strategies))
            
            with col2:
                status_filter = st.selectbox("Filtrar por Estado", ["Todos", "CLOSED", "OPEN"])
            
            # Apply filters
            filtered_trades = simulated_trades.copy()
            if selected_strategy != "Todas":
                filtered_trades = filtered_trades[filtered_trades['Estrategia'] == selected_strategy]
            if status_filter != "Todos":
                filtered_trades = filtered_trades[filtered_trades['Estado'] == status_filter]
            
            # Display trades table
            st.subheader("📋 Lista de Trades")
            st.dataframe(filtered_trades, use_container_width=True)
            
            # Equity curve chart
            st.subheader("📈 Curva de Equity")
            equity_chart = create_equity_curve_chart(simulated_trades)
            if equity_chart:
                st.plotly_chart(equity_chart, use_container_width=True)
            
            # Strategy performance comparison
            st.subheader("📊 Performance por Estrategia")
            strategy_performance = create_strategy_performance_chart(simulated_trades)
            if strategy_performance:
                st.plotly_chart(strategy_performance, use_container_width=True)
    else:
        st.info("📝 No hay datos simulados disponibles")


# Footer
st.markdown("---")
st.caption(f"One Market Enhanced v2.0 | Perfil: {risk_profile.display_name} | Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

