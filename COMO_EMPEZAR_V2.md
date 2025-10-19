# 🚀 Cómo Empezar con One Market v2.0

## ⚡ Inicio Rápido (3 Pasos)

### 1️⃣ Asegurar Datos Disponibles
```powershell
python examples/example_fetch_data.py
```
⏱️ Tiempo: 1-2 minutos  
✅ Descarga datos de BTC-USDT en timeframes 15m, 1h, 4h, 1d

### 2️⃣ Elegir tu Interfaz

#### Opción A: UI con Auto-Selección de Estrategias (🏆 NUEVO)
```powershell
.\EJECUTAR_ENHANCED_UI.bat
```
- ✨ Selección automática de mejor estrategia
- 📊 Comparación de estrategias
- 📜 Historial de trades
- 💼 Perfiles de riesgo

#### Opción B: UI Original con Tabs
```powershell
.\EJECUTAR_UI.bat
```
- 🎯 Trading Plan (vista rápida)
- 📊 Deep Dive (análisis detallado)

### 3️⃣ Explorar y Usar
- Navega por los tabs
- Ajusta parámetros en sidebar
- Sigue las recomendaciones

---

## 📚 Documentación Disponible

| Archivo | Descripción | Para quién |
|---------|-------------|-----------|
| `NUEVO_SISTEMA_ESTRATEGIAS.md` | Sistema de auto-selección | Todos ⭐ |
| `UI_GUIDE.md` | Guía completa de la UI | Usuarios UI |
| `SISTEMA_COMPLETO_V2_RESUMEN.md` | Resumen técnico completo | Desarrolladores |
| `TEST_RAPIDO_5MIN.md` | Checklist de 5 minutos | Testing |
| `GUIA_PRUEBAS_UI.md` | Checklist completo UI | Testing |

---

## 🎯 ¿Cuál UI Usar?

### UI Enhanced (`app_enhanced.py`) - NUEVO ✨
**Usa esta si**:
- Quieres que el sistema elija la estrategia por ti
- Tienes capital pequeño ($500-$10K)
- Prefieres decisiones automáticas basadas en datos
- Quieres ver comparación de estrategias
- Necesitas historial de trades

**Pros**:
- ✅ Automático
- ✅ Optimizado para capital pequeño
- ✅ Tracking completo
- ✅ Perfiles de riesgo

**Contras**:
- ⚠️ Requiere backtesting (10-30 seg primera vez)
- ⚠️ Más complejo para principiantes absolutos

### UI Original (`app.py`) - V2.0
**Usa esta si**:
- Quieres más control manual
- Prefieres combinar estrategias manualmente
- No necesitas auto-selección
- Quieres análisis multi-horizonte detallado

**Pros**:
- ✅ Más rápida (sin backtesting automático)
- ✅ Control total
- ✅ Workflow probado

**Contras**:
- ⚠️ Sin selección automática
- ⚠️ Tienes que decidir qué estrategia usar

---

## 💼 Perfiles de Riesgo

| Perfil | Capital | Risk/Trade | Min Position | Uso |
|--------|---------|------------|--------------|-----|
| 🌱 Starter | $500-$2K | 1.5% | $10 | Aprendizaje |
| 📈 Intermediate | $3K-$10K | 2.0% | $50 | Crecimiento |
| 💎 Advanced | $15K-$100K | 2-4% | $200 | Activo |
| 🏆 Professional | $100K+ | 2-5% | $500 | Pro |

**Auto-selección**: El sistema elige el perfil automáticamente según tu capital

---

## 🔧 Comandos Útiles

### Ejecutar UIs:
```powershell
# Enhanced (auto-selección)
.\EJECUTAR_ENHANCED_UI.bat

# Original (tabs trading/deep dive)
.\EJECUTAR_UI.bat

# API connected
python -m streamlit run ui/app_api_connected.py
```

### Ejecutar Ejemplos:
```powershell
# Fetch datos
python examples/example_fetch_data.py

# Auto-selección de estrategias
python examples/example_auto_strategy_selection.py

# Backtest completo
python examples/example_backtest_complete.py
```

