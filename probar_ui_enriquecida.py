#!/usr/bin/env python3
"""Test script for enhanced UI recommendations."""

import sys
import os
import requests
from datetime import datetime

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

def test_api_recommendation():
    """Test API recommendation endpoint."""
    print_header("ONE MARKET - Probar UI Enriquecida")
    
    API_BASE_URL = "http://localhost:8000"
    
    try:
        print_section("Probando Endpoint de Recomendación")
        
        # Test recommendation endpoint
        response = requests.get(
            f"{API_BASE_URL}/recommendation/daily",
            params={
                "symbol": "BTC/USDT",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "capital": 10000.0,
                "risk_percentage": 2.0
            },
            timeout=30
        )
        
        if response.status_code == 200:
            recommendation = response.json()
            print("✅ Recomendación obtenida exitosamente")
            
            # Display basic info
            print(f"📊 Símbolo: {recommendation.get('symbol', 'N/A')}")
            print(f"📅 Fecha: {recommendation.get('date', 'N/A')}")
            print(f"🎯 Dirección: {recommendation.get('direction', 'N/A')}")
            print(f"💡 Confianza: {recommendation.get('confidence', 0):.1f}%")
            
            # Check for enhanced fields
            print_section("Verificando Campos Enriquecidos")
            
            enhanced_fields = [
                "strategy_name", "strategy_score", "sharpe_ratio", 
                "win_rate", "max_drawdown", "mtf_analysis", "ranking_weights"
            ]
            
            for field in enhanced_fields:
                value = recommendation.get(field)
                if value is not None:
                    print(f"✅ {field}: {value}")
                else:
                    print(f"❌ {field}: No disponible")
            
            # Check MTF analysis
            mtf_analysis = recommendation.get("mtf_analysis")
            if mtf_analysis:
                print_section("Análisis Multi-Timeframe")
                print(f"📊 Score combinado: {mtf_analysis.get('combined_score', 0):.2f}")
                print(f"🎯 Dirección: {mtf_analysis.get('direction', 0)}")
                print(f"💡 Confianza: {mtf_analysis.get('confidence', 0):.1%}")
                
                # Strategy weights
                strategy_weights = mtf_analysis.get("strategy_weights", [])
                if strategy_weights:
                    print(f"⚖️ Estrategias con peso: {len(strategy_weights)}")
                    for sw in strategy_weights:
                        print(f"   - {sw.get('strategy', 'N/A')} ({sw.get('timeframe', 'N/A')}): {sw.get('weight', 0):.3f}")
                
                # Weight distribution
                weight_dist = mtf_analysis.get("weight_distribution", {})
                if weight_dist:
                    print(f"📊 Distribución: LONG={weight_dist.get('LONG', 0):.3f}, SHORT={weight_dist.get('SHORT', 0):.3f}, HOLD={weight_dist.get('HOLD', 0):.3f}")
            
            return True
            
        else:
            print(f"❌ Error HTTP {response.status_code}")
            print(f"📝 Detalle: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar a la API")
        print("💡 Asegúrate de que la API esté corriendo en puerto 8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_ui_components():
    """Test UI components."""
    print_section("Verificando Componentes de UI")
    
    try:
        # Check if UI file exists and has enhanced components
        ui_file = "ui/app_complete.py"
        if os.path.exists(ui_file):
            with open(ui_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for enhanced components
            enhanced_components = [
                "strategy_name", "strategy_score", "sharpe_ratio",
                "win_rate", "max_drawdown", "mtf_analysis",
                "ranking_weights", "strategy_weights"
            ]
            
            found_components = []
            for component in enhanced_components:
                if component in content:
                    found_components.append(component)
            
            print(f"✅ Componentes enriquecidos encontrados: {len(found_components)}/{len(enhanced_components)}")
            for component in found_components:
                print(f"   ✅ {component}")
            
            missing_components = [c for c in enhanced_components if c not in found_components]
            if missing_components:
                print(f"⚠️  Componentes faltantes: {missing_components}")
            
            return len(found_components) >= len(enhanced_components) * 0.8  # 80% success rate
            
        else:
            print("❌ Archivo de UI no encontrado")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando UI: {e}")
        return False

def main():
    """Main test function."""
    try:
        # Test API
        api_success = test_api_recommendation()
        
        # Test UI components
        ui_success = test_ui_components()
        
        print_section("Resumen de Pruebas")
        
        if api_success:
            print("✅ API de recomendaciones: Funcionando")
        else:
            print("❌ API de recomendaciones: Con problemas")
        
        if ui_success:
            print("✅ Componentes de UI: Actualizados")
        else:
            print("❌ Componentes de UI: Necesitan actualización")
        
        if api_success and ui_success:
            print("\n🎉 ¡UI enriquecida lista para usar!")
            print("💡 Ejecuta: streamlit run ui/app_complete.py")
        else:
            print("\n⚠️  Algunos componentes necesitan atención")
        
    except Exception as e:
        print(f"❌ Error en pruebas: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Pruebas completadas")
    else:
        print("\n❌ Pruebas fallaron")
    
    input("\nPresiona Enter para continuar...")
