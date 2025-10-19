# 🏆 Nuevo Sistema de Selección Automática de Estrategias

## 🎯 ¿Qué es?

Un sistema inteligente que:
1. ✅ **Ejecuta backtests automáticos** en todas tus estrategias cada día
2. ✅ **Rankea las estrategias** por Sharpe, Win Rate y Drawdown
3. ✅ **Selecciona la mejor** automáticamente
4. ✅ **Genera un plan de trade** concreto con precio, cantidad y niveles
5. ✅ **Compara real vs simulado** para detectar divergencias

---

## 🚀 Cómo Usarlo

### Opción 1: Interfaz Visual (Recomendado)

```powershell
.\EJECUTAR_ENHANCED_UI.bat
```

O desde PowerShell:
```powershell
python -m streamlit run ui/app_enhanced.py
```

### Opción 2: Script de Consola

```powershell
python examples/example_auto_strategy_selection.py
```

---

## 📊 Componentes Nuevos

### 1. Strategy Orchestrator
**Archivo**: `app/service/strategy_orchestrator.py`

**Funcionalidad**:
- Registra todas las estrategias disponibles
- Ejecuta backtests con capital base de $1,000
- Calcula métricas completas para cada estrategia
- Rankea por score compuesto (Sharpe 30%, WR 25%, DD 20%, PF 15%, Exp 10%)

**Uso**:
```python
from app.service.strategy_orchestrator import StrategyOrchestrator

orchestrator = StrategyOrchestrator(capital=1000, max_risk_pct=0.02)
results = orchestrator.run_all_backtests("BTC-USDT", "1h")
ranked = orchestrator.rank_strategies(results)
best_strategy, score = ranked[0]
```

### 2. Strategy Ranking Service
**Archivo**: `app/service/strategy_ranking.py`

**Funcionalidad**:
- Obtiene la mejor estrategia del día
- Genera plan de trade concreto (entrada, SL, TP, cantidad)
- Calcula nivel de confianza (HIGH/MEDIUM/LOW)
- Compara todas las estrategias en DataFrame

**Uso**:
```python
from app.service.strategy_ranking import StrategyRankingService

service = StrategyRankingService(capital=1000)
recommendation = service.get_daily_recommendation("BTC-USDT", "1h", capital=1000)

print(f"Mejor estrategia: {recommendation.best_strategy_name}")
print(f"Dirección: {recommendation.signal_direction}")
print(f"Entrada: ${recommendation.entry_price}")
```

### 3. Truth Sync Service
**Archivo**: `app/service/truth_sync.py`

**Funcionalidad**:
- Sincroniza trades ejecutados con predicciones del backtest
- Calcula divergencia entre real y simulado
- Genera alertas automáticas cuando divergencia > 20%
- Crea reportes diarios de comparación

**Uso**:
```python
from app.service.truth_sync import TruthSyncService

sync = TruthSyncService()
result = sync.sync_daily_performance()  # Sincroniza ayer
report = sync.generate_daily_report(days=7)
print(report)
```

### 4. Risk Profiles
**Archivo**: `app/config/settings.py`

**Perfiles Disponibles**:
- 🌱 **Starter $1K**: Capital $500-$2K, Risk 1.5%, Min $10/trade
- 📈 **Intermediate $5K**: Capital $3K-$10K, Risk 2%, Min $50/trade
- 💎 **Advanced $25K**: Capital $15K-$100K, Risk 2-4%, Min $200/trade
- 🏆 **Professional $100K+**: Capital $75K+, Risk 2-5%, Min $500/trade

**Uso**:
```python
from app.config.settings import get_risk_profile_for_capital

profile = get_risk_profile_for_capital(1000)  # Auto-selecciona Starter
print(profile.display_name)
print(f"Risk: {profile.default_risk_pct:.1%}")
```

---

## 🌐 Nuevos Endpoints de API

### GET /strategy/best
Obtiene la mejor estrategia del día

**Request**:
```
GET /strategy/best?symbol=BTC-USDT&timeframe=1h&capital=1000
```

**Response**:
```json
{
  "best_strategy_name": "MA Crossover",
  "composite_score": 85.3,
  "sharpe_ratio": 1.8,
  "win_rate": 0.62,
  "signal_direction": 1,
  "entry_price": 95234.50,
  "stop_loss": 94100.00,
  "take_profit": 97500.00,
  "quantity": 0.010526,
  "confidence_level": "HIGH"
}
```

### GET /strategy/compare
Compara todas las estrategias

**Response**:
```json
{
  "strategies": [
    {
      "Strategy": "MA Crossover",
      "Sharpe": 1.8,
      "Win Rate": 0.62,
      ...
    }
  ],
  "count": 3
}
```

### GET /trades/history
Historial de trades con filtros

**Request**:
```
GET /trades/history?symbol=BTC-USDT&start_date=2025-10-01&limit=50
```

### GET /trades/stats
Estadísticas agregadas

**Request**:
```
GET /trades/stats?days=30
```

**Response**:
```json
{
  "stats": {
    "total_trades": 45,
    "win_rate": 0.58,
    "total_pnl": 234.50,
    "profit_factor": 1.85
  }
}
```

