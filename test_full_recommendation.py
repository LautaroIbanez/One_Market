#!/usr/bin/env python3
"""Test script for full recommendation flow."""

from app.service.daily_recommendation import DailyRecommendationService
import traceback

def test_full_recommendation():
    """Test full recommendation flow."""
    
    print("🔍 Test: Flujo completo de recomendaciones")
    print("=" * 50)
    
    try:
        # Initialize service
        service = DailyRecommendationService()
        
        # Test parameters
        symbol = "BTC/USDT"
        date = "2024-01-15"
        
        print(f"📊 Probando recomendación completa para {symbol} en {date}")
        
        # Call the main method
        recommendation = service.get_daily_recommendation(symbol, date, use_strategy_ranking=False)
        
        print(f"✅ Recomendación generada:")
        print(f"   🎯 Dirección: {recommendation.direction}")
        print(f"   💡 Confianza: {recommendation.confidence}")
        print(f"   💰 Precio entrada: {recommendation.entry_price}")
        print(f"   📝 Racional: {recommendation.rationale}")
        print(f"   🤖 Estrategia: {recommendation.strategy_name}")
        print(f"   ⭐ Score: {recommendation.strategy_score}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_full_recommendation()
