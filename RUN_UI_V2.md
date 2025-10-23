# 🚀 Ejecutar One Market UI v2.0

## Orden de Arranque Correcto

### 1. Iniciar Backend API (Requerido)
```powershell
uvicorn main:app --reload --port 8000
```

### 2. Verificar que la API esté funcionando
```powershell
curl http://localhost:8000/health
```
Debería devolver: `{"status": "healthy"}`

### 3. Iniciar UI (En terminal separado)
```powershell
streamlit run ui/app.py
```

## Comando Rápido (Solo si ya tienes la API corriendo)

```powershell
streamlit run ui/app.py
```

## Verificación Visual - Checklist

### Tab 1: Trading Plan ✓
- [ ] Indicador de confianza muestra semáforo (🟢/🟡/🔴)
- [ ] Señal del día con 4 métricas (Dirección, Confianza, Precio, Estado)
- [ ] Plan de trade con entrada, SL, TP visible
- [ ] Gráfico de precio con niveles marcados
- [ ] Botones de acción funcionan

### Tab 2: Deep Dive ✓
- [ ] Análisis multi-horizonte muestra 3 columnas
- [ ] Métricas de performance (6 métricas principales)
- [ ] Gráfico de equity curve se renderiza
- [ ] Gráfico de drawdown se renderiza
- [ ] Desglose por estrategia muestra 3 estrategias
- [ ] Expanders se pueden abrir/cerrar

### General ✓
- [ ] Sidebar permite cambiar símbolo y timeframe
- [ ] Cambio entre tabs es instantáneo
- [ ] No hay errores en consola
- [ ] Cache funciona (segundo load es más rápido)

## Troubleshooting

### Error: "Backend Not Available" / "❌ Backend Not Available"
**Solución**: Asegúrate de que la API esté corriendo primero
```powershell
# Terminal 1: Iniciar API
uvicorn main:app --reload --port 8000

# Terminal 2: Iniciar UI
streamlit run ui/app.py
```

### Error: "No hay datos disponibles"
**Solución**: Ejecutar primero el script de fetch de datos
```powershell
python examples/example_fetch_data.py
```

### Error: "ModuleNotFoundError"
**Solución**: Verificar que todas las dependencias estén instaladas
```powershell
pip install -r requirements.txt
```

### Error: "Port 8501 already in use"
**Solución**: Cerrar otras instancias de Streamlit o usar otro puerto
```powershell
streamlit run ui/app.py --server.port 8502
```

### Error: "Connection refused" en la UI
**Solución**: Verificar que la API esté corriendo en el puerto correcto
```powershell
# Verificar que la API esté corriendo
curl http://localhost:8000/health

# Si no responde, reiniciar la API
uvicorn main:app --reload --port 8000
```

## Acceso

Una vez iniciado, abrir en navegador:
- **URL**: http://localhost:8501
- **Browser recomendado**: Chrome, Edge, Firefox

## Notas

- El primer load puede tardar 5-10 segundos mientras carga datos
- El cache TTL es de 5 minutos
- Para refrescar datos, usar botón "🔄 Refresh Data" en sidebar
- Modo Paper Trading está activo por defecto

¡Disfruta de One Market UI v2.0! 🎉

