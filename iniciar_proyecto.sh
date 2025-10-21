#!/bin/bash

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         🚀 ONE MARKET - Inicio del Proyecto 🚀             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Verificar Python
echo "[1/5] 🔍 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python no encontrado. Por favor instala Python 3.11+"
    exit 1
fi
python3 --version
echo "✅ Python OK"
echo ""

# Verificar dependencias críticas
echo "[2/5] 📦 Verificando dependencias..."
if ! python3 -c "import fastapi, streamlit, pandas, numpy, ccxt, pydantic" 2>/dev/null; then
    echo "⚠️  Faltan dependencias. Instalando..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Error instalando dependencias"
        exit 1
    fi
else
    echo "✅ Dependencias OK"
fi
echo ""

# Verificar imports de la aplicación
echo "[3/5] 🔧 Verificando integridad del sistema..."
python3 -c "from app.data import DataStore, DataFetcher; from main import app; print('✅ Sistema OK')" 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Error en la aplicación. Revisa los logs arriba."
    exit 1
fi
echo ""

# Crear directorios necesarios
echo "[4/5] 📁 Creando directorios..."
mkdir -p storage logs artifacts
echo "✅ Directorios creados"
echo ""

# Mostrar opciones
echo "[5/5] 🎯 Selecciona qué iniciar:"
echo ""
echo "  1. 🌐 API FastAPI (puerto 8000)"
echo "  2. 📊 UI Streamlit (puerto 8501)"
echo "  3. 🔄 Ambos (API + UI en background)"
echo "  4. 🧪 Ejecutar tests"
echo "  5. ❌ Salir"
echo ""
read -p "Opción (1-5): " opcion

case $opcion in
    1)
        echo ""
        echo "🌐 Iniciando API FastAPI..."
        echo ""
        echo "ℹ️  La API estará disponible en: http://localhost:8000"
        echo "ℹ️  Documentación interactiva: http://localhost:8000/docs"
        echo ""
        echo "Presiona Ctrl+C para detener"
        echo ""
        python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    2)
        echo ""
        echo "📊 Iniciando UI Streamlit..."
        echo ""
        echo "ℹ️  La UI estará disponible en: http://localhost:8501"
        echo ""
        echo "Presiona Ctrl+C para detener"
        echo ""
        export PYTHONPATH=$(pwd)
        streamlit run ui/app_enhanced.py
        ;;
    3)
        echo ""
        echo "🔄 Iniciando API y UI..."
        echo ""
        echo "ℹ️  API: http://localhost:8000"
        echo "ℹ️  UI:  http://localhost:8501"
        echo ""
        
        # Iniciar API en background
        nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > logs/api.log 2>&1 &
        API_PID=$!
        echo "✅ API iniciada (PID: $API_PID)"
        
        sleep 3
        
        # Iniciar UI en background
        export PYTHONPATH=$(pwd)
        nohup streamlit run ui/app_enhanced.py > logs/ui.log 2>&1 &
        UI_PID=$!
        echo "✅ UI iniciada (PID: $UI_PID)"
        
        echo ""
        echo "ℹ️  Para detener los servicios:"
        echo "   kill $API_PID $UI_PID"
        echo ""
        echo "ℹ️  Logs disponibles en:"
        echo "   API: logs/api.log"
        echo "   UI:  logs/ui.log"
        echo ""
        ;;
    4)
        echo ""
        echo "🧪 Ejecutando tests..."
        echo ""
        python3 -m pytest tests/ -v --tb=short
        echo ""
        if [ $? -eq 0 ]; then
            echo "✅ Todos los tests pasaron"
        else
            echo "❌ Algunos tests fallaron"
        fi
        ;;
    5)
        echo ""
        echo "👋 Saliendo..."
        exit 0
        ;;
    *)
        echo "❌ Opción inválida"
        exit 1
        ;;
esac

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  Gracias por usar ONE MARKET                ║"
echo "╚════════════════════════════════════════════════════════════╝"

