#!/usr/bin/env python3
"""Debug script for current price retrieval."""

from app.service.daily_recommendation import DailyRecommendationService
from app.data import DataStore, DataFetcher
from datetime import datetime, timedelta

def debug_current_price():
    """Debug current price retrieval."""
    
    print("🔍 Debug: Obteniendo precio actual")
    print("=" * 40)
    
    try:
        # Initialize service
        service = DailyRecommendationService()
        
        # Test current price
        symbol = "BTC/USDT"
        print(f"📊 Probando precio para {symbol}")
        
        current_price = service._get_current_price(symbol)
        print(f"💰 Precio actual: {current_price}")
        
        # Test data store
        print("\n📊 Probando DataStore...")
        target_date = datetime.now()
        bars = service.store.read_bars(symbol, "1h", since=target_date - timedelta(hours=1), until=target_date)
        print(f"📈 Barras encontradas: {len(bars) if bars else 0}")
        
        if bars and len(bars) > 0:
            print(f"📊 Última barra: {bars[-1].close}")
        
        # Test data fetcher
        print("\n📊 Probando DataFetcher...")
        try:
            bars_fetched = service.fetcher.fetch_bars(symbol, "1h", limit=1)
            print(f"📈 Barras obtenidas: {len(bars_fetched) if bars_fetched else 0}")
            
            if bars_fetched and len(bars_fetched) > 0:
                print(f"📊 Última barra: {bars_fetched[-1].close}")
        except Exception as e:
            print(f"❌ Error en DataFetcher: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 40)

if __name__ == "__main__":
    debug_current_price()
