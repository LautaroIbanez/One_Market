# 🧪 Guía Completa de Pruebas - One Market UI v2.0

## 🚀 Cómo Ejecutar

### Opción 1: Usando el Script BAT (Recomendado)
```
Doble clic en: EJECUTAR_UI.bat
```

### Opción 2: Desde PowerShell
```powershell
streamlit run ui/app.py
```

### Opción 3: Desde CMD
```cmd
streamlit run ui/app.py
```

La aplicación se abrirá automáticamente en tu navegador en: **http://localhost:8501**

---

## ✅ Checklist de Pruebas

### 🎯 TAB 1: Trading Plan (Vista Rápida)

#### 1. Indicador de Confianza
- [ ] Se muestra el semáforo (🟢 Alta / 🟡 Media / 🔴 Baja)
- [ ] Aparece el nivel de confianza (ALTA/MEDIA/BAJA)
- [ ] Se muestra la descripción con score y métricas
- [ ] Los colores corresponden al nivel (verde/amarillo/rojo)

#### 2. Señal del Día
- [ ] Se muestra la dirección (LONG 🟢 / SHORT 🔴 / FLAT ⚪)
- [ ] Aparece el porcentaje de confianza de la señal
- [ ] Se muestra el precio actual del mercado
- [ ] El estado indica EJECUTAR ✅ o SKIP ⏸️

#### 3. Plan de Trade (si hay señal ejecutable)
- [ ] **Sección Entrada**:
  - Precio de Entrada visible
  - Rango de Entrada (si aplica)
  - Cantidad calculada
  - Valor Nocional
  
- [ ] **Sección Gestión de Riesgo**:
  - Stop Loss definido
  - Take Profit definido
  - R/R Ratio calculado
  - Riesgo en dólares

- [ ] **Estado de Ventana**:
  - Indica si estamos en Ventana A o B
  - Muestra mensaje si estamos fuera de horario

- [ ] **Botones de Acción**:
  - "📄 Ejecutar Paper Trade" presente
  - "💾 Guardar Plan" presente
  - Los botones responden al click

#### 4. Gráfico de Precio
- [ ] Se renderiza el gráfico de velas
- [ ] Línea de entrada (azul, dash) visible
- [ ] Línea de SL (rojo, dot) visible
- [ ] Línea de TP (verde, dot) visible
- [ ] Zona de entry band (rectángulo azul claro) visible
- [ ] Se puede hacer zoom y pan en el gráfico
- [ ] Hover muestra información de cada vela

---

### 📊 TAB 2: Deep Dive (Análisis Detallado)

#### 1. Análisis Multi-Horizonte
- [ ] **Columna Corto Plazo**:
  - Señal (LONG/SHORT/FLAT)
  - Timing de Entrada
  - Volatilidad
  - Riesgo Recomendado

- [ ] **Columna Medio Plazo**:
  - Tendencia (BULLISH/BEARISH/NEUTRAL)
  - Posición EMA200
  - Filtro
  - RSI Semanal

- [ ] **Columna Largo Plazo**:
  - Régimen (BULL/BEAR/NEUTRAL)
  - Vol Régimen
  - Exposición Recomendada
  - Probabilidad de Régimen

#### 2. Consenso
- [ ] Dirección consensuada (LONG/SHORT/NEUTRAL)
- [ ] Confianza Global (porcentaje)
- [ ] Riesgo Final Recomendado (porcentaje)

#### 3. Métricas de Performance
- [ ] **6 Métricas principales visibles**:
  - CAGR
  - Sharpe
  - Calmar
  - Max DD
  - Win Rate
  - Profit Factor

- [ ] **Gráfico de Equity Curve**:
  - Se renderiza correctamente
  - Muestra evolución del capital
  - Eje X muestra fechas
  - Eje Y muestra valores en dólares
  - Hover funciona

- [ ] **Gráfico de Drawdown**:
  - Se renderiza correctamente
  - Área roja rellenada hasta cero
  - Muestra drawdowns históricos
  - Hover funciona

#### 4. Desglose por Estrategia
- [ ] **Señales Individuales**:
  - MA Crossover (🟢/🔴/⚪)
  - RSI Regime (🟢/🔴/⚪)
  - Triple EMA (🟢/🔴/⚪)

- [ ] **Tabla de Pesos**:
  - Muestra estrategia y peso
  - Formato tabla legible

#### 5. Expanders
- [ ] **📜 Trades Históricos**:
  - Expander se abre/cierra
  - Mensaje "Próximamente" visible
  - Lista de funcionalidades futuras visible

- [ ] **⚙️ Parámetros de Estrategias**:
  - Expander se abre/cierra
  - Parámetros de MA Crossover visibles
  - Parámetros de RSI Regime visibles
  - Parámetros de Triple EMA visibles

- [ ] **ℹ️ Estado de Datos**:
  - Expander se abre/cierra
  - Barras Cargadas (número)
  - Última Actualización (fecha/hora)
  - Antigüedad (en minutos)
  - Metadata JSON visible (si disponible)

---

### ⚙️ SIDEBAR (Compartido entre tabs)

#### Configuración
- [ ] **Selección de Símbolo**:
  - Dropdown funciona
  - Muestra símbolos disponibles (BTC-USDT, etc.)

