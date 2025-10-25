#!/usr/bin/env python3
"""Test final de recomendaciones."""

import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_recommendations():
    """Test the recommendation system."""
    print("🔍 ONE MARKET - Test Final de Recomendaciones")
    print("=" * 50)
    
    try:
        from app.service.daily_recommendation import DailyRecommendationService
        
        print("🔍 Creando servicio de recomendaciones...")
        service = DailyRecommendationService(capital=10000.0, max_risk_pct=2.0)
        print("✅ Servicio creado")
        
        print("🔍 Generando recomendación...")
        date = datetime.now().strftime('%Y-%m-%d')
        recommendation = service._get_signal_based_recommendation('BTC/USDT', date, ['1h', '4h', '1d'])
        
        print("📊 RESULTADO:")
        print(f"   - Dirección: {recommendation.direction}")
        print(f"   - Confianza: {recommendation.confidence}%")
        print(f"   - Precio Entrada: {recommendation.entry_price}")
        print(f"   - Razonamiento: {recommendation.rationale}")
        
        if recommendation.direction.value != 'HOLD' and recommendation.confidence > 0:
            print("🎉 ¡Recomendación generada correctamente!")
            return True
        else:
            print("❌ Recomendación sigue siendo HOLD")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_recommendations()
    print("\n" + "=" * 50)
    print(f"📊 RESULTADO FINAL: {'✅ ÉXITO' if success else '❌ FALLO'}")
    input("\nPresiona Enter para continuar...")



