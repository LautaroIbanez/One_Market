#!/usr/bin/env python3
"""Test script for signal-based recommendation."""

from app.service.daily_recommendation import DailyRecommendationService

def test_signal_recommendation():
    """Test signal-based recommendation directly."""
    
    print("🔍 Test: Recomendación basada en señales")
    print("=" * 40)
    
    try:
        # Initialize service
        service = DailyRecommendationService()
        
        # Test parameters
        symbol = "BTC/USDT"
        date = "2024-01-15"
        timeframes = ["1h", "4h", "1d"]
        
        print(f"📊 Probando recomendación para {symbol} en {date}")
        
        # Call the method directly
        recommendation = service._get_signal_based_recommendation(symbol, date, timeframes)
        
        print(f"✅ Recomendación generada:")
        print(f"   🎯 Dirección: {recommendation.direction}")
        print(f"   💡 Confianza: {recommendation.confidence}")
        print(f"   💰 Precio entrada: {recommendation.entry_price}")
        print(f"   📝 Racional: {recommendation.rationale}")
        print(f"   🤖 Estrategia: {recommendation.strategy_name}")
        print(f"   ⭐ Score: {recommendation.strategy_score}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 40)

if __name__ == "__main__":
    test_signal_recommendation()
