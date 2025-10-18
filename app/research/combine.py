"""Signal combination and blending methods.

This module provides methods to combine multiple trading signals into
a single consensus signal using various weighting schemes.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')


class CombinedSignal(BaseModel):
    """Combined signal output."""
    
    signal: pd.Series = Field(..., description="Combined signal: 1 (long), -1 (short), 0 (flat)")
    confidence: Optional[pd.Series] = Field(None, description="Signal confidence (0-1)")
    weights: Dict[str, float] = Field(default_factory=dict, description="Strategy weights used")
    metadata: Dict[str, any] = Field(default_factory=dict, description="Combination metadata")
    
    class Config:
        arbitrary_types_allowed = True


def simple_average(
    signals: Dict[str, pd.Series],
    threshold: float = 0.0
) -> CombinedSignal:
    """Combine signals using simple average.
    
    Each signal gets equal weight. Final signal is the sign of the average.
    
    Args:
        signals: Dictionary of {strategy_name: signal_series}
        threshold: Threshold for signal generation (default: 0)
        
    Returns:
        CombinedSignal with combined signal
    """
    if not signals:
        raise ValueError("No signals provided")
    
    # Convert to DataFrame
    signal_df = pd.DataFrame(signals)
    
    # Calculate simple average
    avg_signal = signal_df.mean(axis=1)
    
    # Generate discrete signal
    combined = pd.Series(0, index=avg_signal.index)
    combined[avg_signal > threshold] = 1
    combined[avg_signal < -threshold] = -1
    
    # Confidence is absolute value of average
    confidence = abs(avg_signal) / len(signals)
    
    # Equal weights
    weights = {name: 1.0 / len(signals) for name in signals.keys()}
    
    return CombinedSignal(
        signal=combined,
        confidence=confidence,
        weights=weights,
        metadata={
            "method": "simple_average",
            "num_strategies": len(signals),
            "threshold": threshold
        }
    )


def weighted_average(
    signals: Dict[str, pd.Series],
    weights: Dict[str, float],
    threshold: float = 0.0
) -> CombinedSignal:
    """Combine signals using custom weights.
    
    Args:
        signals: Dictionary of {strategy_name: signal_series}
        weights: Dictionary of {strategy_name: weight}
        threshold: Threshold for signal generation
        
    Returns:
        CombinedSignal with combined signal
    """
    if not signals:
        raise ValueError("No signals provided")
    
    if set(signals.keys()) != set(weights.keys()):
        raise ValueError("Signals and weights must have same keys")
    
    # Normalize weights to sum to 1
    total_weight = sum(weights.values())
    normalized_weights = {k: v / total_weight for k, v in weights.items()}
    
    # Convert to DataFrame
    signal_df = pd.DataFrame(signals)
    
    # Apply weights
    weighted_signals = signal_df.copy()
    for col in weighted_signals.columns:
        weighted_signals[col] = weighted_signals[col] * normalized_weights[col]
    
    # Calculate weighted average
    avg_signal = weighted_signals.sum(axis=1)
    
    # Generate discrete signal
    combined = pd.Series(0, index=avg_signal.index)
    combined[avg_signal > threshold] = 1
    combined[avg_signal < -threshold] = -1
    
    # Confidence is absolute value of weighted average
    confidence = abs(avg_signal)
    
    return CombinedSignal(
        signal=combined,
        confidence=confidence,
        weights=normalized_weights,
        metadata={
            "method": "weighted_average",
            "num_strategies": len(signals),
            "threshold": threshold
        }
    )


def sharpe_weighted(
    signals: Dict[str, pd.Series],
    returns: pd.Series,
    lookback_period: int = 90,
    min_periods: int = 30,
    threshold: float = 0.0
) -> CombinedSignal:
    """Combine signals weighted by rolling Sharpe ratio.
    
    Strategies with higher Sharpe ratios get higher weights.
    Weights are recalculated on a rolling basis.
    
    Args:
        signals: Dictionary of {strategy_name: signal_series}
        returns: Returns series for calculating strategy returns
        lookback_period: Rolling window for Sharpe calculation
        min_periods: Minimum periods for Sharpe calculation
        threshold: Threshold for signal generation
        
    Returns:
        CombinedSignal with combined signal
    """
    if not signals:
        raise ValueError("No signals provided")
    
    # Convert to DataFrame
    signal_df = pd.DataFrame(signals)
    
    # Calculate strategy returns (signal[t-1] * return[t])
    strategy_returns = {}
    for col in signal_df.columns:
        strategy_returns[col] = signal_df[col].shift(1) * returns
    
    returns_df = pd.DataFrame(strategy_returns)
    
    # Calculate rolling Sharpe for each strategy
    sharpe_ratios = {}
    for col in returns_df.columns:
        mean_ret = returns_df[col].rolling(window=lookback_period, min_periods=min_periods).mean()
        std_ret = returns_df[col].rolling(window=lookback_period, min_periods=min_periods).std()
        sharpe = mean_ret / std_ret
        sharpe_ratios[col] = sharpe.fillna(0)
    
    sharpe_df = pd.DataFrame(sharpe_ratios)
    
    # Clip negative Sharpe ratios to small positive value
    sharpe_df = sharpe_df.clip(lower=0.01)
    
    # Normalize to get weights (sum to 1 for each row)
    weights_df = sharpe_df.div(sharpe_df.sum(axis=1), axis=0)
    
    # Apply dynamic weights to signals
    weighted_signals = signal_df * weights_df
    
    # Calculate weighted average signal
    avg_signal = weighted_signals.sum(axis=1)
    
    # Generate discrete signal
    combined = pd.Series(0, index=avg_signal.index)
    combined[avg_signal > threshold] = 1
    combined[avg_signal < -threshold] = -1
    
    # Confidence is absolute value of weighted average
    confidence = abs(avg_signal)
    
    # Average weights over time for reporting
    avg_weights = weights_df.mean().to_dict()
    
    return CombinedSignal(
        signal=combined,
        confidence=confidence,
        weights=avg_weights,
        metadata={
            "method": "sharpe_weighted",
            "num_strategies": len(signals),
            "lookback_period": lookback_period,
            "threshold": threshold
        }
    )


def majority_vote(
    signals: Dict[str, pd.Series],
    min_agreement: float = 0.5
) -> CombinedSignal:
    """Combine signals using majority voting.
    
    Signal is generated only when minimum fraction of strategies agree.
    
    Args:
        signals: Dictionary of {strategy_name: signal_series}
        min_agreement: Minimum fraction of strategies that must agree (0-1)
        
    Returns:
        CombinedSignal with combined signal
    """
    if not signals:
        raise ValueError("No signals provided")
    
    # Convert to DataFrame
    signal_df = pd.DataFrame(signals)
    
    # Count votes for each direction
    num_long = (signal_df == 1).sum(axis=1)
    num_short = (signal_df == -1).sum(axis=1)
    num_strategies = len(signals)
    
    # Calculate agreement fractions
    long_agreement = num_long / num_strategies
    short_agreement = num_short / num_strategies
    
    # Generate signal based on minimum agreement
    combined = pd.Series(0, index=signal_df.index)
    combined[long_agreement >= min_agreement] = 1
    combined[short_agreement >= min_agreement] = -1
    
    # Confidence is the agreement fraction
    confidence = pd.Series(0.0, index=signal_df.index)
    confidence[combined == 1] = long_agreement[combined == 1]
    confidence[combined == -1] = short_agreement[combined == -1]
    
    # Equal weights
    weights = {name: 1.0 / len(signals) for name in signals.keys()}
    
    return CombinedSignal(
        signal=combined,
        confidence=confidence,
        weights=weights,
        metadata={
            "method": "majority_vote",
            "num_strategies": len(signals),
            "min_agreement": min_agreement
        }
    )


def logistic_model(
    signals: Dict[str, pd.Series],
    returns: pd.Series,
    features: Optional[pd.DataFrame] = None,
    train_period: int = 252,
    refit_frequency: int = 21,
    threshold: float = 0.5
) -> CombinedSignal:
    """Combine signals using logistic regression model.
    
    Trains a logistic model to predict profitable signals based on
    strategy signals and optional additional features.
    
    Args:
        signals: Dictionary of {strategy_name: signal_series}
        returns: Future returns series (for training)
        features: Optional additional features DataFrame
        train_period: Training window size
        refit_frequency: How often to refit model (in periods)
        threshold: Probability threshold for signal generation
        
    Returns:
        CombinedSignal with combined signal
    """
    if not signals:
        raise ValueError("No signals provided")
    
    # Convert signals to DataFrame
    signal_df = pd.DataFrame(signals)
    
    # Add additional features if provided
    if features is not None:
        X = pd.concat([signal_df, features], axis=1)
    else:
        X = signal_df.copy()
    
    # Create target: 1 if next return is positive, 0 otherwise
    future_returns = returns.shift(-1)
    y = (future_returns > 0).astype(int)
    
    # Initialize output
    predictions = pd.Series(np.nan, index=X.index)
    probabilities = pd.Series(np.nan, index=X.index)
    
    # Rolling window training and prediction
    for i in range(train_period, len(X), refit_frequency):
        # Define training window
        train_start = max(0, i - train_period)
        train_end = i
        
        # Training data
        X_train = X.iloc[train_start:train_end]
        y_train = y.iloc[train_start:train_end]
        
        # Remove NaN rows
        valid_idx = ~(X_train.isna().any(axis=1) | y_train.isna())
        X_train = X_train[valid_idx]
        y_train = y_train[valid_idx]
        
        if len(X_train) < 20:  # Need minimum data
            continue
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        
        # Train model
        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_train_scaled, y_train)
        
        # Predict for next refit_frequency periods
        predict_end = min(i + refit_frequency, len(X))
        X_pred = X.iloc[i:predict_end]
        
        # Remove NaN rows for prediction
        valid_pred_idx = ~X_pred.isna().any(axis=1)
        if valid_pred_idx.sum() == 0:
            continue
        
        X_pred_valid = X_pred[valid_pred_idx]
        X_pred_scaled = scaler.transform(X_pred_valid)
        
        # Predict probabilities
        proba = model.predict_proba(X_pred_scaled)[:, 1]  # Probability of positive return
        
        # Store predictions
        probabilities.loc[X_pred_valid.index] = proba
    
    # Generate signals from probabilities
    combined = pd.Series(0, index=X.index)
    combined[probabilities > threshold] = 1
    combined[probabilities < (1 - threshold)] = -1
    
    # Confidence is distance from 0.5
    confidence = abs(probabilities - 0.5) * 2
    
    # Feature importance as weights (use last model)
    if 'model' in locals():
        feature_names = X.columns.tolist()
        importance = abs(model.coef_[0])
        importance_norm = importance / importance.sum()
        weights = {name: float(imp) for name, imp in zip(feature_names, importance_norm)}
    else:
        weights = {name: 1.0 / len(signals) for name in signals.keys()}
    
    return CombinedSignal(
        signal=combined,
        confidence=confidence,
        weights=weights,
        metadata={
            "method": "logistic_model",
            "num_strategies": len(signals),
            "train_period": train_period,
            "refit_frequency": refit_frequency,
            "threshold": threshold
        }
    )


def resolve_ties(signal: pd.Series, tie_resolution: Literal["flat", "previous", "random"] = "flat") -> pd.Series:
    """Resolve ties when signal is neutral (0).
    
    Args:
        signal: Signal series
        tie_resolution: How to resolve neutral signals
            - "flat": Keep as 0 (default)
            - "previous": Use previous signal
            - "random": Random choice between 1 and -1
            
    Returns:
        Resolved signal series
    """
    resolved = signal.copy()
    
    if tie_resolution == "flat":
        return resolved
    
    elif tie_resolution == "previous":
        # Forward fill non-zero values
        non_zero_mask = resolved != 0
        resolved = resolved.where(non_zero_mask).ffill().fillna(0)
    
    elif tie_resolution == "random":
        # Random for zero values
        zero_mask = resolved == 0
        num_zeros = zero_mask.sum()
        if num_zeros > 0:
            random_signals = np.random.choice([-1, 1], size=num_zeros)
            resolved.loc[zero_mask] = random_signals
    
    else:
        raise ValueError(f"Unknown tie resolution method: {tie_resolution}")
    
    return resolved


def combine_signals(
    signals: Dict[str, pd.Series],
    method: Literal["simple_average", "weighted_average", "sharpe_weighted", "majority_vote", "logistic_model"] = "simple_average",
    returns: Optional[pd.Series] = None,
    weights: Optional[Dict[str, float]] = None,
    features: Optional[pd.DataFrame] = None,
    tie_resolution: Literal["flat", "previous", "random"] = "flat",
    **kwargs
) -> CombinedSignal:
    """Combine multiple signals using specified method.
    
    Args:
        signals: Dictionary of {strategy_name: signal_series}
        method: Combination method
        returns: Returns series (required for sharpe_weighted and logistic_model)
        weights: Custom weights (for weighted_average)
        features: Additional features (for logistic_model)
        tie_resolution: How to resolve tie signals
        **kwargs: Additional method-specific parameters
        
    Returns:
        CombinedSignal with combined signal
        
    Raises:
        ValueError: If required parameters are missing
    """
    # Select combination method
    if method == "simple_average":
        result = simple_average(signals, **kwargs)
    
    elif method == "weighted_average":
        if weights is None:
            raise ValueError("weighted_average requires 'weights' parameter")
        result = weighted_average(signals, weights, **kwargs)
    
    elif method == "sharpe_weighted":
        if returns is None:
            raise ValueError("sharpe_weighted requires 'returns' parameter")
        result = sharpe_weighted(signals, returns, **kwargs)
    
    elif method == "majority_vote":
        result = majority_vote(signals, **kwargs)
    
    elif method == "logistic_model":
        if returns is None:
            raise ValueError("logistic_model requires 'returns' parameter")
        result = logistic_model(signals, returns, features, **kwargs)
    
    else:
        raise ValueError(f"Unknown combination method: {method}")
    
    # Resolve ties
    result.signal = resolve_ties(result.signal, tie_resolution)
    
    return result

