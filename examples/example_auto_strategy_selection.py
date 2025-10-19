"""Example: Automatic Strategy Selection

This example demonstrates:
1. Running backtests on all strategies
2. Ranking them by performance
3. Getting the best strategy recommendation
4. Generating a concrete trade plan
"""
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.service.strategy_ranking import StrategyRankingService
from app.config.settings import get_risk_profile_for_capital, RISK_PROFILES


def main():
    print("="*70)
    print("  One Market - Automatic Strategy Selection Example")
    print("="*70)
    print()
    
    # Configuration
    symbol = "BTC-USDT"
    timeframe = "1h"
    capital = 1000.0  # $1K starter capital
    
    print(f"Symbol: {symbol}")
    print(f"Timeframe: {timeframe}")
    print(f"Capital: ${capital:,.2f}")
    print()
    
    # Get risk profile
    risk_profile = get_risk_profile_for_capital(capital)
    print(f"Risk Profile: {risk_profile.display_name}")
    print(f"  - {risk_profile.description}")
    print(f"  - Risk per trade: {risk_profile.default_risk_pct:.1%}")
    print(f"  - Min position: ${risk_profile.min_position_size_usd}")
    print()
    
    # Initialize service
    print("Inicializando servicio de ranking...")
    service = StrategyRankingService(
        capital=capital,
        max_risk_pct=risk_profile.max_risk_pct,
        lookback_days=90
    )
    print("✅ Servicio inicializado")
    print()
    
    # Get daily recommendation
    print("Ejecutando backtests y generando recomendación...")
    print("(Esto puede tardar 10-30 segundos)")
    print()
    
    recommendation = service.get_daily_recommendation(
        symbol=symbol,
        timeframe=timeframe,
        capital=capital,
        ranking_method="composite"
    )
    
    if recommendation is None:
        print("❌ No se pudo generar recomendación")
        print("Verifica que hay datos disponibles en storage/")
        return
    
    print("✅ Recomendación generada!")
    print("="*70)
    print()
    
    # Display recommendation
    print("🏆 MEJOR ESTRATEGIA DEL DÍA")
    print("-"*70)
    print(f"Estrategia: {recommendation.best_strategy_name}")
    print(f"Score: {recommendation.composite_score:.1f}/100")
    print(f"Rank: #{recommendation.rank}")
    print()
    
    print("📊 MÉTRICAS DE PERFORMANCE (Últimos 90 días)")
    print("-"*70)
    print(f"Sharpe Ratio: {recommendation.sharpe_ratio:.2f}")
    print(f"Win Rate: {recommendation.win_rate:.1%}")
    print(f"Max Drawdown: {abs(recommendation.max_drawdown):.1%}")
    print(f"Expectancy: ${recommendation.expectancy:.2f}")
    print()
    
    print(f"🎯 NIVEL DE CONFIANZA: {recommendation.confidence_level}")
    print(f"   {recommendation.confidence_description}")
    print()
    
    # Trade plan
    if recommendation.signal_direction != 0:
        print("💰 PLAN DE TRADE RECOMENDADO")
        print("-"*70)
        
        direction = "LONG 🟢" if recommendation.signal_direction == 1 else "SHORT 🔴"
        print(f"Dirección: {direction}")
        
        if recommendation.entry_price:
            print(f"Precio de Entrada: ${recommendation.entry_price:,.2f}")
        
        if recommendation.stop_loss:
            print(f"Stop Loss: ${recommendation.stop_loss:,.2f}")
        
        if recommendation.take_profit:
            print(f"Take Profit: ${recommendation.take_profit:,.2f}")
        
        if recommendation.quantity:
            print(f"Cantidad: {recommendation.quantity:.6f} units")
        
        if recommendation.risk_amount:
            print(f"Riesgo: ${recommendation.risk_amount:.2f} ({recommendation.risk_amount/capital:.1%})")
        
        if recommendation.stop_loss and recommendation.take_profit and recommendation.entry_price:
            risk = abs(recommendation.entry_price - recommendation.stop_loss)
            reward = abs(recommendation.take_profit - recommendation.entry_price)
            rr = reward / risk if risk > 0 else 0
            print(f"R/R Ratio: {rr:.2f}")
        
        print()
        
        # Execution guide
        print("📋 PASOS PARA EJECUTAR EN BINANCE")
        print("-"*70)
        print("1. Ir a Binance Spot > Buscar", symbol)
        print(f"2. Seleccionar orden {'LIMIT BUY' if recommendation.signal_direction == 1 else 'LIMIT SELL'}")
        print(f"3. Precio: ${recommendation.entry_price:,.2f}")
        print(f"4. Cantidad: {recommendation.quantity:.6f}")
        print(f"5. Configurar Stop Loss: ${recommendation.stop_loss:,.2f}" if recommendation.stop_loss else "")
        print(f"6. Configurar Take Profit: ${recommendation.take_profit:,.2f}" if recommendation.take_profit else "")
        print("7. Revisar y confirmar orden")
        print()
    
    else:
        print("⏸️ NO HAY TRADE RECOMENDADO HOY")
        print("La estrategia sugiere mantenerse al margen.")
        print()
    
    print("="*70)
    print()
    
    # Compare all strategies
    print("📊 COMPARACIÓN DE TODAS LAS ESTRATEGIAS")
    print("="*70)
    comparison_df = service.compare_strategies(symbol, timeframe)
    
    if not comparison_df.empty:
        # Format for console display
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.float_format', lambda x: f'{x:.2f}')
        
        print(comparison_df.to_string(index=False))
        print()
    
    print("="*70)
    print("✅ Ejemplo completado")
    print()
    print("💡 TIP: Ejecuta 'streamlit run ui/app_enhanced.py' para ver esto en interfaz visual")


if __name__ == "__main__":
    main()

