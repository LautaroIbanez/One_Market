#!/usr/bin/env python3
"""Test with detailed logging."""

import logging
logging.basicConfig(level=logging.DEBUG)

from app.service.daily_recommendation import DailyRecommendationService

def test_with_logging():
    """Test with detailed logging."""
    
    print("🔍 Test: Con logging detallado")
    print("=" * 40)
    
    try:
        service = DailyRecommendationService()
        recommendation = service.get_daily_recommendation("BTC/USDT", "2024-01-15", use_strategy_ranking=False)
        
        print(f"\n✅ Resultado:")
        print(f"   Dirección: {recommendation.direction}")
        print(f"   Confianza: {recommendation.confidence}")
        print(f"   Racional: {recommendation.rationale}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 40)

if __name__ == "__main__":
    test_with_logging()
