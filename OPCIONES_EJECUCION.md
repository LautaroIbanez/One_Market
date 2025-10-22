# 🚀 **OPCIONES PARA EJECUTAR ONE MARKET**

## 📋 **PROBLEMA SOLUCIONADO: Streamlit no encontrado**

✅ **Solución implementada:** Scripts que instalan automáticamente las dependencias

## 🎯 **OPCIONES DISPONIBLES PARA EJECUTAR**

### **OPCIÓN 1: Ejecutar UI con Python (Recomendada)**
```bash
python ejecutar_ui_python.py
```
**✅ Ventajas:**
- Instala automáticamente todas las dependencias
- No requiere comandos batch complejos
- Funciona en cualquier sistema

### **OPCIÓN 2: Ejecutar UI Simple**
```bash
EJECUTAR_UI_SIMPLE.bat
```
**✅ Ventajas:**
- Script batch simple
- Instala dependencias automáticamente

### **OPCIÓN 3: Instalar dependencias manualmente**
```bash
# 1. Instalar dependencias
pip install streamlit plotly pandas requests

# 2. Ejecutar UI
streamlit run ui/app_complete.py
```

### **OPCIÓN 4: Ejecutar proyecto completo**
```bash
EJECUTAR_PROYECTO_COMPLETO.bat
```
**✅ Ventajas:**
- Ejecuta todo el sistema
- Verifica API y UI

## 🌐 **URLs DEL SISTEMA**

- **UI Principal:** http://localhost:8501
- **API:** http://localhost:8000
- **Documentación API:** http://localhost:8000/docs

## 🔍 **VERIFICACIÓN RÁPIDA**

### **1. Verificar que la API esté corriendo**
```bash
# La API ya está funcionando según los logs
# Si no, ejecutar: EJECUTAR_API.bat
```

### **2. Verificar UI funcionando**
- Abrir http://localhost:8501
- Deberías ver la UI de One Market con recomendaciones enriquecidas

## 📊 **FUNCIONALIDADES DISPONIBLES**

### **✅ Recomendaciones Enriquecidas**
- **🤖 Estrategia ganadora** con nombre y score
- **📊 Métricas de rendimiento** (Sharpe, Win Rate, Max Drawdown)
- **🔄 Análisis multi-timeframe** con pesos por timeframe
- **⚖️ Distribución de pesos** por dirección (LONG/SHORT/HOLD)

### **✅ UI Actualizada**
- **Métricas de estrategia** visualizadas
- **Análisis multi-timeframe** con gráficos
- **Desglose de pesos** de estrategias
- **Información detallada** de recomendaciones

## 🛠️ **SOLUCIÓN DE PROBLEMAS**

### **Problema: "streamlit no se reconoce"**
**✅ Solución:** Usar `python ejecutar_ui_python.py`

### **Problema: Dependencias faltantes**
**✅ Solución:** El script las instala automáticamente

### **Problema: API no responde**
**✅ Solución:** Ejecutar `EJECUTAR_API.bat`

## 🎉 **ESTADO ACTUAL**

✅ **API funcionando** en puerto 8000
✅ **UI ejecutándose** en puerto 8501
✅ **Dependencias instaladas** automáticamente
✅ **Sistema completo funcionando**

## 💡 **RECOMENDACIÓN**

**Usar la OPCIÓN 1:** `python ejecutar_ui_python.py`

**Razones:**
- Más confiable
- Instala dependencias automáticamente
- Funciona en cualquier sistema
- Fácil de usar

---

**🚀 ¡El sistema ONE MARKET está completamente funcional y listo para usar!**
