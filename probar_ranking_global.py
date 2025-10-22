#!/usr/bin/env python3
"""
Script para probar el sistema de ranking global.
"""
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

def test_global_ranking():
    """Probar el sistema de ranking global."""
    print("🔧 Probando sistema de ranking global...")
    
    try:
        # Probar endpoint de salud
        print("🌐 Verificando salud del servicio...")
        response = requests.get(f"{API_BASE}/global-ranking/health", timeout=10)
        
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Servicio saludable: {health.get('status')}")
            print(f"📊 Timeframes: {health.get('timeframes')}")
            print(f"⚖️ Pesos: {health.get('ranking_weights')}")
        else:
            print(f"❌ Error de salud: HTTP {response.status_code}")
            return False
        
        # Probar ranking para BTC/USDT
        print("\n🎯 Ejecutando ranking para BTC/USDT...")
        payload = {
            "symbol": "BTC/USDT",
            "date": None,  # Usar fecha actual
            "timeframes": ["1h", "4h", "1d"],
            "ranking_weights": {
                "sharpe_ratio": 0.3,
                "win_rate": 0.25,
                "profit_factor": 0.2,
                "max_drawdown": 0.15,
                "cagr": 0.1
            }
        }
        
        response = requests.post(
            f"{API_BASE}/global-ranking/run",
            json=payload,
            timeout=120  # 2 minutos para ejecutar todos los backtests
        )
        
        print(f"📥 Respuesta: HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Ranking ejecutado exitosamente")
            print(f"📊 Símbolo: {result.get('symbol')}")
            print(f"📅 Fecha: {result.get('date')}")
            print(f"🔢 Total estrategias: {result.get('total_strategies')}")
            print(f"✅ Estrategias válidas: {result.get('valid_strategies')}")
            print(f"⏰ Tiempo ejecución: {result.get('execution_time'):.2f}s")
            print(f"🏆 Mejor estrategia: {result.get('best_strategy')}")
            print(f"📈 Mejor score: {result.get('best_score'):.3f}")
            
            # Mostrar top 5 estrategias
            rankings = result.get('rankings', [])
            if rankings:
                print(f"\n🏆 TOP 5 ESTRATEGIAS:")
                for i, ranking in enumerate(rankings[:5]):
                    print(f"  {i+1}. {ranking.get('strategy_name')} ({ranking.get('timeframe')})")
                    print(f"     Score: {ranking.get('composite_score'):.3f}")
                    print(f"     Sharpe: {ranking.get('sharpe_ratio'):.3f}")
                    print(f"     Win Rate: {ranking.get('win_rate'):.1%}")
                    print(f"     Trades: {ranking.get('total_trades')}")
                    print()
            
            return True
        else:
            print(f"❌ Error ejecutando ranking: HTTP {response.status_code}")
            try:
                error_detail = response.json()
                print(f"📝 Detalle: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"📝 Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_get_rankings():
    """Probar obtención de rankings."""
    print("\n📊 Probando obtención de rankings...")
    
    try:
        response = requests.get(
            f"{API_BASE}/global-ranking/rankings/BTC/USDT",
            params={"limit": 5},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Rankings obtenidos exitosamente")
            print(f"📊 Símbolo: {result.get('symbol')}")
            print(f"📅 Fecha: {result.get('date')}")
            print(f"🔢 Total estrategias: {result.get('total_strategies')}")
            
            rankings = result.get('rankings', [])
            if rankings:
                print(f"\n🏆 TOP {len(rankings)} ESTRATEGIAS:")
                for i, ranking in enumerate(rankings):
                    print(f"  {i+1}. {ranking.get('strategy_name')} ({ranking.get('timeframe')})")
                    print(f"     Posición: {ranking.get('rank_position')}")
                    print(f"     Score: {ranking.get('composite_score'):.3f}")
                    print(f"     Sharpe: {ranking.get('sharpe_ratio'):.3f}")
                    print(f"     Win Rate: {ranking.get('win_rate'):.1%}")
                    print()
            
            return True
        else:
            print(f"❌ Error obteniendo rankings: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_get_metrics():
    """Probar obtención de métricas consolidadas."""
    print("\n📈 Probando métricas consolidadas...")
    
    try:
        response = requests.get(
            f"{API_BASE}/global-ranking/metrics/BTC/USDT",
            timeout=30
        )
        
        if response.status_code == 200:
            metrics = response.json()
            print("✅ Métricas obtenidas exitosamente")
            print(f"📊 Símbolo: {metrics.get('symbol')}")
            print(f"📅 Fecha: {metrics.get('date')}")
            print(f"🔢 Total estrategias: {metrics.get('total_strategies')}")
            print(f"✅ Estrategias válidas: {metrics.get('valid_strategies')}")
            print(f"📈 Sharpe promedio: {metrics.get('avg_sharpe'):.3f}")
            print(f"🎯 Win Rate promedio: {metrics.get('avg_win_rate'):.1%}")
            print(f"💰 Profit Factor promedio: {metrics.get('avg_profit_factor'):.3f}")
            print(f"📉 Max Drawdown promedio: {metrics.get('avg_max_drawdown'):.1%}")
            print(f"📊 CAGR promedio: {metrics.get('avg_cagr'):.1%}")
            print(f"🏆 Mejor estrategia: {metrics.get('best_strategy')}")
            print(f"📈 Mejor score: {metrics.get('best_score'):.3f}")
            
            return True
        else:
            print(f"❌ Error obteniendo métricas: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 PROBAR RANKING GLOBAL")
    print("=" * 60)
    
    # Probar ranking global
    ranking_success = test_global_ranking()
    
    if ranking_success:
        # Probar obtención de rankings
        rankings_success = test_get_rankings()
        
        # Probar obtención de métricas
        metrics_success = test_get_metrics()
        
        # Resumen
        print("\n" + "=" * 60)
        print("📋 RESUMEN DEL RANKING GLOBAL:")
        print(f"  🎯 Ranking ejecución: {'✅' if ranking_success else '❌'}")
        print(f"  📊 Obtención rankings: {'✅' if rankings_success else '❌'}")
        print(f"  📈 Obtención métricas: {'✅' if metrics_success else '❌'}")
        
        if ranking_success and rankings_success and metrics_success:
            print(f"\n🎉 ¡RANKING GLOBAL FUNCIONANDO CORRECTAMENTE!")
            print(f"✅ Sistema automatizado de ranking implementado")
            print(f"✅ API endpoints funcionando")
            print(f"✅ Base de datos persistente")
            print(f"✅ Métricas consolidadas disponibles")
        else:
            print(f"\n⚠️  Algunos componentes del ranking global tienen problemas")
    else:
        print(f"\n❌ RANKING GLOBAL NO FUNCIONA")
        print(f"🔧 Revisa los errores arriba para más detalles")
