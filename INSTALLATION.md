# Guía de Instalación - One Market

## Instalación Básica (Sin vectorbt)

```bash
# Instalar dependencias core
pip install -r requirements.txt
```

**Nota**: La instalación básica NO incluye vectorbt (backtest usa modo simplificado).

---

## Instalación Completa (Con vectorbt)

### Opción 1: Pip (puede tener problemas en Windows)
```bash
pip install vectorbt
```

### Opción 2: Usar alternativas
Si vectorbt no se instala en tu sistema, el backtest funciona en **modo simplificado**:
- ✅ Todas las señales funcionan
- ✅ Monte Carlo funciona
- ✅ Métricas básicas funcionan
- ⚠️ Algunas métricas avanzadas limitadas

---

## Ejecutar Ejemplos en PowerShell

En Windows PowerShell, usar `.\` antes del comando:

```powershell
# Correcto ✅
.\run_example.bat examples\example_core_usage.py

# Incorrecto ❌
run_example.bat examples\example_core_usage.py
```

### O usar Python directamente:
```powershell
$env:PYTHONPATH="$PWD"
python examples\example_core_usage.py
```

---

## Verificar Instalación

```bash
# Ejecutar health check
python scripts/health_check.py

# Ejecutar tests básicos
python -m pytest tests/test_core_timeframes.py -v
```

---

## Problemas Comunes

### pandas-ta no se instala
**Solución**: Ya removido de requirements.txt (no crítico)

### vectorbt no se instala
**Solución**: El sistema funciona en modo simplificado sin problemas

### "Module not found"
**Solución**: Configurar PYTHONPATH
```powershell
$env:PYTHONPATH="$PWD"
```

### Scripts .bat no funcionan en PowerShell
**Solución**: Usar `.\script.bat` en vez de `script.bat`

---

## Instalación Mínima

Si tienes problemas, instala solo lo esencial:

```bash
pip install pandas numpy pyarrow ccxt pydantic pydantic-settings scikit-learn scipy
```

Esto es suficiente para:
- ✅ Fetch de datos
- ✅ Storage
- ✅ Indicadores y señales
- ✅ Combinación (incluyendo ML)
- ✅ Backtest simplificado
- ✅ Monte Carlo

---

## Dependencias Opcionales

| Package | Necesario para | Alternativa |
|---------|----------------|-------------|
| vectorbt | Backtest avanzado | Modo simplificado ✅ |
| pandas-ta | Indicadores extras | Implementación propia ✅ |
| streamlit | UI Dashboard | Epic 5 (futuro) |
| fastapi | REST API | Epic 4 (futuro) |

---

**Todo lo implementado en Epic 1-3 funciona sin vectorbt** ✅

