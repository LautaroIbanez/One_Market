@echo off
title ONE MARKET - Probar Recomendaciones Directo
chcp 65001 >nul
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 ONE MARKET - Probar Recomendaciones Directo   ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 Cambiando al directorio del proyecto...
cd /d %~dp0
echo ✅ Directorio: %CD%

echo.
echo 🔬 Probando recomendaciones directamente...
echo.

python -c "
import sys
import os
sys.path.append('.')

from app.service.daily_recommendation import DailyRecommendationService
from datetime import datetime

print('🔍 Creando servicio de recomendaciones...')
service = DailyRecommendationService(capital=10000.0, max_risk_pct=2.0)
print('✅ Servicio creado')

print('🔍 Generando recomendación...')
date = datetime.now().strftime('%Y-%m-%d')
recommendation = service._get_signal_based_recommendation('BTC/USDT', date, ['1h', '4h', '1d'])

print('📊 RESULTADO:')
print(f'   - Dirección: {recommendation.direction}')
print(f'   - Confianza: {recommendation.confidence}%')
print(f'   - Precio Entrada: {recommendation.entry_price}')
print(f'   - Razonamiento: {recommendation.rationale}')

if recommendation.direction.value != 'HOLD' and recommendation.confidence > 0:
    print('🎉 ¡Recomendación generada correctamente!')
else:
    print('❌ Recomendación sigue siendo HOLD')
"

echo.
echo 🛑 Presiona cualquier tecla para continuar...
pause >nul

