#!/usr/bin/env python3
"""Diagnostic script for date issues in recommendations."""

import sys
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_header(title: str):
    """Print formatted header."""
    print("=" * 60)
    print(f"🔧 {title}")
    print("=" * 60)

def print_section(title: str):
    """Print formatted section."""
    print(f"\n📊 {title}")
    print("-" * 40)

def diagnose_date_issues():
    """Diagnose date-related issues."""
    print_header("ONE MARKET - Diagnóstico de Fechas")
    
    # Check current system time
    print_section("Verificación de Fechas del Sistema")
    
    now_utc = datetime.now(timezone.utc)
    now_local = datetime.now()
    
    print(f"🕐 Fecha actual UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🕐 Fecha actual local: {now_local.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Fecha para recomendaciones: {now_utc.strftime('%Y-%m-%d')}")
    
    # Check timezone info
    print_section("Información de Zona Horaria")
    
    try:
        arg_tz = ZoneInfo("America/Argentina/Buenos_Aires")
        now_arg = datetime.now(arg_tz)
        print(f"🇦🇷 Fecha Argentina: {now_arg.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 Fecha Argentina para recomendaciones: {now_arg.strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"❌ Error con zona horaria Argentina: {e}")
    
    # Test recommendation service date
    print_section("Prueba de Servicio de Recomendaciones")
    
    try:
        from app.service.daily_recommendation import DailyRecommendationService
        
        service = DailyRecommendationService()
        
        # Test with current date
        current_date = now_utc.strftime('%Y-%m-%d')
        print(f"🧪 Probando recomendación para fecha: {current_date}")
        
        recommendation = service.get_daily_recommendation(
            symbol="BTC/USDT",
            date=current_date,
            timeframes=["1h", "4h", "1d"],
            use_strategy_ranking=True
        )
        
        print(f"✅ Recomendación generada:")
        print(f"   Fecha solicitada: {current_date}")
        print(f"   Fecha en recomendación: {recommendation.date}")
        print(f"   Dirección: {recommendation.direction}")
        print(f"   Confianza: {recommendation.confidence:.1%}")
        
        if recommendation.date != current_date:
            print(f"⚠️  PROBLEMA: Fecha solicitada ({current_date}) != Fecha en recomendación ({recommendation.date})")
        else:
            print(f"✅ Fechas coinciden correctamente")
            
    except Exception as e:
        print(f"❌ Error en servicio de recomendaciones: {e}")
    
    # Check API endpoint behavior
    print_section("Simulación de Endpoint API")
    
    try:
        # Simulate the API endpoint logic
        if True:  # date is None
            api_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            print(f"🌐 Fecha generada por API: {api_date}")
            
            # Validate date format
            try:
                datetime.fromisoformat(api_date)
                print(f"✅ Formato de fecha válido")
            except ValueError as e:
                print(f"❌ Formato de fecha inválido: {e}")
        
    except Exception as e:
        print(f"❌ Error en simulación de API: {e}")

def fix_date_issue():
    """Attempt to fix date issue."""
    print_section("Intento de Solución")
    
    try:
        # Force current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        print(f"🔧 Forzando fecha actual: {current_date}")
        
        from app.service.daily_recommendation import DailyRecommendationService
        
        service = DailyRecommendationService()
        
        # Test with forced current date
        recommendation = service.get_daily_recommendation(
            symbol="BTC/USDT",
            date=current_date,
            timeframes=["1h", "4h", "1d"],
            use_strategy_ranking=False  # Use signal-based for testing
        )
        
        print(f"✅ Recomendación con fecha forzada:")
        print(f"   Fecha solicitada: {current_date}")
        print(f"   Fecha en recomendación: {recommendation.date}")
        print(f"   Dirección: {recommendation.direction}")
        print(f"   Confianza: {recommendation.confidence:.1%}")
        print(f"   Rationale: {recommendation.rationale}")
        
        if recommendation.date == current_date:
            print(f"✅ PROBLEMA SOLUCIONADO: Fechas coinciden")
        else:
            print(f"❌ PROBLEMA PERSISTE: Fechas no coinciden")
            
    except Exception as e:
        print(f"❌ Error en solución: {e}")

def main():
    """Main diagnostic function."""
    try:
        diagnose_date_issues()
        fix_date_issue()
        
        print_section("Resumen del Diagnóstico")
        print("✅ Verificación de fechas del sistema completada")
        print("✅ Prueba de servicio de recomendaciones completada")
        print("✅ Simulación de endpoint API completada")
        print("✅ Intento de solución completado")
        
    except Exception as e:
        print(f"❌ Error en diagnóstico: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Diagnóstico completado exitosamente")
    else:
        print("\n❌ Diagnóstico falló")
    
    input("\nPresiona Enter para continuar...")
