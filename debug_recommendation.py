#!/usr/bin/env python3
"""Debug script for recommendation system."""

import requests
import json
from datetime import datetime

def debug_recommendation():
    """Debug the recommendation system."""
    
    print("🔍 ONE MARKET - Debug Sistema de Recomendaciones")
    print("=" * 50)
    
    # Test parameters
    symbol = "BTC/USDT"
    date = "2024-01-15"
    
    # API endpoint
    url = "http://localhost:8000/recommendation/daily"
    
    print(f"📊 Probando recomendación para {symbol} en {date}")
    print()
    
    try:
        # Make request without cache
        params = {
            "symbol": symbol,
            "date": date,
            "capital": 10000.0,
            "risk_percentage": 2.0
        }
        
        print("📤 Enviando solicitud...")
        response = requests.get(url, params=params, timeout=30)
        
        print(f"📥 Respuesta: HTTP {response.status_code}")
        
        if response.status_code == 200:
            recommendation = response.json()
            
            print("📋 RESPUESTA COMPLETA:")
            print(json.dumps(recommendation, indent=2, default=str))
            
        else:
            print(f"❌ Error HTTP {response.status_code}")
            print(f"📝 Detalle: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    print("=" * 50)

if __name__ == "__main__":
    debug_recommendation()
