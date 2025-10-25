# 🚀 Guía Completa de Prueba - One Market Trading System

Esta guía te ayudará a probar todas las mejoras implementadas en el sistema One Market.

## 📋 Índice
1. [Verificación Inicial](#1-verificación-inicial)
2. [Sincronización de Datos](#2-sincronización-de-datos)
3. [Interfaz de Usuario Básica](#3-interfaz-de-usuario-básica)
4. [Interfaz de Usuario Mejorada](#4-interfaz-de-usuario-mejorada)
5. [Nuevas Funcionalidades](#5-nuevas-funcionalidades)
6. [Scripts de Automatización](#6-scripts-de-automatización)

---

## 1️⃣ Verificación Inicial

### Ejecutar Tests
Primero verifica que todas las pruebas pasen:

```bash
# Todas las pruebas nuevas
python -m pytest tests/test_signal_confidence.py tests/test_ui_skip_state.py tests/test_data_sync.py tests/test_decision_tracker.py -v

# Test completo del proyecto
python -m pytest tests/ -v --tb=short
```

**Esperado:** ✅ Todos los tests deben pasar (24 tests nuevos + tests existentes)

---

## 2️⃣ Sincronización de Datos

### Opción A: Sincronización Simple
```bash
# Sincronizar BTC/USDT 1h (últimos 7 días)
python -m scripts.sync_data --symbol "BTC/USDT" --timeframe "1h" --days 7
```

### Opción B: Sincronización Completa (Batch)
```bash
# Sincronizar múltiples símbolos/timeframes
python -m scripts.sync_data --batch --verbose
```

### Opción C: Dry Run (Prueba sin guardar)
```bash
# Probar sin guardar datos
python -m scripts.sync_data --dry-run --verbose
```

**Esperado:**
- ✅ Mensajes de progreso en consola
- ✅ Datos guardados en `storage/symbol=BTC-USDT/`
- ✅ Metadata de última actualización en `storage/last_updates.json`

---

## 3️⃣ Interfaz de Usuario Básica

### Lanzar UI Básica
```bash
python -m streamlit run ui/app.py
```

### Qué Verificar:

#### **Tab: 🎯 Trading Plan**
1. **Confianza de Señal Mejorada:**
   - Pasa el cursor sobre "Confianza Señal"
   - Verifica tooltip: "Estrategias a favor: X/Y"
   - La confianza debe estar en escala 0-100%

2. **Gráfico de Precios con Niveles:**
   - Busca decisiones en estado SKIP
   - Verifica que los niveles aparezcan en color naranja (hipotéticos)
   - Verifica etiquetas "Hipotético Entry", "Hipotético SL", "Hipotético TP"

3. **Estado de Decisión:**
   - Cuando estado es "⏸️ SKIP"
   - Pasa el cursor sobre el estado
   - Verifica tooltip con razón del skip

#### **Tab: 📊 Deep Dive**
4. **Reporte de Retroalimentación:**
   - Debe aparecer una nueva sección "📊 Análisis de Retroalimentación"
   - Métricas de rendimiento (si hay decisiones previas)
   - Gráficos de tendencias rolling
   - Análisis de razones de skip
   - Recomendaciones automáticas

---

## 4️⃣ Interfaz de Usuario Mejorada

### Lanzar UI Enhanced
```bash
python -m streamlit run ui/app_enhanced.py
```

### Qué Verificar:
- Todas las funcionalidades de UI básica
- Características adicionales de auto-strategy selection
- Comparación de estrategias
- Paper trading integrado

---

## 5️⃣ Nuevas Funcionalidades

### A. Confianza de Señal (0-1 scale)

**Test Manual:**
1. Abre UI
2. Navega a Trading Plan
3. Observa métrica "Confianza Señal"
4. Verifica que muestra porcentaje (0-100%)
5. Tooltip debe mostrar: "Estrategias a favor: X/Y"

**Test Programático:**
```python
from app.research.combine import simple_average
import pandas as pd

# Test con señales
dates = pd.date_range('2023-01-01', periods=10, freq='D')
signals = {
    'strategy1': pd.Series([1, 1, 1, 1, 1, -1, -1, -1, -1, -1], index=dates),
    'strategy2': pd.Series([1, 1, 1, 1, 1, -1, -1, -1, -1, -1], index=dates),
    'strategy3': pd.Series([1, 1, 1, 1, 1, -1, -1, -1, -1, -1], index=dates)
}

result = simple_average(signals)
print(f"Confianza: {result.confidence.iloc[0]}")  # Debe ser 1.0 (100%)
print(f"Metadata: {result.metadata}")  # num_strategies: 3
```

### B. Niveles Hipotéticos en Estado SKIP

**Test Manual:**
1. En UI, busca una decisión con `should_execute=False`
2. Verifica que el gráfico muestra:
   - Líneas en color naranja (no azul)
   - Etiquetas con prefijo "Hipotético"
   - Zona de entrada en color naranja (no azul claro)
3. Pasa cursor sobre "Estado: ⏸️ SKIP"
4. Verifica tooltip con razón del skip

### C. Actualización Diaria de Datos

**Test Manual:**
```bash
# 1. Ejecutar sincronización
python -m scripts.sync_data --symbol "BTC/USDT" --timeframe "1h" --days 7

# 2. Verificar archivo de tracking
cat storage/last_updates.json
```

**Contenido Esperado:**
```json
{
  "BTC/USDT_1h": {
    "symbol": "BTC/USDT",
    "timeframe": "1h",
    "last_update": "2025-10-19T22:00:00+00:00",
    "bars_count": 168,
    "latest_timestamp": 1760911200000,
    "latest_price": 108931.31,
    "success": true,
    "error": null
  }
}
```

**Test Programático:**
```python
from app.data.last_update import get_tracker, is_data_fresh

tracker = get_tracker()

# Verificar última actualización
record = tracker.get_last_update("BTC/USDT", "1h")
print(f"Última actualización: {record.last_update}")
print(f"Barras: {record.bars_count}")
print(f"Precio: ${record.latest_price:,.2f}")

# Verificar frescura
is_fresh = is_data_fresh("BTC/USDT", "1h", max_age_hours=24)
print(f"¿Datos frescos? {is_fresh}")

# Resumen
summary = tracker.get_data_summary()
print(f"Total registros: {summary['total_records']}")
print(f"Datos frescos: {summary['fresh_data']}")
print(f"Datos stale: {summary['stale_data']}")
```

### D. Loop de Retroalimentación

**Test Manual:**
1. Abre UI y navega a "📊 Deep Dive"
2. Verifica sección "📊 Análisis de Retroalimentación"
3. Observa:
   - Métricas de rendimiento
   - Gráficos de tendencias rolling
   - Análisis de razones de skip
   - Recomendaciones automáticas

**Test Programático:**
```python
from app.service.decision_tracker import get_tracker, record_decision, record_outcome
from app.service.decision import DailyDecision
from datetime import datetime, timezone

tracker = get_tracker()

# Crear decisión de prueba
decision = DailyDecision(
    decision_date=datetime.now(timezone.utc),
    trading_day=datetime.now().strftime('%Y-%m-%d'),
    window="A",
    signal=1,
    signal_strength=0.8,
    signal_source="test_strategy",
    should_execute=True,
    entry_price=105.0,
    stop_loss=100.0,
    take_profit=110.0,
    entry_mid=105.0,
    market_price=105.0,
    timestamp_ms=int(datetime.now().timestamp() * 1000)
)

# Registrar decisión
decision_id = record_decision(decision)
print(f"Decisión registrada: {decision_id}")

# Registrar resultado
record_outcome(
    decision_id=decision_id,
    outcome_price=108.0,
    pnl=3.0,
    pnl_pct=0.0286,
    was_executed=True,
    exit_reason="TP"
)

# Obtener métricas
metrics = tracker.get_performance_metrics(days=30)
print(f"Total decisiones: {metrics['total_decisions']}")
print(f"Tasa de éxito: {metrics['win_rate']:.1%}")
print(f"P&L total: ${metrics['total_pnl']:,.2f}")
print(f"Sharpe ratio: {metrics['sharpe_ratio']:.2f}")
```

---

## 6️⃣ Scripts de Automatización

### Configurar Cron Job (Linux/Mac)

1. **Editar crontab:**
```bash
crontab -e
```

2. **Agregar línea:**
```cron
# Ejecutar todos los días a las 2:00 AM
0 2 * * * cd /path/to/One_Market && python -m scripts.sync_data --batch >> logs/sync.log 2>&1
```

### GitHub Actions (Automatización Cloud)

El archivo `.github/workflows/daily-data-sync.yml` ya está configurado para:
- Ejecutarse diariamente a las 2:00 AM UTC
- Sincronizar todos los símbolos/timeframes
- Generar logs en caso de error
- Permitir ejecución manual

**Para activar:**
1. Push a GitHub
2. Ve a Actions > Daily Data Sync
3. Click "Run workflow" para prueba manual

### Windows Task Scheduler

1. **Crear script batch:**
```batch
@echo off
cd C:\path\to\One_Market
python -m scripts.sync_data --batch --verbose
```

2. **Configurar tarea:**
- Abrir Task Scheduler
- Create Basic Task
- Trigger: Daily 2:00 AM
- Action: Start Program
- Program: C:\path\to\sync_script.bat

---

## 🧪 Checklist de Verificación

### ✅ Tests Automatizados
- [ ] `test_signal_confidence.py` - 4 tests pasan
- [ ] `test_ui_skip_state.py` - 5 tests pasan
- [ ] `test_data_sync.py` - 8 tests pasan
- [ ] `test_decision_tracker.py` - 7 tests pasan

### ✅ Funcionalidades UI
- [ ] Tooltip de confianza muestra "X/Y estrategias"
- [ ] Niveles hipotéticos en color naranja
- [ ] Etiquetas "Hipotético" visibles
- [ ] Tooltip de skip_reason funcional
- [ ] Tab "Deep Dive" con reporte de retroalimentación

### ✅ Sincronización de Datos
- [ ] Script sync_data.py funciona
- [ ] Archivo last_updates.json se crea
- [ ] Datos se guardan en storage/
- [ ] Dry-run funciona correctamente

### ✅ Sistema de Retroalimentación
- [ ] Decisiones se registran
- [ ] Outcomes se guardan
- [ ] Métricas se calculan correctamente
- [ ] Gráficos de tendencias se generan
- [ ] Recomendaciones aparecen

---

## 🎯 Flujo de Trabajo Recomendado

### Uso Diario:

1. **Mañana:**
```bash
# Actualizar datos
python -m scripts.sync_data --batch

# Iniciar UI
python -m streamlit run ui/app.py
```

2. **Durante el día:**
- Monitorear Trading Plan
- Revisar niveles (reales o hipotéticos)
- Verificar razones de skip

3. **Final del día:**
- Revisar Deep Dive
- Analizar métricas de retroalimentación
- Ajustar parámetros según recomendaciones

### Análisis Semanal:

```bash
# Ver resumen de datos
python -c "
from app.data.last_update import get_data_summary
summary = get_data_summary()
print('=== RESUMEN DE DATOS ===')
for key, value in summary.items():
    print(f'{key}: {value}')
"

# Ver métricas de decisiones
python -c "
from app.service.decision_tracker import get_performance_metrics
metrics = get_performance_metrics(days=7)
print('=== MÉTRICAS SEMANALES ===')
for key, value in metrics.items():
    print(f'{key}: {value}')
"
```

---

## 🐛 Troubleshooting

### Problema: Tests fallan
**Solución:**
```bash
pip install --upgrade -r requirements.txt
python -m pytest tests/ -v --tb=short
```

### Problema: UI no se carga
**Solución:**
```bash
# Verificar instalación de Streamlit
pip install --upgrade streamlit

# Limpiar cache
streamlit cache clear

# Reiniciar
python -m streamlit run ui/app.py
```

### Problema: No hay datos
**Solución:**
```bash
# Sincronizar datos
python -m scripts.sync_data --batch --verbose

# Verificar archivos
ls -la storage/symbol=BTC-USDT/tf=1h/
```

### Problema: Retroalimentación vacía
**Solución:**
El sistema necesita decisiones previas para mostrar retroalimentación. 
Las decisiones se registran automáticamente cuando usas el sistema.

---

## 📚 Documentación Adicional

- `ARCHITECTURE.md` - Arquitectura del sistema
- `README.md` - Guía general
- `QUICKSTART.md` - Inicio rápido
- `UI_GUIDE.md` - Guía de interfaz

---

## 🎉 ¡Listo!

Ahora tienes todas las herramientas para probar el sistema completo con todas las mejoras implementadas. 

**Preguntas frecuentes:**
- **¿Cómo veo los logs?** → `logs/` directorio
- **¿Dónde están los datos?** → `storage/` directorio
- **¿Cómo exporto decisiones?** → Archivos JSON en `storage/`

**Siguiente paso:** Ejecuta la UI y explora las nuevas funcionalidades.

```bash
python -m streamlit run ui/app.py
```

¡Disfruta del sistema mejorado! 🚀