- [ ] **Selección de Timeframe**:
  - Dropdown funciona
  - Opciones: 15m, 1h, 4h, 1d

- [ ] **Modo de Trading**:
  - Radio buttons funcionan
  - Opciones: Paper Trading, Live Trading

#### Risk Management
- [ ] **Risk per Trade**:
  - Slider de 0.5% a 5.0%
  - Valor por defecto: 2.0%
  - Se actualiza visualmente

- [ ] **Capital**:
  - Input numérico funciona
  - Valor por defecto: $100,000
  - Se puede modificar

- [ ] **Target R/R Ratio**:
  - Slider de 1.0 a 5.0
  - Valor por defecto: 1.5
  - Se actualiza visualmente

#### TP/SL Configuration
- [ ] **TP/SL Method**:
  - Dropdown funciona
  - Opciones: ATR, Swing, Hybrid

- [ ] **ATR Multipliers**:
  - ATR Multiplier SL (1.0-5.0, default 2.0)
  - ATR Multiplier TP (1.0-10.0, default 3.0)
  - Ambos inputs funcionan

- [ ] **Botón Refresh**:
  - Botón "🔄 Refresh Data" presente
  - Click recarga los datos

---

### 🔄 Interactividad

#### Navegación entre Tabs
- [ ] Click en "🎯 Trading Plan" cambia al tab 1
- [ ] Click en "📊 Deep Dive" cambia al tab 2
- [ ] Transición es instantánea (sin delay notable)
- [ ] Contenido de cada tab se preserva al cambiar

#### Cambios en Sidebar
- [ ] Cambiar símbolo recarga ambos tabs
- [ ] Cambiar timeframe recarga ambos tabs
- [ ] Cambiar risk % actualiza cálculos
- [ ] Cambiar capital actualiza tamaños de posición

#### Performance
- [ ] Primera carga: 5-10 segundos (aceptable)
- [ ] Cambios posteriores: 1-2 segundos (cache funciona)
- [ ] Gráficos se renderizan sin lag
- [ ] No hay errores en consola del navegador (F12)

---

### 🐛 Troubleshooting

#### Si ves "No hay datos disponibles"
```powershell
python examples/example_fetch_data.py
```

#### Si hay error de módulo faltante
```powershell
pip install -r requirements.txt
```

#### Si el puerto 8501 está ocupado
```powershell
streamlit run ui/app.py --server.port 8502
```

#### Para ver logs detallados
En la terminal donde corriste Streamlit verás:
- Warnings en amarillo
- Errors en rojo
- Info en blanco

---

## 📸 Capturas Esperadas

### Tab 1: Trading Plan
```
┌────────────────────────────────────────┐
│  📈 Confianza del Sistema              │
│  🟢  ALTA  "Confianza alta (85/100)..."│
├────────────────────────────────────────┤
│  📍 Señal de Hoy                       │
│  🟢 LONG  |  75%  |  $95,234  |  ✅    │
├────────────────────────────────────────┤
│  💰 Plan de Trade                      │
│  📍 Entrada    |  🛡️ Gestión de Riesgo │
│  $95,100       |  SL: $94,000          │
│  ±0.15%        |  TP: $97,500          │
│                |  R/R: 2.4             │
├────────────────────────────────────────┤
│  📈 Gráfico de Precio                  │
│  [Candlestick chart con niveles]      │
└────────────────────────────────────────┘
```

### Tab 2: Deep Dive
```
┌────────────────────────────────────────┐
│  🧭 Análisis Multi-Horizonte           │
│  📊 Corto | 📈 Medio | 🌍 Largo       │
├────────────────────────────────────────┤
│  📊 Métricas de Performance            │
│  CAGR | Sharpe | Calmar | DD | WR | PF│
│  [Equity Curve]                        │
│  [Drawdown Chart]                      │
├────────────────────────────────────────┤
│  🔍 Desglose por Estrategia            │
│  MA: 🟢 | RSI: 🔴 | EMA: 🟢           │
└────────────────────────────────────────┘
```

---

## ✅ Criterios de Éxito

La UI v2.0 está funcionando correctamente si:

1. ✅ Ambos tabs se cargan sin errores
2. ✅ El indicador de confianza muestra correctamente
3. ✅ Los gráficos se renderizan (precio, equity, drawdown)
4. ✅ Las métricas muestran valores numéricos (no NaN o error)
5. ✅ Los botones responden a clicks
6. ✅ El sidebar afecta el contenido de ambos tabs
7. ✅ No hay errores en la consola del navegador
8. ✅ La navegación entre tabs es fluida

---

## 🎉 Resultado Esperado

Si todo funciona correctamente, deberías ver:
- **Tab 1** con vista minimalista y accionable
- **Tab 2** con métricas detalladas y gráficos
- **Transición suave** entre tabs
- **Sin errores** en consola
- **Carga rápida** gracias al cache

---

## 📞 Soporte

Si encuentras algún problema:
1. Revisa la terminal donde corriste Streamlit
2. Abre la consola del navegador (F12)
3. Verifica que hay datos en `storage/symbol=BTC-USDT/`
4. Intenta refrescar con el botón del sidebar

**¡Disfruta de One Market UI v2.0!** 🚀

