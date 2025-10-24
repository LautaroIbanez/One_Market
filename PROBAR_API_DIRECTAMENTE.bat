@echo off
title ONE MARKET - Probar API Directamente
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Probar API Directamente         ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0
echo ✅ Directorio: %CD%

echo.
echo 🔬 Probando API directamente...
echo.

python -c "
import requests
import json
from datetime import datetime

print('🔍 Probando endpoint de salud...')
try:
    health_response = requests.get('http://localhost:8000/health', timeout=5)
    if health_response.status_code == 200:
        print('✅ API Health: OK')
        print(f'   Respuesta: {health_response.json()}')
    else:
        print(f'❌ API Health: ERROR {health_response.status_code}')
        exit(1)
except Exception as e:
    print(f'❌ Error conectando API: {e}')
    exit(1)

print()
print('🔍 Probando endpoint de recomendaciones...')
try:
    rec_response = requests.get('http://localhost:8000/recommendation/daily', 
                               params={'symbol': 'BTC/USDT', 'date': datetime.now().strftime('%Y-%m-%d')}, 
                               timeout=10)
    
    if rec_response.status_code == 200:
        data = rec_response.json()
        print('✅ Recomendación obtenida:')
        print(f'   - Dirección: {data.get(\"direction\")}')
        print(f'   - Confianza: {data.get(\"confidence\")}%')
        print(f'   - Precio Entrada: {data.get(\"entry_price\")}')
        print(f'   - Razonamiento: {data.get(\"rationale\")}')
        
        if data.get('direction') != 'HOLD' and data.get('confidence', 0) > 0:
            print('🎉 ¡API devuelve recomendaciones correctas!')
        else:
            print('❌ API sigue devolviendo HOLD')
    else:
        print(f'❌ Error en recomendaciones: {rec_response.status_code}')
        print(f'   Respuesta: {rec_response.text}')
        
except Exception as e:
    print(f'❌ Error obteniendo recomendación: {e}')
"

echo.
echo 🛑 Presiona cualquier tecla para continuar...
pause >nul