### GET /alerts/divergence
Alertas de divergencia real vs simulado

**Response**:
```json
{
  "alerts": [
    {
      "date": "2025-10-18",
      "strategy_name": "RSI Regime",
      "alert_reason": "PnL divergence: 25.3%"
    }
  ]
}
```

### GET /profiles
Lista de perfiles de riesgo

### GET /profiles/recommend
Perfil recomendado para un capital

---

## 📱 Interfaz Mejorada (app_enhanced.py)

### Tab 1: 🏆 Auto Strategy
- Muestra la mejor estrategia del día
- Score compuesto y métricas clave
- Nivel de confianza (HIGH/MEDIUM/LOW)
- Plan de trade completo con precio, cantidad, SL y TP

### Tab 2: 📊 Strategy Comparison
- Tabla comparativa de todas las estrategias
- Gráficos de Sharpe y Win Rate
- Identifica la mejor por cada métrica
- Descarga CSV de la comparación

### Tab 3: 📜 Trade History
- Historial completo de trades ejecutados
- Filtros por estado y lado
- Estadísticas agregadas (Win Rate, PnL Total, etc.)
- Gráfico de P&L acumulado
- Descarga CSV del historial

---

## 💼 Perfiles de Riesgo en UI

En el sidebar ahora puedes:
1. Seleccionar perfil manualmente o automático
2. El perfil se ajusta según tu capital
3. Ver detalles del perfil seleccionado
4. Los parámetros (risk%, comisiones, ATR multipliers) se aplican automáticamente

---

## 🔄 Workflow Diario Completo

### Mañana (09:00 AM):

1. **Abrir app_enhanced.py**
   ```
   .\EJECUTAR_ENHANCED_UI.bat
   ```

2. **Ir al Tab "🏆 Auto Strategy"**
   - Ver cuál estrategia es la mejor hoy
   - Revisar el score y confianza
   - Si confianza es HIGH (🟢), continuar

3. **Revisar Plan de Trade**
   - Dirección: LONG o SHORT
   - Precio de entrada
   - Stop Loss y Take Profit
   - Cantidad exacta en units

4. **Ir al Tab "📊 Strategy Comparison"** (Opcional)
   - Ver cómo se comparan todas las estrategias
   - Validar que la selección tiene sentido

5. **Ejecutar en Binance**
   - Seguir la guía paso a paso en onboarding
   - Colocar orden LIMIT
   - Configurar SL y TP
   - Monitorear

### Tarde/Noche:

6. **Monitorear Posición**
   - Revisar evolución del precio
   - Verificar que SL/TP siguen activos

7. **Fin del Día**
   - Si el trade cerró, registrar resultado
   - Ir al Tab "📜 Trade History"
   - Ver el trade en la tabla
   - Revisar P&L acumulado

### Semanal/Mensual:

8. **Análisis de Divergencia**
   - Ejecutar script de sincronización
   - Revisar alertas de divergencia
   - Ajustar estrategias si es necesario

---

## 🧪 Testing

### Test 1: Ejecutar Ejemplo
```powershell
python examples/example_auto_strategy_selection.py
```

**Resultado esperado**:
- Lista todas las estrategias
- Muestra la mejor con score
- Genera plan de trade
- Muestra tabla comparativa

### Test 2: UI Enhanced
```powershell
python -m streamlit run ui/app_enhanced.py
```

**Verificar**:
- Tab Auto Strategy muestra recomendación
- Tab Strategy Comparison muestra tabla y gráficos
- Tab Trade History muestra trades (si hay)
- Selector de perfil de riesgo funciona

### Test 3: API Endpoints
```powershell
# Iniciar API
python main.py

# En otra terminal, test endpoints:
curl http://localhost:8000/strategy/best?symbol=BTC-USDT&timeframe=1h&capital=1000
curl http://localhost:8000/strategy/compare?symbol=BTC-USDT&timeframe=1h
curl http://localhost:8000/trades/history
curl http://localhost:8000/profiles
```

---

## ⚠️ Consideraciones Importantes

### Capital Pequeño ($1K)
- ✅ Usar perfil "Starter $1K"
- ✅ Risk 1.5% máximo ($15/trade)
- ✅ Verificar que posición mínima de Binance se cumple (típicamente $10)
- ⚠️ Comisiones son significativas (0.1% cada entrada/salida = 0.2% total)
- ⚠️ Slippage puede afectar más en % con capital pequeño

### Ejecución en Binance
- ✅ Siempre usar órdenes LIMIT (no MARKET)
- ✅ Configurar SL y TP SIEMPRE
- ✅ Verificar saldo disponible antes
- ⚠️ Horarios: Mercado crypto es 24/7, pero nuestras ventanas son específicas
- ⚠️ Volatilidad: BTC puede moverse rápido, estar atento

### Divergencia Real vs Simulado
- Es normal que haya divergencia de 5-10%
- Factores: slippage real, timing de ejecución, condiciones de mercado
- Alertas solo se disparan con divergencia > 20%
- Revisar semanalmente para ajustar si es necesario