### Ejecutar API:
```powershell
python main.py
# Docs: http://localhost:8000/docs
```

### Ejecutar Tests:
```powershell
# Tests de UI
python -m pytest tests/test_ui_smoke.py -v

# Todos los tests
python -m pytest tests/ -v

# Test específico
python -m pytest tests/test_service_advisor.py -v
```

---

## 🎓 Learning Path

### Nivel 1: Principiante (Día 1-7)
1. Ejecutar `example_fetch_data.py`
2. Abrir `UI_GUIDE.md` y leer sección de tabs
3. Ejecutar `EJECUTAR_UI.bat` (UI original)
4. Explorar Tab "Trading Plan"
5. Familiarizarse con métricas

### Nivel 2: Intermedio (Semana 2-4)
1. Ejecutar `EJECUTAR_ENHANCED_UI.bat` (UI enhanced)
2. Entender cómo funciona auto-selección
3. Ejecutar `example_auto_strategy_selection.py`
4. Ver comparación de estrategias
5. Ejecutar primer trade en Paper Trading

### Nivel 3: Avanzado (Mes 2+)
1. Leer `SISTEMA_COMPLETO_V2_RESUMEN.md`
2. Explorar código en `app/service/`
3. Usar API endpoints (`main.py`)
4. Personalizar perfiles de riesgo
5. Crear tu propia estrategia

---

## 📊 Roadmap Futuro (Opcional)

### Short-term:
- [ ] Instalar vectorbt para backtests completos
- [ ] Ejecutar 10-20 trades para generar historial
- [ ] Configurar scheduler para backtests automáticos diarios

### Medium-term:
- [ ] Agregar más estrategias al registry
- [ ] Implementar walk-forward optimization
- [ ] Crear dashboard de performance

### Long-term:
- [ ] Integración con exchange API para ejecución automática
- [ ] Machine learning para optimización de parámetros
- [ ] Multi-symbol portfolio management

---

## 🆘 Soporte

### Recursos:
- `README.md` - Visión general del proyecto
- `ARCHITECTURE.md` - Arquitectura del sistema
- `BACKTEST_DESIGN.md` - Diseño de backtesting
- `UI_GUIDE.md` v2.0 - Guía de la interfaz
- `CHANGELOG.md` v2.0.0 - Cambios completos

### Testing:
- `TEST_RAPIDO_5MIN.md` - Verificar en 5 minutos
- `GUIA_PRUEBAS_UI.md` - Checklist completo

### Common Issues:
1. **No data**: Run `example_fetch_data.py`
2. **Import errors**: `pip install -r requirements.txt`
3. **vectorbt missing**: Optional, install with `pip install vectorbt`
4. **Port busy**: Use `--server.port 8502`

---

## ✅ Checklist de Verificación

Antes de empezar a tradear real:

- [ ] ✅ Datos descargados (storage/ tiene archivos)
- [ ] ✅ UI Enhanced funciona (tabs se cargan)
- [ ] ✅ Estrategia se selecciona automáticamente
- [ ] ✅ Plan de trade se genera correctamente
- [ ] ✅ Entiendes el indicador de confianza
- [ ] ✅ Sabes cómo ejecutar en Binance
- [ ] ✅ Has probado en Paper Trading primero
- [ ] ✅ Tienes cuenta de Binance verificada
- [ ] ✅ Entiendes los riesgos (puedes perder dinero)
- [ ] ✅ Solo usas capital que puedes permitirte perder

---

## 🎉 ¡Listo para Empezar!

**Comando para ejecutar AHORA**:
```powershell
.\EJECUTAR_ENHANCED_UI.bat
```

**URL**: http://localhost:8501

**Tiempo total de setup**: ~5 minutos  
**Tiempo diario de uso**: ~3 minutos

---

**¡Bienvenido a One Market v2.0 - Trading Inteligente con Auto-Selección!** 🏆

**Fecha**: Octubre 19, 2025  
**Versión**: 2.0.0  
**Status**: ✅ LISTO PARA PRODUCCIÓN

