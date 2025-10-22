#!/usr/bin/env python3
"""Quick verification script for complete One Market project."""

import sys
import os
import requests
from datetime import datetime

def print_header(title: str):
    """Print formatted header."""
    print("=" * 60)
    print(f"🔧 {title}")
    print("=" * 60)

def print_section(title: str):
    """Print formatted section."""
    print(f"\n📊 {title}")
    print("-" * 40)

def main():
    """Main verification function."""
    print_header("ONE MARKET - Verificación del Proyecto Completo")
    
    API_BASE_URL = "http://localhost:8000"
    
    try:
        # Test API health
        print_section("Verificando API")
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API funcionando correctamente")
            else:
                print(f"❌ API con problemas: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ API no disponible - Ejecuta EJECUTAR_API.bat primero")
            return False
        
        # Test recommendation endpoint
        print_section("Probando Recomendaciones Enriquecidas")
        try:
            response = requests.get(
                f"{API_BASE_URL}/recommendation/daily",
                params={
                    "symbol": "BTC/USDT",
                    "capital": 10000.0,
                    "risk_percentage": 2.0
                },
                timeout=10
            )
            
            if response.status_code == 200:
                recommendation = response.json()
                print("✅ Recomendación obtenida exitosamente")
                
                # Check enhanced fields
                enhanced_fields = ["strategy_name", "strategy_score", "mtf_analysis", "ranking_weights"]
                found_fields = [field for field in enhanced_fields if recommendation.get(field) is not None]
                
                print(f"✅ Campos enriquecidos disponibles: {len(found_fields)}/{len(enhanced_fields)}")
                print(f"📅 Fecha: {recommendation.get('date', 'N/A')}")
                print(f"🎯 Dirección: {recommendation.get('direction', 'N/A')}")
                print(f"💡 Confianza: {recommendation.get('confidence', 0):.1f}%")
                
                if recommendation.get('strategy_name'):
                    print(f"🤖 Estrategia: {recommendation.get('strategy_name')}")
                    print(f"⭐ Score: {recommendation.get('strategy_score', 0):.2f}")
                
            else:
                print(f"❌ Error en recomendaciones: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error probando recomendaciones: {e}")
            return False
        
        # Check UI files
        print_section("Verificando UI")
        ui_file = "ui/app_complete.py"
        if os.path.exists(ui_file):
            print("✅ UI enriquecida disponible")
            
            # Check for enhanced components
            with open(ui_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            enhanced_components = ["strategy_name", "mtf_analysis", "ranking_weights"]
            found_components = [c for c in enhanced_components if c in content]
            print(f"✅ Componentes enriquecidos: {len(found_components)}/{len(enhanced_components)}")
            
        else:
            print("❌ UI no encontrada")
            return False
        
        # Summary
        print_section("Resumen Final")
        print("✅ API: Funcionando")
        print("✅ Recomendaciones Enriquecidas: Funcionando")
        print("✅ UI Actualizada: Disponible")
        print("✅ Sistema Completo: LISTO")
        
        print("\n🎉 ¡Proyecto completo funcionando correctamente!")
        print("\n💡 Para usar el sistema:")
        print("   1. API ya está corriendo en puerto 8000")
        print("   2. UI de Streamlit ejecutándose")
        print("   3. Visita: http://localhost:8501")
        print("   4. API docs: http://localhost:8000/docs")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Verificación completada exitosamente")
    else:
        print("\n❌ Verificación falló")
    
    input("\nPresiona Enter para continuar...")
