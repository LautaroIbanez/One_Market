# ⚡ Test Rápido de 5 Minutos

## Paso 1: Iniciar (30 seg)
```powershell
.\EJECUTAR_UI.bat
```
✅ Espera a que se abra el navegador en http://localhost:8501

---

## Paso 2: Tab Trading Plan (2 min)

### Acción 1: Revisar Indicador de Confianza
- ¿Ves un emoji de semáforo? 🟢/🟡/🔴
- ¿Dice "ALTA", "MEDIA" o "BAJA"?
- ¿Muestra un número como "(85/100)"?

**✅ SI** → Continúa  
**❌ NO** → Revisa consola del navegador (F12)

### Acción 2: Revisar Señal
- ¿Muestra 4 métricas (Dirección, Confianza, Precio, Estado)?
- ¿Los valores son números (no "NaN" o error)?

**✅ SI** → Continúa  
**❌ NO** → Verifica que hay datos en storage/

### Acción 3: Scroll hasta el Gráfico
- ¿Ves velas (candlesticks)?
- ¿Ves líneas de colores (azul, rojo, verde)?
- ¿Puedes hacer zoom con la rueda del mouse?

**✅ SI** → Continúa  
**❌ NO** → Revisa la terminal de Streamlit

---

## Paso 3: Tab Deep Dive (2 min)

### Acción 4: Cambiar al Tab "📊 Deep Dive"
- Click en la pestaña "Deep Dive"
- ¿Cambia el contenido inmediatamente?

**✅ SI** → Continúa  
**❌ NO** → Refresca la página (F5)

### Acción 5: Scroll hacia Abajo
- ¿Ves "🧭 Análisis Multi-Horizonte" con 3 columnas?
- ¿Ves "📊 Métricas de Performance" con 6 números?
- ¿Ves 2 gráficos (Equity Curve azul y Drawdown rojo)?

**✅ SI** → Continúa  
**❌ NO** → Verifica que combined signals se generan

### Acción 6: Abrir Expander "📜 Trades Históricos"
- Click en el expander
- ¿Se abre y muestra "💡 Próximamente"?

**✅ SI** → ¡TODO FUNCIONA! 🎉  
**❌ NO** → Revisa logs de Streamlit

---

## Paso 4: Sidebar (30 seg)

### Acción 7: Cambiar Timeframe
- En el sidebar izquierdo
- Cambia de "1h" a "4h"
- ¿Se recarga el contenido?
- ¿Los números cambian?

**✅ SI** → ¡PERFECTO! 🎉  
**❌ NO** → Click en "🔄 Refresh Data"

---

## ✅ Resultado Final

Si llegaste hasta aquí sin problemas:
- ✅ La UI v2.0 funciona correctamente
- ✅ Ambos tabs están operativos
- ✅ Los gráficos se renderizan
- ✅ Las métricas se calculan
- ✅ La navegación es fluida

**🎉 ¡Felicitaciones! One Market UI v2.0 está listo para usar.**

---

## ❌ Si algo falló

### Error: "No hay datos disponibles"
```powershell
python examples/example_fetch_data.py
```
Espera 1-2 minutos, luego refresca la UI.

### Error: Gráficos no se ven
1. Abre consola del navegador (F12)
2. Busca errores en rojo
3. Si dice "plotly", ejecuta: `pip install plotly`

### Error: Números son "NaN"
1. Verifica que hay al menos 100 barras de datos
2. Click en "🔄 Refresh Data" en sidebar
3. Cambia a timeframe "1d" (más datos disponibles)

### Error: App no inicia
1. Verifica que Streamlit está instalado: `pip install streamlit`
2. Prueba otro puerto: `streamlit run ui/app.py --server.port 8502`
3. Cierra otras instancias de Streamlit

---

## 📞 Debug Avanzado

Si necesitas más información:

```powershell
# Ver logs detallados
streamlit run ui/app.py --logger.level=debug

# Verificar datos disponibles
dir storage\symbol=BTC-USDT\

# Verificar que tests pasan
python -m pytest tests/test_ui_smoke.py -v
```

**Tiempo total del test: ~5 minutos** ⏱️

