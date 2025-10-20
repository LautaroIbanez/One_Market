"""Quick test script to verify all new features work.

This script tests:
1. DecisionTracker with historical data
2. Hypothetical plan calculation
3. Daily briefing generation
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.data.store import DataStore
from app.service.decision import DecisionEngine
from app.service.decision_tracker import get_tracker, get_performance_metrics
from app.service.daily_briefing import generate_daily_briefing
from app.research.signals import generate_signal
from app.research.combine import combine_signals


def test_decision_tracker():
    """Test 1: Verify DecisionTracker has historical data."""
    print("\n" + "="*60)
    print("TEST 1: DecisionTracker con Datos Históricos")
    print("="*60)
    
    try:
        tracker = get_tracker()
        metrics = get_performance_metrics(days=90)
        
        print(f"✅ DecisionTracker inicializado")
        print(f"   Total Decisiones: {metrics['total_decisions']}")
        print(f"   Ejecutadas: {metrics['executed_decisions']}")
        print(f"   Win Rate: {metrics['win_rate']:.1%}")
        print(f"   Total PnL: ${metrics['total_pnl']:,.2f}")
        print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"   Max Drawdown: {metrics['max_drawdown']:.2%}")
        
        if metrics['total_decisions'] > 0:
            print("\n✅ TEST 1 PASSED: DecisionTracker tiene datos históricos")
            return True
        else:
            print("\n⚠️  TEST 1 WARNING: DecisionTracker está vacío")
            print("   Ejecuta: python scripts/populate_decision_tracker.py --days 60")
            return False
    
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        return False


def test_hypothetical_plan():
    """Test 2: Verify hypothetical plan calculation works."""
    print("\n" + "="*60)
    print("TEST 2: Cálculo de Plan Hipotético")
    print("="*60)
    
    try:
        # Load data
        store = DataStore()
        bars = store.read_bars("BTC/USDT", "1h")
        
        if len(bars) < 100:
            print("❌ TEST 2 FAILED: Insufficient data")
            return False
        
        df = pd.DataFrame([bar.to_dict() for bar in bars])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        print(f"✅ Datos cargados: {len(df)} bars")
        
        # Calculate hypothetical plan
        engine = DecisionEngine()
        hypo_plan = engine.calculate_hypothetical_plan(
            df=df,
            signal=1,  # LONG
            signal_strength=0.75,
            capital=100000.0,
            risk_pct=0.02
        )
        
        if hypo_plan.get('has_plan'):
            print(f"✅ Plan hipotético calculado")
            print(f"   Dirección: {hypo_plan['side']}")
            print(f"   Entry: ${hypo_plan['entry_price']:,.2f}")
            print(f"   Stop Loss: ${hypo_plan['stop_loss']:,.2f}")
            print(f"   Take Profit: ${hypo_plan['take_profit']:,.2f}")
            print(f"   R/R Ratio: {hypo_plan['risk_reward_ratio']:.2f}")
            print(f"   Position Size: {hypo_plan['position_size']['quantity']:.4f}")
            print(f"   Risk Amount: ${hypo_plan['position_size']['risk_amount']:,.2f}")
            print("\n✅ TEST 2 PASSED: Plan hipotético funciona correctamente")
            return True
        else:
            print(f"\n❌ TEST 2 FAILED: {hypo_plan.get('reason', 'Unknown error')}")
            return False
    
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_daily_briefing():
    """Test 3: Verify daily briefing generation works."""
    print("\n" + "="*60)
    print("TEST 3: Generación de Briefing Diario")
    print("="*60)
    
    try:
        # Load data
        store = DataStore()
        bars = store.read_bars("BTC/USDT", "1h")
        
        if len(bars) < 100:
            print("❌ TEST 3 FAILED: Insufficient data")
            return False
        
        df = pd.DataFrame([bar.to_dict() for bar in bars])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        print(f"✅ Datos cargados: {len(df)} bars")
        
        # Generate briefing
        briefing = generate_daily_briefing(
            symbol="BTC/USDT",
            timeframe="1h",
            df=df,
            strategies=['ma_crossover', 'rsi_regime_pullback', 'macd_histogram_atr_filter'],
            combination_method='simple_average',
            capital=100000.0,
            risk_pct=0.02
        )
        
        print(f"✅ Briefing generado")
        print(f"   Símbolo: {briefing.symbol}")
        print(f"   Timeframe: {briefing.timeframe}")
        print(f"   Estado: {'EJECUTAR' if briefing.should_execute else 'SKIP'}")
        print(f"   Dirección: {briefing.signal_direction}")
        print(f"   Confianza: {briefing.signal_confidence:.1%}")
        print(f"   Volatilidad: {briefing.volatility_state.upper()}")
        
        if briefing.metrics:
            print(f"\n   Performance (30d):")
            print(f"   - Win Rate: {briefing.metrics.recent_win_rate:.1%}")
            print(f"   - Sharpe: {briefing.metrics.recent_sharpe:.2f}")
            print(f"   - Total PnL: ${briefing.metrics.recent_total_pnl:,.2f}")
            print(f"   - Trades: {briefing.metrics.executed_decisions}/{briefing.metrics.total_decisions}")
        
        if briefing.risk_warning:
            print(f"\n   ⚠️  Warning: {briefing.risk_warning}")
        
        # Test markdown export
        from app.service.daily_briefing import export_briefing_markdown
        markdown = export_briefing_markdown(briefing)
        
        if len(markdown) > 100:
            print(f"\n✅ Exportación Markdown: {len(markdown)} caracteres")
            print("\n✅ TEST 3 PASSED: Briefing diario funciona correctamente")
            return True
        else:
            print("\n❌ TEST 3 FAILED: Markdown export too short")
            return False
    
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🧪 ONE MARKET - PRUEBA RÁPIDA DE FUNCIONALIDADES")
    print("="*60)
    print("\nProbando las 3 mejoras implementadas:\n")
    print("1. DecisionTracker con datos históricos")
    print("2. Plan hipotético para decisiones SKIP")
    print("3. Briefing diario con recomendación operativa")
    
    results = []
    
    # Run tests
    results.append(("DecisionTracker", test_decision_tracker()))
    results.append(("Plan Hipotético", test_hypothetical_plan()))
    results.append(("Briefing Diario", test_daily_briefing()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{'='*60}")
    print(f"Resultado Final: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON! El sistema está listo.")
        print("\n📖 Para probar la UI completa, abre:")
        print("   http://localhost:8501")
        print("\n📋 Guía de pruebas completa en:")
        print("   GUIA_PRUEBAS_COMPLETA.md")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisa los errores arriba.")
        print("\n💡 Sugerencias:")
        print("   - Verifica que hay datos: python -m scripts.sync_data")
        print("   - Puebla el tracker: python scripts/populate_decision_tracker.py --days 60")
    
    print("="*60)
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

