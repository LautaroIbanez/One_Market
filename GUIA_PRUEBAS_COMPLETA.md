# 🧪 Guía Completa de Pruebas - One Market Trading System

**Fecha**: 20 de Octubre 2025  
**Versión**: 2.1.0

---

## 🎯 Objetivo

Esta guía te llevará paso a paso por todas las funcionalidades del sistema, incluyendo las 3 mejoras recién implementadas.

---

## ✅ Pre-requisitos

Antes de empezar, verifica que:
- [x] La UI está corriendo en `http://localhost:8501`
- [x] Tienes datos de BTC/USDT en storage
- [x] El DecisionTracker está poblado (20 trades históricos)

---

## 📋 Plan de Pruebas

### **Parte 1: Verificar Datos Básicos** (5 minutos)
### **Parte 2: Probar Tab "🎯 Trading Plan"** (10 minutos)
### **Parte 3: Probar Tab "📊 Deep Dive"** (5 minutos)
### **Parte 4: Probar Funcionalidades Avanzadas** (10 minutos)
### **Parte 5: Verificar Todas las Mejoras Nuevas** (10 minutos)

**Tiempo Total Estimado**: ~40 minutos

---

## 🔍 PARTE 1: Verificar Datos Básicos (5 min)

### 1.1 Abrir la Aplicación

1. Abre tu navegador
2. Ve a: `http://localhost:8501`
3. **✅ VERIFICA:** La página carga sin errores

### 1.2 Verificar Sidebar

**En el Sidebar izquierdo:**

1. **Symbol**: Debe mostrar "BTC/USDT" (o similar)
2. **Timeframe**: Debe tener opciones: 15m, 1h, 4h, 1d
3. **Trading Mode**: Paper Trading / Live Trading
4. **Capital**: $100,000 (ajustable)
5. **Risk per Trade**: 2.0% (ajustable)

**✅ ACCIÓN:** Prueba cambiar cada valor y observa que se actualiza

### 1.3 Verificar Datos Cargados

**Al final del sidebar:**

```
📊 Datos Disponibles
Registros: XXX bars
Rango: YYYY-MM-DD to YYYY-MM-DD
Última actualización: HH:MM:SS
```

**✅ VERIFICA:** 
- Hay más de 100 bars cargados
- El rango de fechas es reciente
- La última actualización es de hoy

---

## 🎯 PARTE 2: Tab "🎯 Trading Plan" (10 min)

### 2.1 Briefing Diario (NUEVO ✨)

**Ubicación:** Primera sección después del separador

**Lo que debes ver:**

```
📋 Briefing Diario del Trade

[4 métricas en columnas:]
Estado          Dirección       Confianza    Volatilidad
✅/⏸️           🟢/🔴/⚪       XX.X%        🟢/🟡/🔴
```

**✅ PRUEBA 1: Verificar Métricas**
- Estado debe ser "EJECUTAR" o "SKIP"
- Dirección debe ser LONG, SHORT o FLAT con ícono de color
- Confianza debe estar entre 0-100%
- Volatilidad debe mostrar estado: NORMAL, HIGH, EXTREME

**✅ PRUEBA 2: Expandir Recomendación**
1. Click en "📝 Ver Recomendación Completa"
2. Debe expandirse mostrando texto detallado con:
   - Decisión de ejecutar o skip
   - Plan de entrada (si aplica)
   - Contexto de mercado
   - Performance reciente (30 días)

**✅ PRUEBA 3: Warnings de Riesgo**
- Si la volatilidad es alta/extrema, debe aparecer un warning naranja/rojo
- Si el win rate es bajo (<40%), debe aparecer otro warning

**✅ PRUEBA 4: Descargar Briefing**
1. Click en "📥 Descargar Briefing (Markdown)"
2. Debe descargarse un archivo `.md`
3. Abre el archivo en un editor de texto
4. Verifica que contenga:
   - Fecha y símbolo
   - Recomendación completa
   - Breakdown de estrategias
   - Validation checks

