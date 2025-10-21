"""
UI Text Dictionary - One Market Dashboard
Coloquial explanations and tooltips for trading parameters.
"""

# Tooltips and explanations
TOOLTIPS = {
    "risk_pct": {
        "title": "¿Qué es el Riesgo por Trade?",
        "description": "Es el porcentaje de tu capital que estás dispuesto a perder en una sola operación. Por ejemplo, si tienes $10,000 y arriesgas 2%, perderás máximo $200 si el trade sale mal.",
        "recommended": "1-2% para principiantes, 3-5% para traders experimentados"
    },
    
    "rr_target": {
        "title": "¿Qué es el Ratio Riesgo/Recompensa (R/R)?",
        "description": "Es cuánto esperas ganar por cada dólar que arriesgas. Si R/R = 2, significa que por cada $1 que arriesgas, esperas ganar $2.",
        "recommended": "1.5-3.0 es un buen balance. Menos de 1.5 es muy conservador."
    },
    
    "tpsl_method": {
        "title": "¿Qué método usar para Stop Loss y Take Profit?",
        "description": "ATR se adapta a la volatilidad del mercado, Swing usa niveles técnicos, Hybrid combina ambos.",
        "recommended": "ATR para principiantes (más automático)"
    },
    
    "atr_multiplier": {
        "title": "¿Qué son los multiplicadores ATR?",
        "description": "ATR mide la volatilidad. Multiplicador 2.0 significa que tu stop estará a 2 veces la volatilidad promedio del mercado.",
        "recommended": "SL: 2.0, TP: 3.0 (balance conservador)"
    },
    
    "capital": {
        "title": "¿Cuánto capital usar?",
        "description": "El dinero total que tienes disponible para trading. No uses dinero que necesites para gastos diarios.",
        "recommended": "Solo dinero que puedas permitirte perder"
    },
    
    "timeframe": {
        "title": "¿Qué timeframe elegir?",
        "description": "15m = más señales pero más ruido, 1h = balance ideal, 4h = menos señales pero más confiables, 1d = swing trading.",
        "recommended": "1h para principiantes (balance perfecto)"
    }
}

# Presets for different user types
PRESETS = {
    "conservador": {
        "name": "🛡️ Conservador",
        "description": "Para principiantes y traders de bajo riesgo",
        "risk_pct": 1.0,
        "rr_target": 1.5,
        "tpsl_method": "ATR",
        "atr_multiplier_sl": 2.0,
        "atr_multiplier_tp": 3.0,
        "timeframe": "1h"
    },
    
    "moderado": {
        "name": "⚖️ Moderado", 
        "description": "Balance entre riesgo y oportunidad",
        "risk_pct": 2.0,
        "rr_target": 2.0,
        "tpsl_method": "ATR",
        "atr_multiplier_sl": 2.0,
        "atr_multiplier_tp": 4.0,
        "timeframe": "1h"
    },
    
    "agresivo": {
        "name": "🚀 Agresivo",
        "description": "Para traders experimentados con alta tolerancia al riesgo",
        "risk_pct": 3.0,
        "rr_target": 2.5,
        "tpsl_method": "Hybrid",
        "atr_multiplier_sl": 1.5,
        "atr_multiplier_tp": 3.75,
        "timeframe": "15m"
    }
}

# Section descriptions
SECTIONS = {
    "basico": {
        "title": "🎯 Configuración Básica",
        "description": "Parámetros esenciales para empezar a tradear"
    },
    
    "avanzado": {
        "title": "⚙️ Configuración Avanzada", 
        "description": "Ajustes técnicos para traders experimentados"
    },
    
    "riesgo": {
        "title": "🛡️ Gestión de Riesgo",
        "description": "Controla cuánto dinero arriesgas en cada operación"
    }
}

# Help messages
HELP_MESSAGES = {
    "modo_automatico": "El modo automático usa configuraciones probadas y seguras. Solo cambia si sabes lo que haces.",
    "personalizar": "⚠️ Solo para traders experimentados. Configuraciones incorrectas pueden causar pérdidas grandes.",
    "preset_recomendado": "💡 Recomendamos empezar con 'Moderado' y ajustar según tu experiencia."
}

# Status messages
STATUS_MESSAGES = {
    "fuera_horario": "⏰ Fuera de horario de trading. Las ventanas son 09:00-12:30 y 14:00-17:00 (UTC-3)",
    "sin_senal": "😴 No hay señales activas en este momento",
    "senal_activa": "🎯 Señal activa - Revisa los niveles de entrada",
    "modo_paper": "📝 Modo Paper Trading - No se ejecutarán operaciones reales",
    "modo_live": "⚠️ Modo Live Trading - Se ejecutarán operaciones reales"
}



