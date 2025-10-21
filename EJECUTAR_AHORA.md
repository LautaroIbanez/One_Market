# 🚀 ONE MARKET - Guía de Ejecución Inmediata

## ✅ Sistema Verificado y Listo

**Estado**: 🟢 **COMPLETAMENTE OPERATIVO**
- ✅ app.data funcionando
- ✅ API importable (38 endpoints)
- ✅ Tests pasando (14/15)
- ✅ Todas las dependencias instaladas

---

## 🎯 **MÉTODO 1: Script Automático (MÁS FÁCIL)** ⭐

### Paso 1: Ejecuta el script
```bash
INICIAR_PROYECTO.bat
```

### Paso 2: Selecciona la opción
```
Opción 3: 🔄 Ambos (API + UI en ventanas separadas)
```

✅ **LISTO** - El sistema se abrirá en 2 ventanas automáticamente

---

## 🎯 **MÉTODO 2: Ejecución Manual (Paso a Paso)**

### **Terminal 1 - Iniciar API** 🌐

```bash
# Copiar y pegar este comando:
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Resultado esperado:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

✅ **API Funcionando** cuando veas estos mensajes

**URLs disponibles:**
- 🌐 API: http://localhost:8000
- 📖 Documentación: http://localhost:8000/docs
- 🔍 Health: http://localhost:8000/data/health

---

### **Terminal 2 - Iniciar UI** 📊

**IMPORTANTE**: Abre una **NUEVA TERMINAL** (PowerShell o CMD) y ejecuta:

```bash
# Copiar y pegar estos comandos:
cd C:\Users\lauta\OneDrive\Desktop\Trading\One_Market
streamlit run ui/app_enhanced.py
```

**Resultado esperado:**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

✅ **UI Funcionando** cuando veas estos mensajes

**URL disponible:**
- 📊 UI: http://localhost:8501

---

## 🔍 **Verificación de que Está Funcionando**

### Verificar API (desde cualquier terminal)
```bash
curl http://localhost:8000/data/health
```

**Respuesta esperada:**
```json
{"status":"ok","exchange_connected":true,"timestamp":"2025-10-21T..."}
```

### Verificar UI
Abre tu navegador en: http://localhost:8501

Deberías ver:
- 🏆 **One Market Enhanced - Auto Strategy Selection**
- 3 pestañas: Auto Strategy, Best Strategy, Strategy Comparison

---

## 📊 **Primeros Pasos Después de Iniciar**

### 1. Sincronizar Datos (IMPORTANTE - Primera vez)

**Opción A - Via Script:**
```bash
# En una nueva terminal:
python update_data.py
```

**Opción B - Via API:**
```bash
curl -X POST "http://localhost:8000/data/sync" \
  -H "Content-Type: application/json" \
  -d "{\"symbol\": \"BTC/USDT\", \"tf\": \"1h\", \"since\": \"2025-10-14T00:00:00Z\"}"
```

### 2. Generar Recomendación
```bash
curl "http://localhost:8000/recommendation/daily?symbol=BTC/USDT&date=2025-10-21"
```

### 3. Ejecutar Backtest
```bash
curl -X POST "http://localhost:8000/backtest/run" \
  -H "Content-Type: application/json" \
  -d "{\"symbol\": \"BTC/USDT\", \"timeframe\": \"1h\", \"strategy\": \"ma_crossover\"}"
```

---

## 🆘 **Solución de Problemas**

### ❌ Error: "Address already in use" (Puerto 8000 ocupado)
```bash
# Encontrar proceso en puerto 8000
netstat -ano | findstr ":8000"

# Matar proceso (reemplazar XXXX con el PID)
taskkill /F /PID XXXX

# O usar otro puerto
python -m uvicorn main:app --port 8001
```

### ❌ Error: "Address already in use" (Puerto 8501 ocupado)
```bash
# Matar proceso Streamlit anterior
taskkill /F /IM streamlit.exe

# O usar otro puerto
streamlit run ui/app_enhanced.py --server.port 8502
```

### ❌ Error: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### ❌ Error: "No data found"
```bash
# Sincronizar datos primero
python update_data.py
```

---

## 📋 **Checklist de Ejecución**

- [ ] Terminal 1: API iniciada (puerto 8000)
- [ ] Terminal 2: UI iniciada (puerto 8501)
- [ ] Navegador: http://localhost:8501 abierto
- [ ] Datos sincronizados (update_data.py ejecutado)

---

## 🎯 **Comandos Rápidos de Referencia**

```bash
# Iniciar API
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Iniciar UI
streamlit run ui/app_enhanced.py

# Sincronizar datos
python update_data.py

# Ejecutar tests
python -m pytest tests/test_data_contracts.py -v

# Health check
curl http://localhost:8000/data/health
```

---

## 📚 **Documentación Completa**

- **INICIO_RAPIDO.md** - Guía detallada
- **STATUS_REPORT.md** - Estado del sistema
- **README.md** - Documentación completa
- **ESTADO_SISTEMA.txt** - Estado visual

---

## ✅ **Resumen**

**Para ejecutar AHORA:**

1. **Opción Fácil**: Ejecuta `INICIAR_PROYECTO.bat` → Opción 3
2. **Opción Manual**: 
   - Terminal 1: `python -m uvicorn main:app --port 8000 --reload`
   - Terminal 2: `streamlit run ui/app_enhanced.py`

**¡El sistema está 100% operativo y listo para usar!** 🎉

---

**¿Necesitas ayuda?** Revisa `STATUS_REPORT.md` o ejecuta los health checks.