**⏱️ Checkpoint:** Has probado el briefing diario completo

---

### 2.2 Confianza del Sistema

**Ubicación:** Después del briefing

**Lo que debes ver:**
```
📈 Confianza del Sistema

[Ícono grande]  Nivel: ALTA/MEDIA/BAJA
Descripción de confianza
```

**✅ PRUEBA:** 
- El ícono debe corresponder al nivel (⭐⭐⭐ = alta, ⭐⭐ = media, ⭐ = baja)
- La descripción debe explicar el nivel de confianza

---

### 2.3 Señal de Hoy

**Ubicación:** Sección "📍 Señal de Hoy"

**4 Métricas principales:**
1. **Dirección**: LONG/SHORT/FLAT con delta
2. **Confianza**: Porcentaje con tooltip
3. **Precio Actual**: Valor en USD
4. **Estado**: EJECUTAR o SKIP

**✅ PRUEBA 1: Verificar Tooltips**
- Pasa el mouse sobre "Confianza"
- Debe mostrar: "Estrategias a favor: X/Y"
- Pasa el mouse sobre "Estado" si es SKIP
- Debe mostrar la razón del skip

**✅ PRUEBA 2: Consistencia**
- La dirección debe coincidir con el briefing
- La confianza debe coincidir con el briefing

---

### 2.4 Plan de Trade (Si EJECUTAR)

**Si `Estado = ✅ EJECUTAR`:**

**Debes ver 2 columnas:**

**Columna 1 - Entrada:**
- Precio de Entrada
- Rango de Entrada
- Cantidad
- Valor Nocional

**Columna 2 - Gestión de Riesgo:**
- Stop Loss
- Take Profit
- R/R Ratio
- Riesgo ($)

**✅ PRUEBA:**
- Todos los valores deben ser numéricos y positivos
- R/R Ratio debe ser > 1.0 (idealmente > 1.5)
- Riesgo debe ser ~2% del capital

**Ventana de Trading:**
```
⏰ Ventana de Trading
🟢 Ventana A/B activa (horarios)
```

**Botones de Acción:**
- 📄 Ejecutar Paper Trade
- 💰 Ejecutar Live Trade (si modo Live)
- 💾 Guardar Plan

**✅ PRUEBA:**
- Click en "📄 Ejecutar Paper Trade"
- Debe mostrar mensaje de éxito

---

### 2.5 Escenario Alternativo (Si SKIP) (NUEVO ✨)

**Si `Estado = ⏸️ SKIP`:**

**Debes ver:**
```
🔮 Escenario Alternativo (Hipotético)

⏰ Operación Bloqueada: [razón]

💡 Explicación: [detalle de por qué]
```

**✅ PRUEBA 1: Verificar Explicación**
- La razón debe ser clara (ej: "Outside trading hours")
- La explicación debe dar contexto completo

**Si hay señal direccional (LONG/SHORT):**

**Debes ver:**
```
📋 Plan que se ejecutaría (si condiciones fueran favorables)

[2 columnas:]
📍 Entrada Hipotética        🛡️ Niveles de Riesgo
- Precio de Entrada          - Stop Loss
- Dirección                  - Take Profit
- Confianza                  - R/R Ratio

💼 Posición Propuesta
[3 columnas: Cantidad, Valor, Riesgo]

ℹ️ Nota explicativa
```

**✅ PRUEBA 2: Verificar Plan Hipotético**
- Todos los valores deben estar calculados
- El plan debe ser consistente (LONG → SL < Entry < TP)
- La distancia al precio actual debe mostrarse como delta
- Debe aparecer nota explicando que es hipotético

**✅ PRUEBA 3: Colores y Visualización**
- Los niveles hipotéticos NO deben tener fondo verde (como ejecutables)
- Debe ser claro que es un "escenario alternativo"

**⏱️ Checkpoint:** Has probado el plan hipotético completo

---

### 2.6 Gráfico de Precio

**Ubicación:** Sección "📈 Gráfico de Precio"

