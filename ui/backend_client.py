"""Backend client for UI integration.

This module provides a client to interact with the unified backend API,
ensuring the UI uses the same engine as the API.
"""
import requests
import json
import pandas as pd
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import logging
import streamlit as st
import time

logger = logging.getLogger(__name__)


class BackendClient:
    """Client for unified backend API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize client.
        
        Args:
            base_url: Base URL for the API
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def run_backtest(
        self,
        symbol: str,
        timeframe: str,
        strategy: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        initial_capital: float = 10000.0,
        risk_per_trade: float = 0.02,
        commission: float = 0.001,
        slippage: float = 0.0005,
        use_trading_windows: bool = True,
        force_close: bool = True,
        one_trade_per_day: bool = True,
        atr_sl_multiplier: float = 2.0,
        atr_tp_multiplier: float = 3.0,
        atr_period: int = 14
    ) -> Optional[Dict[str, Any]]:
        """Run backtest using unified API.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            strategy: Strategy name
            from_date: Start date
            to_date: End date
            initial_capital: Initial capital
            risk_per_trade: Risk per trade
            commission: Commission rate
            slippage: Slippage rate
            use_trading_windows: Use trading windows
            force_close: Force close positions
            one_trade_per_day: One trade per day rule
            atr_sl_multiplier: ATR stop loss multiplier
            atr_tp_multiplier: ATR take profit multiplier
            atr_period: ATR period
            
        Returns:
            Backtest results or None if failed
        """
        try:
            # Prepare request data
            request_data = {
                "symbol": symbol,
                "timeframe": timeframe,
                "strategy": strategy,
                "initial_capital": initial_capital,
                "risk_per_trade": risk_per_trade,
                "commission": commission,
                "slippage": slippage,
                "use_trading_windows": use_trading_windows,
                "force_close": force_close,
                "one_trade_per_day": one_trade_per_day,
                "atr_sl_multiplier": atr_sl_multiplier,
                "atr_tp_multiplier": atr_tp_multiplier,
                "atr_period": atr_period
            }
            
            # Add dates if provided
            if from_date:
                request_data["from_date"] = from_date.isoformat()
            if to_date:
                request_data["to_date"] = to_date.isoformat()
            
            # Make API request
            response = self.session.post(
                f"{self.base_url}/backtest/run",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Backtest completed: {result['total_trades']} trades, Sharpe={result['sharpe_ratio']:.2f}")
                return result
            else:
                logger.error(f"Backtest failed: {response.status_code} - {response.text}")
                st.error(f"Backend error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            st.error(f"Connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in backtest: {e}")
            st.error(f"Unexpected error: {e}")
            return None
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available strategies.
        
        Returns:
            List of strategy names
        """
        try:
            response = self.session.get(f"{self.base_url}/backtest/strategies", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("strategies", [])
            else:
                logger.error(f"Failed to get strategies: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting strategies: {e}")
            return []
    
    def get_daily_recommendation(
        self,
        symbol: str,
        date: Optional[str] = None,
        capital: float = 10000.0,
        risk_percentage: float = 2.0,
        include_freshness: bool = True,
        use_strategy_ranking: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get daily recommendation.
        
        Args:
            symbol: Trading symbol
            date: Date in YYYY-MM-DD format (default: today)
            capital: Available capital
            risk_percentage: Risk percentage per trade
            include_freshness: Include data freshness validation
            use_strategy_ranking: Use strategy ranking instead of signal-based
            
        Returns:
            Recommendation data or None if failed
        """
        try:
            params = {
                "symbol": symbol,
                "capital": capital,
                "risk_percentage": risk_percentage,
                "include_freshness": include_freshness,
                "use_strategy_ranking": use_strategy_ranking
            }
            
            if date:
                params["date"] = date
            
            response = self.session.get(
                f"{self.base_url}/recommendation/daily",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                # Extract recommendation data from nested structure
                recommendation = data.get("recommendation", {})
                metadata = data.get("metadata", {})
                data_freshness = data.get("data_freshness", {})
                
                # Return the recommendation data with metadata
                return {
                    "recommendation": recommendation,
                    "metadata": metadata,
                    "data_freshness": data_freshness,
                    "raw_response": data
                }
            else:
                logger.error(f"Recommendation failed: {response.status_code} - {response.text}")
                st.error(f"Recommendation error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting recommendation: {e}")
            st.error(f"Recommendation error: {e}")
            return None
    
    def get_recommendation_history(
        self,
        symbol: str,
        from_date: str,
        to_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recommendation history.
        
        Args:
            symbol: Trading symbol
            from_date: Start date
            to_date: End date (default: today)
            
        Returns:
            List of recommendations
        """
        try:
            params = {
                "symbol": symbol,
                "from_date": from_date
            }
            
            if to_date:
                params["to_date"] = to_date
            
            response = self.session.get(
                f"{self.base_url}/recommendation/history",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"History failed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return []
    
    def compare_strategies(
        self,
        symbol: str,
        timeframe: str,
        strategies: List[str],
        **kwargs
    ) -> pd.DataFrame:
        """Compare multiple strategies and return DataFrame.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            strategies: List of strategy names
            **kwargs: Additional backtest parameters
            
        Returns:
            DataFrame with strategy comparison
        """
        results = {}
        
        for strategy in strategies:
            logger.info(f"Running backtest for {strategy}")
            result = self.run_backtest(
                symbol=symbol,
                timeframe=timeframe,
                strategy=strategy,
                **kwargs
            )
            results[strategy] = result
        
        comparison_data = []
        for strategy, result in results.items():
            if result:
                comparison_data.append({
                    'Strategy': strategy,
                    'CAGR': result['cagr'],
                    'Sharpe': result['sharpe_ratio'],
                    'Sortino': result['sortino_ratio'],
                    'Calmar': result['calmar_ratio'],
                    'Win Rate': result['win_rate'],
                    'Max DD': result['max_drawdown'],
                    'Profit Factor': result['profit_factor'],
                    'Expectancy': result['expectancy'],
                    'Trades': result['total_trades'],
                    'Volatility': result['volatility']
                })
            else:
                # Add failed strategy with default values
                comparison_data.append({
                    'Strategy': strategy,
                    'CAGR': 0.0,
                    'Sharpe': 0.0,
                    'Sortino': 0.0,
                    'Calmar': 0.0,
                    'Win Rate': 0.0,
                    'Max DD': 0.0,
                    'Profit Factor': 0.0,
                    'Expectancy': 0.0,
                    'Trades': 0,
                    'Volatility': 0.0
                })
        
        df = pd.DataFrame(comparison_data)
        return df.sort_values('Sharpe', ascending=False).reset_index(drop=True)
    
    def check_backend_health(self) -> bool:
        """Check if backend is healthy.
        
        Returns:
            True if backend is healthy, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def wait_for_healthcheck(self, timeout: int = 30, interval: int = 2) -> bool:
        """Wait for backend to become healthy.
        
        Args:
            timeout: Maximum time to wait in seconds
            interval: Check interval in seconds
            
        Returns:
            True if backend becomes healthy, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.check_backend_health():
                return True
            time.sleep(interval)
        
        return False
    
    def get_ohlcv_data(self, symbol: str, timeframe: str, limit: int = 500) -> Optional[pd.DataFrame]:
        """Get OHLCV data from backend.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            limit: Maximum number of bars to return
            
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            params = {
                "symbol": symbol,
                "timeframe": timeframe,
                "limit": limit
            }
            
            response = self.session.get(
                f"{self.base_url}/data/ohlcv",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('bars'):
                    df = pd.DataFrame(data['bars'])
                    df = df.sort_values('timestamp').reset_index(drop=True)
                    return df
                else:
                    logger.warning(f"No OHLCV data returned for {symbol} {timeframe}")
                    return None
            else:
                logger.error(f"OHLCV request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting OHLCV data: {e}")
            return None
    
    def get_symbols(self) -> List[str]:
        """Get available symbols from backend.
        
        Returns:
            List of available symbols
        """
        try:
            response = self.session.get(f"{self.base_url}/symbols", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("symbols", [])
            else:
                logger.error(f"Failed to get symbols: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting symbols: {e}")
            return []
    
    def get_strategies(self) -> List[str]:
        """Get available strategies from backend.
        
        Returns:
            List of available strategies
        """
        try:
            response = self.session.get(f"{self.base_url}/strategies", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("strategies", [])
            else:
                logger.error(f"Failed to get strategies: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting strategies: {e}")
            return []
