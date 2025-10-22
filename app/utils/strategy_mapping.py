"""
Strategy name mapping for One Market platform.

This module provides mapping between user-friendly strategy names
and internal technical names.
"""
from typing import Dict, List, Optional

# Mapping from user-friendly names to technical names
STRATEGY_NAME_MAPPING: Dict[str, str] = {
    "MA Crossover": "ma_crossover",
    "RSI Regime Pullback": "rsi_regime_pullback", 
    "Trend Following EMA": "trend_following_ema",
    "Donchian Breakout": "donchian_breakout_adx",
    "MACD Histogram": "macd_histogram_atr_filter",
    "Mean Reversion": "mean_reversion",
    "ATR Channel Breakout": "atr_channel_breakout_volume",
    "VWAP Z-Score Reversion": "vwap_zscore_reversion",
    "EMA Triple Momentum": "ema_triple_momentum"
}

# Reverse mapping from technical names to user-friendly names
TECHNICAL_TO_FRIENDLY: Dict[str, str] = {
    v: k for k, v in STRATEGY_NAME_MAPPING.items()
}

def get_technical_name(friendly_name: str) -> Optional[str]:
    """Get technical name from friendly name.
    
    Args:
        friendly_name: User-friendly strategy name
        
    Returns:
        Technical name or None if not found
    """
    return STRATEGY_NAME_MAPPING.get(friendly_name)

def get_friendly_name(technical_name: str) -> Optional[str]:
    """Get friendly name from technical name.
    
    Args:
        technical_name: Technical strategy name
        
    Returns:
        Friendly name or None if not found
    """
    return TECHNICAL_TO_FRIENDLY.get(technical_name)

def get_available_strategies() -> List[str]:
    """Get list of available friendly strategy names.
    
    Returns:
        List of friendly strategy names
    """
    return list(STRATEGY_NAME_MAPPING.keys())

def get_available_technical_strategies() -> List[str]:
    """Get list of available technical strategy names.
    
    Returns:
        List of technical strategy names
    """
    return list(STRATEGY_NAME_MAPPING.values())

def normalize_strategy_name(strategy_name: str) -> str:
    """Normalize strategy name to technical format.
    
    Args:
        strategy_name: Strategy name (friendly or technical)
        
    Returns:
        Technical strategy name
    """
    # If it's already a technical name, return as is
    if strategy_name in TECHNICAL_TO_FRIENDLY:
        return strategy_name
    
    # Try to map from friendly name
    technical_name = get_technical_name(strategy_name)
    if technical_name:
        return technical_name
    
    # If not found, return original (might be a new strategy)
    return strategy_name