**Debes ver:**
- Gráfico de velas (candlestick)
- Líneas horizontales para niveles

**Si EJECUTAR:**
- Línea AZUL: Entry Price
- Línea ROJA: Stop Loss
- Línea VERDE: Take Profit
- Zona AZUL CLARO: Entry Band
- Etiquetas: "Entry Price", "Stop Loss", "Take Profit"

**Si SKIP (con plan hipotético):**
- Línea NARANJA: Entry Price Hipotético
- Línea NARANJA: SL Hipotético
- Línea NARANJA: TP Hipotético
- Zona NARANJA: Entry Band Hipotético
- Etiquetas: "Hipotético Entry", "Hipotético SL", "Hipotético TP"

**✅ PRUEBA:**
1. Verifica que las líneas aparecen correctamente
2. Haz zoom en el gráfico (arrastrando)
3. Pasa el mouse sobre las velas (debe mostrar OHLCV)
4. Verifica que los colores son correctos según estado

---

## 📊 PARTE 3: Tab "📊 Deep Dive" (5 min)

### 3.1 Breakdown de Estrategias

**Ubicación:** Primera sección

**Debes ver tabla con columnas:**
- Estrategia
- Señal (LONG/SHORT/FLAT)
- Confianza

**✅ PRUEBA:**
- Debe haber 3-6 estrategias listadas
- Cada una con señal y confianza
- Las señales pueden ser diferentes entre estrategias

---

### 3.2 Método de Combinación

**Debes ver:**
- Nombre del método (Simple Average, Sharpe Weighted, etc.)
- Descripción del método
- Explicación de cómo combina señales

**✅ PRUEBA:**
- Cambia el método en sidebar
- Verifica que se actualiza la descripción

---

### 3.3 Análisis de Retroalimentación (NUEVO ✨)

**Ubicación:** Sección "📊 Análisis de Retroalimentación"

**Debes ver:**

**Métricas de Performance (últimos 30 días):**
```
[6 métricas en columnas:]
Total Decisiones    Ejecutadas    Win Rate    Sharpe    Total PnL    Max DD
```

**✅ PRUEBA 1: Verificar Métricas**
- Total Decisiones debe ser > 0 (si poblaste el tracker)
- Win Rate debe estar entre 0-100%
- Sharpe debe ser un número (puede ser negativo)
- Total PnL debe mostrar ganancia/pérdida en USD
- Max DD debe ser negativo (drawdown)

**Si no hay datos:**
```
ℹ️ No hay suficientes datos...
```

**Si hay datos, debes ver gráficos:**

**Gráfico 1: Tendencias Rolling**
- Líneas para: PnL acumulado, Win Rate, Confianza
- Eje X: Fechas
- Eje Y: Valores

**Gráfico 2: Razones de Skip**
- Gráfico de barras
- Muestra frecuencia de cada razón de skip

**Recomendaciones:**
- Lista de recomendaciones basadas en performance
- Puede incluir ajustes de parámetros sugeridos

**✅ PRUEBA 2: Interactividad**
- Pasa el mouse sobre los gráficos
- Debe mostrar tooltips con valores exactos
- Haz zoom si es posible

**⏱️ Checkpoint:** Has visto todas las métricas de retroalimentación

---

### 3.4 Métricas de Backtest

**Ubicación:** Sección "📈 Métricas de Backtest"

**Debes ver:**

**Gráfico de Equity Curve:**
- Línea ascendente/descendente mostrando capital
- Período: últimos 12 meses

**Gráfico de Drawdown:**
- Área roja mostrando caídas
- Debe coincidir con períodos de pérdidas

**6 Métricas clave:**
```
CAGR        Sharpe      Max DD
Win Rate    PF          Return
```

**✅ PRUEBA:**
- Verifica que las métricas son consistentes
- CAGR debe ser razonable (-50% a +200%)
- Sharpe > 1.0 es bueno, > 2.0 es excelente
- Max DD debe ser negativo
- Win Rate entre 40-70% es típico

---

