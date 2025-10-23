#!/usr/bin/env python3
"""Test script for complete recommendation system."""

import requests
import json
from datetime import datetime

def test_recommendation_system():
    """Test the complete recommendation system."""
    
    print("🔬 ONE MARKET - Probando Sistema de Recomendaciones Completo")
    print("=" * 60)
    
    # Test parameters
    symbol = "BTC/USDT"
    date = "2024-01-15"  # Use a specific date
    
    # API endpoint
    url = "http://localhost:8000/recommendation/daily"
    
    print(f"📊 Probando recomendación para {symbol} en {date}")
    print(f"🌐 URL: {url}")
    print()
    
    try:
        # Make request
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
            
            print("✅ Recomendación generada exitosamente!")
            print()
            
            # Display basic information
            print("📋 INFORMACIÓN BÁSICA:")
            print(f"   📅 Fecha: {recommendation.get('date', 'N/A')}")
            print(f"   📊 Símbolo: {recommendation.get('symbol', 'N/A')}")
            print(f"   ⏰ Timeframe: {recommendation.get('timeframe', 'N/A')}")
            print(f"   🎯 Dirección: {recommendation.get('direction', 'N/A')}")
            print(f"   💡 Confianza: {recommendation.get('confidence', 0)}%")
            print()
            
            # Display strategy information
            strategy_name = recommendation.get('strategy_name')
            if strategy_name:
                print("🤖 INFORMACIÓN DE ESTRATEGIA:")
                print(f"   📝 Estrategia: {strategy_name}")
                print(f"   ⭐ Score: {recommendation.get('strategy_score', 'N/A')}")
                print(f"   📈 Sharpe Ratio: {recommendation.get('sharpe_ratio', 'N/A')}")
                print(f"   🎯 Win Rate: {recommendation.get('win_rate', 'N/A')}")
                print(f"   📉 Max Drawdown: {recommendation.get('max_drawdown', 'N/A')}")
                print()
            
            # Display trading plan
            entry_price = recommendation.get('entry_price')
            if entry_price:
                print("💰 PLAN DE TRADING:")
                print(f"   💵 Precio de entrada: ${entry_price:.2f}")
                print(f"   🛑 Stop Loss: ${recommendation.get('stop_loss', 'N/A')}")
                print(f"   🎯 Take Profit: ${recommendation.get('take_profit', 'N/A')}")
                print(f"   📊 Cantidad: {recommendation.get('quantity', 'N/A')}")
                print(f"   💸 Riesgo: ${recommendation.get('risk_amount', 'N/A')}")
                print(f"   📈 % Riesgo: {recommendation.get('risk_percentage', 'N/A')}%")
                print()
            
            # Display multi-timeframe analysis
            mtf_analysis = recommendation.get('mtf_analysis')
            if mtf_analysis:
                print("🔄 ANÁLISIS MULTI-TIMEFRAME:")
                print(f"   📊 Score Combinado: {mtf_analysis.get('combined_score', 'N/A')}")
                print(f"   🎯 Dirección: {mtf_analysis.get('direction', 'N/A')}")
                print(f"   💡 Confianza: {mtf_analysis.get('confidence', 'N/A')}")
                
                strategy_weights = mtf_analysis.get('strategy_weights', [])
                if strategy_weights:
                    print("   ⚖️ Pesos de Estrategias:")
                    for sw in strategy_weights:
                        print(f"      - {sw.get('strategy', 'N/A')} ({sw.get('timeframe', 'N/A')}): {sw.get('weight', 0):.3f}")
                
                weight_distribution = mtf_analysis.get('weight_distribution', {})
                if weight_distribution:
                    print("   📊 Distribución de Pesos:")
                    for direction, weight in weight_distribution.items():
                        print(f"      - {direction}: {weight:.3f}")
                print()
            
            # Display rationale
            rationale = recommendation.get('rationale', 'N/A')
            print(f"💭 RACIONAL: {rationale}")
            print()
            
            # Display hashes
            print("🔐 HASHES:")
            print(f"   📊 Dataset Hash: {recommendation.get('dataset_hash', 'N/A')}")
            print(f"   ⚙️ Params Hash: {recommendation.get('params_hash', 'N/A')}")
            print()
            
            print("✅ Prueba completada exitosamente!")
            
        else:
            print(f"❌ Error HTTP {response.status_code}")
            print(f"📝 Detalle: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión")
        print("💡 Asegúrate de que la API esté ejecutándose en http://localhost:8000")
        print("   Ejecuta: python -m uvicorn main:app --host 0.0.0.0 --port 8000")
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    
    print()
    print("=" * 60)
    print("🏁 Prueba de recomendaciones completada")

if __name__ == "__main__":
    test_recommendation_system()
