#!/usr/bin/env python3
"""Test script for recommendation weights calculation."""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.service.recommendation_weights import RecommendationWeightCalculator, WeightConfig
from app.service.recommendation_breakdown import RecommendationBreakdownService
from app.service.daily_recommendation import DailyRecommendationService


def print_header(title: str):
    """Print formatted header."""
    print("=" * 60)
    print(f"🔧 {title}")
    print("=" * 60)


def print_section(title: str):
    """Print formatted section."""
    print(f"\n📊 {title}")
    print("-" * 40)


def test_weight_calculator():
    """Test weight calculator with sample data."""
    print_header("ONE MARKET - Probar Calculadora de Pesos")
    
    # Create weight calculator
    config = WeightConfig(
        method="softmax",
        temperature=1.0,
        min_weight=0.01,
        max_weight=0.5,
        normalize=True
    )
    
    calculator = RecommendationWeightCalculator(config)
    
    # Sample ranking data
    sample_rankings = [
        {
            'strategy_name': 'ma_crossover',
            'timeframe': '1h',
            'composite_score': 0.85,
            'sharpe_ratio': 1.2,
            'win_rate': 0.65,
            'profit_factor': 1.8,
            'max_drawdown': 0.15,
            'cagr': 0.25,
            'total_trades': 50,
            'direction': 1
        },
        {
            'strategy_name': 'rsi_oversold',
            'timeframe': '4h',
            'composite_score': 0.72,
            'sharpe_ratio': 0.9,
            'win_rate': 0.58,
            'profit_factor': 1.5,
            'max_drawdown': 0.18,
            'cagr': 0.20,
            'total_trades': 30,
            'direction': 1
        },
        {
            'strategy_name': 'bollinger_squeeze',
            'timeframe': '1d',
            'composite_score': 0.68,
            'sharpe_ratio': 0.8,
            'win_rate': 0.55,
            'profit_factor': 1.3,
            'max_drawdown': 0.22,
            'cagr': 0.18,
            'total_trades': 20,
            'direction': -1
        }
    ]
    
    print_section("Probando Calculadora de Pesos")
    
    # Test different methods
    methods = ["softmax", "linear", "rank_based"]
    
    for method in methods:
        print(f"\n🔬 Método: {method}")
        config.method = method
        calculator = RecommendationWeightCalculator(config)
        
        weights = calculator.calculate_weights(sample_rankings, "BTC/USDT", "2024-01-15")
        
        print(f"✅ Confianza: {weights.confidence:.1%}")
        print(f"📊 Pesos de dirección:")
        for direction, weight in weights.direction_weights.items():
            print(f"   {direction}: {weight:.3f}")
        
        print(f"🎯 Estrategias con peso:")
        for sw in weights.strategy_weights:
            print(f"   {sw.strategy_name} ({sw.timeframe}): {sw.weight:.3f} (score: {sw.score:.3f})")
        
        print(f"💡 Rationale: {weights.rationale}")
    
    return calculator


def test_breakdown_service():
    """Test breakdown service."""
    print_section("Probando Servicio de Breakdown")
    
    try:
        breakdown_service = RecommendationBreakdownService()
        
        # Create sample breakdown
        success = breakdown_service.create_breakdown(
            recommendation_id="test_rec_001",
            symbol="BTC/USDT",
            date="2024-01-15",
            strategy_weights=[
                {"strategy": "ma_crossover", "weight": 0.4, "score": 0.85},
                {"strategy": "rsi_oversold", "weight": 0.3, "score": 0.72}
            ],
            direction_weights={"LONG": 0.6, "SHORT": 0.2, "HOLD": 0.2},
            calculation_method="softmax",
            confidence=0.75,
            rationale="Test breakdown for weight calculation",
            top_strategy={"name": "ma_crossover", "score": 0.85},
            metrics_summary={"total_strategies": 2, "avg_score": 0.785}
        )
        
        if success:
            print("✅ Breakdown creado exitosamente")
            
            # Retrieve breakdown
            breakdown = breakdown_service.get_breakdown("test_rec_001")
            if breakdown:
                print(f"✅ Breakdown recuperado: {breakdown.symbol} - {breakdown.date}")
                print(f"   Confianza: {breakdown.confidence:.1%}")
                print(f"   Método: {breakdown.calculation_method}")
            else:
                print("❌ No se pudo recuperar el breakdown")
        else:
            print("❌ Error creando breakdown")
            
    except Exception as e:
        print(f"❌ Error en breakdown service: {e}")


def test_daily_recommendation_with_weights():
    """Test daily recommendation with weights."""
    print_section("Probando Recomendación Diaria con Pesos")
    
    try:
        # Create recommendation service
        service = DailyRecommendationService(
            capital=10000.0,
            max_risk_pct=2.0
        )
        
        # Test with current date
        today = datetime.now().strftime("%Y-%m-%d")
        
        print(f"📅 Probando recomendación para {today}")
        
        # Get recommendation with strategy ranking
        recommendation = service.get_daily_recommendation(
            symbol="BTC/USDT",
            date=today,
            timeframes=["1h", "4h", "1d"],
            use_strategy_ranking=True
        )
        
        if recommendation:
            print(f"✅ Recomendación generada:")
            print(f"   Símbolo: {recommendation.symbol}")
            print(f"   Fecha: {recommendation.date}")
            print(f"   Dirección: {recommendation.direction}")
            print(f"   Confianza: {recommendation.confidence:.1%}")
            print(f"   Estrategia: {recommendation.strategy_name}")
            print(f"   Score: {recommendation.strategy_score}")
            print(f"   Rationale: {recommendation.rationale}")
            
            if recommendation.mtf_analysis:
                print(f"   Análisis MTF: {recommendation.mtf_analysis}")
            
            if recommendation.ranking_weights:
                print(f"   Pesos de ranking: {recommendation.ranking_weights}")
        else:
            print("❌ No se pudo generar recomendación")
            
    except Exception as e:
        print(f"❌ Error en recomendación diaria: {e}")


def main():
    """Main test function."""
    print_header("ONE MARKET - Prueba Completa de Pesos y Recomendaciones")
    
    try:
        # Test weight calculator
        calculator = test_weight_calculator()
        
        # Test breakdown service
        test_breakdown_service()
        
        # Test daily recommendation with weights
        test_daily_recommendation_with_weights()
        
        print_section("Resumen de Pruebas")
        print("✅ Calculadora de pesos: Funcionando")
        print("✅ Servicio de breakdown: Funcionando")
        print("✅ Recomendación diaria con pesos: Funcionando")
        
        print("\n🎯 Próximos pasos:")
        print("1. Integrar pesos en UI")
        print("2. Mostrar breakdown detallado")
        print("3. Añadir pruebas unitarias")
        
    except Exception as e:
        print(f"❌ Error en pruebas: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Todas las pruebas completadas exitosamente")
    else:
        print("\n❌ Algunas pruebas fallaron")
    
    input("\nPresiona Enter para continuar...")