## 🚀 PARTE 4: Funcionalidades Avanzadas (10 min)

### 4.1 Cambiar Símbolo y Timeframe

**En Sidebar:**
1. Cambia el símbolo a otro disponible
2. Cambia el timeframe (15m, 1h, 4h, 1d)

**✅ VERIFICA:**
- La página se recarga
- Todos los datos se actualizan
- El briefing se regenera
- El gráfico muestra el nuevo timeframe

---

### 4.2 Ajustar Parámetros de Riesgo

**En Sidebar:**
1. Cambia "Capital" a $50,000
2. Cambia "Risk per Trade" a 1.0%

**✅ VERIFICA:**
- El position sizing se actualiza
- El riesgo en USD cambia proporcionalmente
- El briefing refleja los nuevos valores

---

### 4.3 Probar Diferentes Métodos de Combinación

**En Sidebar:**
1. Cambia "Signal Combination Method"
2. Prueba: Simple Average, Weighted Average, Sharpe Weighted

**✅ VERIFICA:**
- La señal puede cambiar
- La confianza puede cambiar
- El briefing se actualiza
- La descripción del método cambia

---

### 4.4 Verificar Actualización de Datos

**En Sidebar, al final:**

**Debes ver botón:**
```
🔄 Actualizar Datos
```

**✅ PRUEBA:**
1. Click en el botón
2. Debe mostrar spinner "Actualizando..."
3. Los datos se recargan
4. La última actualización cambia

---

## ✨ PARTE 5: Verificar Todas las Mejoras Nuevas (10 min)

Esta es la parte más importante - verificar que las 3 mejoras implementadas funcionen perfectamente.

### 5.1 Mejora 1: DecisionTracker Poblado

**Verificación en UI:**

1. Ve a tab "📊 Deep Dive"
2. Scroll hasta "📊 Análisis de Retroalimentación"
3. **✅ VERIFICA:**
   - Total Decisiones > 0 (debe ser ~9)
   - Ejecutadas = Total (todas fueron ejecutadas en backtest)
   - Win Rate ~66-67%
   - Total PnL ~$13,500
   - Hay gráficos de tendencias rolling

**Verificación en Archivos:**

```bash
# Abre PowerShell en la carpeta del proyecto
cd storage
cat decision_history.json
cat decision_outcomes.json
```

**✅ VERIFICA:**
- Ambos archivos existen
- Contienen datos en formato JSON
- Hay múltiples registros

**✅ PRUEBA COMPLETA:**
- Si no ves datos, ejecuta:
  ```bash
  python scripts/populate_decision_tracker.py --days 60
  ```
- Recarga la UI
- Debes ver las métricas pobladas

---

### 5.2 Mejora 2: Plan Hipotético en SKIP

**Cómo Forzar un SKIP:**

**Opción A: Esperar fuera de horario**
- Si estás fuera de 09:00-12:30 o 14:00-17:00 UTC-3
- Debes ver automáticamente SKIP

**Opción B: Modificar temporalmente**
- En el código, puedes simular estar fuera de horario

**✅ PRUEBA COMPLETA:**

1. **Verifica Estado SKIP:**
   ```
   Estado: ⏸️ SKIP
   ```

2. **Verifica Razón:**
   ```
   ⏰ Operación Bloqueada: Outside trading hours
   ```

3. **Verifica Explicación:**
   ```
   💡 Explicación: Las operaciones solo se ejecutan durante...
   ```

4. **Verifica Plan Hipotético:**
   - Debe aparecer sección "📋 Plan que se ejecutaría..."
   - Con entrada, SL, TP calculados
   - Con position sizing
   - Con nota explicativa

5. **Verifica Gráfico:**
   - Las líneas deben ser NARANJAS
   - Las etiquetas deben decir "Hipotético"
   - La zona debe ser naranja transparente

