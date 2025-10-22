#!/usr/bin/env python3
"""Execute UI using Python directly."""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Main function to run UI."""
    print("🚀 ONE MARKET - Ejecutando UI con Python")
    print("=" * 50)
    
    # Check if streamlit is installed
    try:
        import streamlit
        print("✅ Streamlit ya está instalado")
    except ImportError:
        print("📦 Instalando Streamlit...")
        if install_package("streamlit"):
            print("✅ Streamlit instalado correctamente")
        else:
            print("❌ Error instalando Streamlit")
            return False
    
    # Check other dependencies
    dependencies = ["plotly", "pandas", "requests"]
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} ya está instalado")
        except ImportError:
            print(f"📦 Instalando {dep}...")
            if install_package(dep):
                print(f"✅ {dep} instalado correctamente")
            else:
                print(f"❌ Error instalando {dep}")
    
    print("\n🚀 Iniciando UI de Streamlit...")
    print("ℹ️  La UI se abrirá en: http://localhost:8501")
    print("ℹ️  Asegúrate de que la API esté corriendo en: http://localhost:8000")
    print("\n" + "=" * 50)
    
    # Run streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "ui/app_complete.py", 
            "--server.port", "8501"
        ])
    except KeyboardInterrupt:
        print("\n✅ UI cerrada correctamente")
    except Exception as e:
        print(f"❌ Error ejecutando UI: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 UI ejecutada exitosamente")
    else:
        print("\n❌ Error ejecutando UI")
    
    input("\nPresiona Enter para continuar...")