---

## 📚 Archivos Creados

1. `app/service/strategy_orchestrator.py` - Orquestador de backtests
2. `app/service/strategy_ranking.py` - Servicio de ranking y recomendación
3. `app/service/truth_sync.py` - Sincronización real vs simulado
4. `ui/app_enhanced.py` - UI mejorada con auto-selección
5. `ui/onboarding.py` - Guía de ejecución en Binance
6. `examples/example_auto_strategy_selection.py` - Ejemplo de uso
7. `app/config/settings.py` - Perfiles de riesgo (extendido)
8. `app/service/paper_trading.py` - Nuevas tablas DB (extendido)
9. `main.py` - Nuevos endpoints API (extendido)

---

## 🎊 Próximos Pasos

1. **Probar la UI Enhanced**:
   ```
   .\EJECUTAR_ENHANCED_UI.bat
   ```

2. **Ejecutar ejemplo de consola**:
   ```
   python examples/example_auto_strategy_selection.py
   ```

3. **Explorar los 3 tabs** en la UI:
   - Tab 1: Ver estrategia seleccionada automáticamente
   - Tab 2: Comparar todas las estrategias
   - Tab 3: Ver historial (si tienes trades)

4. **Probar perfiles de riesgo**:
   - Cambiar capital en sidebar
   - Ver cómo se selecciona el perfil automáticamente

5. **Ejecutar tu primer trade**:
   - Seguir la guía de onboarding paso a paso
   - Usar capital pequeño ($50-$100) para probar

---

## 💡 Beneficios del Sistema

### Antes (Manual):
- ❌ Tenías que decidir qué estrategia usar
- ❌ No sabías cuál funcionaba mejor últimamente
- ❌ Tenías que calcular manualmente los niveles
- ❌ No había comparación sistemática

### Ahora (Automático):
- ✅ El sistema elige la mejor estrategia por ti
- ✅ Basado en datos de los últimos 90 días
- ✅ Plan de trade completo generado automáticamente
- ✅ Confianza medida objetivamente
- ✅ Historial y comparación siempre disponibles

---

## 📈 Métricas de Ranking

### Composite Score (0-100):
- **30%** - Sharpe Ratio (rendimiento ajustado por riesgo)
- **25%** - Win Rate (% de trades ganadores)
- **20%** - Max Drawdown (control de pérdidas)
- **15%** - Profit Factor (wins/losses ratio)
- **10%** - Expectancy (ganancia esperada por trade)

### Niveles de Confianza:
- **🟢 HIGH** (75-100): Ejecutar con confianza
- **🟡 MEDIUM** (50-74): Ejecutar con precaución
- **🔴 LOW** (<50): Considerar skip o reducir tamaño

---

## 🐛 Troubleshooting

### "No se pudo generar recomendación"
**Causa**: Faltan datos históricos  
**Solución**:
```powershell
python examples/example_fetch_data.py
```

### "Insufficient data for backtest"
**Causa**: Menos de 100 barras disponibles  
**Solución**: Fetch más datos o usar timeframe más largo (1d)

### "No hay trades en historial"
**Causa**: No has ejecutado trades aún  
**Solución**: Es normal, ejecuta tu primer trade y aparecerá

### Backtest muy lento (>30 seg)
**Causa**: Muchos datos o PC lenta  
**Solución**: Reducir lookback_days de 90 a 30

---

## 🎓 Guía Rápida para Principiantes

### Tu Primer Trade con Auto-Selection:

1. **Capital**: Empieza con $500-$1,000
2. **Perfil**: Selecciona "🌱 Starter $1K"
3. **Símbolo**: Usa BTC-USDT (más líquido)
4. **Timeframe**: Usa 1h o 4h (más estable)
5. **Ejecuta ejemplo**: `python examples/example_auto_strategy_selection.py`
6. **Revisa recomendación**: ¿Confianza HIGH?
7. **Abre Binance**: Sigue la guía paso a paso
8. **Ejecuta**: Orden LIMIT + SL + TP
9. **Monitorea**: Durante el día
10. **Cierra**: Cuando se active SL o TP
11. **Registra**: Anota el resultado

### Después de 10 Trades:
- Revisa Win Rate en "Trade History"
- Compara con el backtest
- Ajusta risk% si es necesario
- Considera cambiar de perfil si el capital creció

---

## 📞 Soporte y Recursos

- **Documentación**: Ver `UI_GUIDE.md` v2.0
- **Arquitectura**: Ver `ARCHITECTURE.md`
- **Backtesting**: Ver `BACKTEST_DESIGN.md`
- **API Docs**: http://localhost:8000/docs (cuando la API esté corriendo)

---

**Versión**: 2.0.0  
**Última actualización**: Octubre 19, 2025  
**Estado**: ✅ Completamente funcional y listo para usar

---

## 🎉 ¡Felicitaciones!

Ahora tienes un sistema de trading **completamente automatizado** que:
- Selecciona la mejor estrategia por ti
- Genera planes de trade concretos
- Monitorea la performance
- Alerta sobre divergencias

**¡Empieza a tradear con confianza!** 🚀