**✅ CHECKLIST Plan Hipotético:**
- [ ] Sección aparece cuando hay SKIP + señal direccional
- [ ] Muestra precio de entrada hipotético
- [ ] Muestra SL y TP hipotéticos
- [ ] Muestra R/R ratio
- [ ] Muestra position sizing completo
- [ ] Muestra distancia al precio actual
- [ ] Tiene nota explicativa
- [ ] Gráfico usa colores naranjas
- [ ] Etiquetas dicen "Hipotético"

---

### 5.3 Mejora 3: Briefing Diario

**✅ CHECKLIST Briefing Visual:**

1. **Tarjeta de Métricas:**
   - [ ] 4 métricas visibles (Estado, Dirección, Confianza, Volatilidad)
   - [ ] Íconos de colores correctos
   - [ ] Valores actualizados

2. **Recomendación Expandible:**
   - [ ] Se puede expandir/colapsar
   - [ ] Muestra texto completo
   - [ ] Incluye plan de entrada (si ejecutar)
   - [ ] Incluye contexto de mercado
   - [ ] Incluye performance reciente

3. **Warnings de Riesgo:**
   - [ ] Aparecen si volatilidad alta/extrema
   - [ ] Aparecen si win rate bajo
   - [ ] Colores de alerta correctos (amarillo/rojo)

4. **Descarga de Markdown:**
   - [ ] Botón visible y funcional
   - [ ] Descarga archivo .md
   - [ ] Archivo contiene briefing completo
   - [ ] Formato Markdown correcto

5. **Breakdown de Estrategias:**
   - [ ] Lista todas las estrategias usadas
   - [ ] Muestra señal de cada una
   - [ ] Formato claro

6. **Validation Checks:**
   - [ ] Lista de checks con ✅/❌
   - [ ] Checks relevantes (has signal, trading hours, etc.)

**✅ PRUEBA DESCARGA:**

1. Click en "📥 Descargar Briefing (Markdown)"
2. Abre el archivo descargado
3. **Debe contener:**
   ```markdown
   # Daily Trading Briefing
   **Date**: 2025-10-20...
   **Symbol**: BTC/USDT
   
   ✅ **EXECUTE TRADE** / ⏸️ **SKIP TRADE**
   ...
   
   ## Strategy Breakdown
   ...
   
   ## Validation Checks
   ...
   ```

**✅ PRUEBA API (Opcional):**

Si tienes `main.py` corriendo:

```bash
# En otra terminal o PowerShell
curl -X POST http://localhost:8000/briefing/generate `
  -H "Content-Type: application/json" `
  -d '{"symbol":"BTC/USDT","timeframe":"1h"}'
```

Debe retornar JSON con briefing completo.

---

## 🎯 Pruebas de Integración Final

### Test 1: Flujo Completo - Escenario EJECUTAR

1. **Setup:**
   - Asegúrate de estar dentro de horario de trading (09:00-17:00 UTC-3)
   - Usa symbol con señal fuerte

2. **Verificar:**
   - [ ] Briefing muestra "✅ EJECUTAR"
   - [ ] Hay plan de trade completo
   - [ ] Gráfico muestra líneas azules/verdes/rojas
   - [ ] Botones de acción disponibles
   - [ ] Métricas de retroalimentación visibles
   - [ ] Descarga de briefing funciona

### Test 2: Flujo Completo - Escenario SKIP

1. **Setup:**
   - Fuera de horario de trading O
   - Signal = 0 (FLAT)

2. **Verificar:**
   - [ ] Briefing muestra "⏸️ SKIP"
   - [ ] Aparece explicación de bloqueo
   - [ ] Si hay señal: plan hipotético visible
   - [ ] Gráfico usa colores naranjas (hipotético)
   - [ ] Descarga de briefing funciona (con estado SKIP)

### Test 3: Cambio de Parámetros

1. **Cambios sucesivos:**
   - Cambia símbolo
   - Cambia timeframe
   - Cambia capital
   - Cambia risk %
   - Cambia método de combinación

2. **Verificar después de cada cambio:**
   - [ ] Briefing se regenera
   - [ ] Métricas se actualizan
   - [ ] Gráfico se actualiza
   - [ ] Sin errores en consola

---

## 📊 Checklist Final de Verificación

### Funcionalidades Core:
- [ ] Sistema carga sin errores
- [ ] Sidebar funciona correctamente
- [ ] Datos se cargan y muestran
- [ ] Tabs funcionan (Trading Plan y Deep Dive)
- [ ] Gráficos renderizan correctamente

### Mejora 1 - DecisionTracker:
- [ ] Archivos JSON existen en storage/
- [ ] Métricas de retroalimentación pobladas
- [ ] Gráficos rolling muestran datos
- [ ] Win rate, Sharpe, PnL son razonables

### Mejora 2 - Plan Hipotético:
- [ ] Aparece cuando hay SKIP + señal
- [ ] Calcula todos los niveles
- [ ] Usa colores naranjas en gráfico
- [ ] Etiquetas dicen "Hipotético"
- [ ] Nota explicativa visible

### Mejora 3 - Briefing Diario:
- [ ] Tarjeta visible en Tab 1
- [ ] 4 métricas actualizadas
- [ ] Recomendación expandible funciona
- [ ] Warnings aparecen cuando aplican
- [ ] Descarga de Markdown funciona
- [ ] Breakdown de estrategias correcto
- [ ] Validation checks visibles

### Extras:
- [ ] Performance es aceptable (< 5s carga)
- [ ] No hay mensajes de error en UI
- [ ] Todos los botones responden
- [ ] Tooltips informativos funcionan

---

## 🐛 Troubleshooting

### Problema: No aparece el briefing
**Solución:**
- Verifica que hay datos cargados (>100 bars)
- Recarga la página (F5)
- Revisa la consola del navegador (F12)

### Problema: Plan hipotético no aparece
**Solución:**
- Solo aparece si estado = SKIP Y señal ≠ 0
- Verifica que estés fuera de horario de trading
- O que tengas señal direccional (LONG/SHORT)

### Problema: Métricas de retroalimentación vacías
**Solución:**
```bash
python scripts/populate_decision_tracker.py --days 60
```
Luego recarga la UI.

### Problema: Descarga de Markdown falla
**Solución:**
- Verifica permisos de descarga en navegador
- Intenta con otro navegador
- Revisa que no haya errores en consola

---

## ✅ Resultados Esperados

Si todo funciona correctamente, debes ver:

### En Tab "🎯 Trading Plan":
✅ Briefing diario con 4 métricas  
✅ Recomendación completa expandible  
✅ Plan de trade O plan hipotético (según estado)  
✅ Gráfico con niveles correctamente coloreados  
✅ Descarga de Markdown funcional  

### En Tab "📊 Deep Dive":
✅ Breakdown de estrategias  
✅ Análisis de retroalimentación con datos reales  
✅ Gráficos rolling de tendencias  
✅ Métricas de backtest de 12 meses  
✅ Recomendaciones basadas en performance  

### Archivos Generados:
✅ `storage/decision_history.json` con ~9 decisiones  
✅ `storage/decision_outcomes.json` con ~9 outcomes  
✅ Briefing descargado en formato Markdown  

---

## 🎉 ¡Pruebas Completadas!

Si llegaste hasta aquí y todo funcionó correctamente:

**¡FELICITACIONES! 🎊**

Has probado exitosamente:
- ✅ Sistema completo One Market
- ✅ 3 mejoras nuevas implementadas
- ✅ Todas las funcionalidades core
- ✅ Integración UI + Backend
- ✅ Exportación y persistencia de datos

**El sistema está listo para uso en producción** (paper trading) o para continuar desarrollo hacia live trading.

---

## 📞 Siguiente Paso

¿Qué quieres hacer ahora?

1. **Usar el sistema diariamente** → Configura sincronización automática
2. **Mejorar estrategias** → Experimenta con parámetros en sidebar
3. **Agregar más funcionalidades** → Notificaciones, más símbolos, etc.
4. **Preparar para live trading** → Conectar exchange real (Epic 8)

---

**Happy Trading! 🚀📈**

