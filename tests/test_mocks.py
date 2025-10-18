"""
Mock utilities for testing.
Provides mock data and exchange responses.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
import numpy as np


class MockExchange:
    """Mock exchange for testing without real API calls."""
    
    def __init__(self):
        self.calls = []
        self.rate_limited = False
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        since: Optional[int] = None,
        limit: int = 500
    ) -> List[List]:
        """Mock fetch_ohlcv returning synthetic data."""
        self.calls.append({
            'method': 'fetch_ohlcv',
            'symbol': symbol,
            'timeframe': timeframe,
            'since': since,
            'limit': limit
        })
        
        # Generate synthetic OHLCV data
        if since:
            start_date = pd.Timestamp(since, unit='ms')
        else:
            start_date = pd.Timestamp.now() - pd.Timedelta(days=30)
        
        dates = pd.date_range(start=start_date, periods=limit, freq=self._tf_to_freq(timeframe))
        
        # Generate realistic-looking prices
        base_price = 40000 if 'BTC' in symbol else 2000
        price_walk = np.cumsum(np.random.randn(limit) * 100) + base_price
        
        ohlcv = []
        for i, date in enumerate(dates):
            price = price_walk[i]
            ohlcv.append([
                int(date.timestamp() * 1000),  # timestamp
                float(price),  # open
                float(price + abs(np.random.randn() * 50)),  # high
                float(price - abs(np.random.randn() * 50)),  # low
                float(price + np.random.randn() * 20),  # close
                float(1000 + abs(np.random.randn() * 500))  # volume
            ])
        
        return ohlcv
    
    def _tf_to_freq(self, timeframe: str) -> str:
        """Convert timeframe to pandas frequency."""
        mapping = {
            '1m': '1T',
            '5m': '5T',
            '15m': '15T',
            '1h': '1H',
            '4h': '4H',
            '1d': '1D'
        }
        return mapping.get(timeframe, '1H')
    
    def fetch_ticker(self, symbol: str) -> dict:
        """Mock fetch_ticker."""
        self.calls.append({'method': 'fetch_ticker', 'symbol': symbol})
        
        return {
            'symbol': symbol,
            'last': 40000.0 if 'BTC' in symbol else 2000.0,
            'bid': 39990.0 if 'BTC' in symbol else 1999.0,
            'ask': 40010.0 if 'BTC' in symbol else 2001.0,
            'volume': 10000.0,
            'timestamp': int(datetime.now().timestamp() * 1000)
        }


def create_mock_ohlcv(
    n_bars: int = 200,
    start_price: float = 40000.0,
    volatility: float = 0.02,
    trend: float = 0.0,
    timeframe: str = '1h'
) -> pd.DataFrame:
    """
    Create mock OHLCV data for testing.
    
    Args:
        n_bars: Number of bars to generate
        start_price: Starting price
        volatility: Price volatility (std dev)
        trend: Daily trend (positive = uptrend, negative = downtrend)
        timeframe: Timeframe string
    
    Returns:
        DataFrame with OHLCV data
    """
    freq_map = {
        '1m': '1T',
        '5m': '5T',
        '15m': '15T',
        '1h': '1H',
        '4h': '4H',
        '1d': '1D'
    }
    
    freq = freq_map.get(timeframe, '1H')
    dates = pd.date_range(start='2023-01-01', periods=n_bars, freq=freq)
    
    # Generate price walk
    returns = np.random.randn(n_bars) * volatility + trend / n_bars
    close_prices = start_price * (1 + returns).cumprod()
    
    # Generate OHLC from close
    df = pd.DataFrame({
        'timestamp': dates,
        'open': close_prices * (1 + np.random.randn(n_bars) * 0.001),
        'high': close_prices * (1 + abs(np.random.randn(n_bars)) * 0.01),
        'low': close_prices * (1 - abs(np.random.randn(n_bars)) * 0.01),
        'close': close_prices,
        'volume': abs(np.random.randn(n_bars) * 1000 + 5000)
    })
    
    # Ensure high is highest and low is lowest
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
    
    return df


def create_trending_ohlcv(n_bars: int = 200, direction: str = 'up') -> pd.DataFrame:
    """Create mock OHLCV data with clear trend."""
    trend = 0.001 if direction == 'up' else -0.001
    return create_mock_ohlcv(n_bars=n_bars, trend=trend, volatility=0.015)


def create_ranging_ohlcv(n_bars: int = 200) -> pd.DataFrame:
    """Create mock OHLCV data in a range."""
    return create_mock_ohlcv(n_bars=n_bars, trend=0.0, volatility=0.01)


def create_volatile_ohlcv(n_bars: int = 200) -> pd.DataFrame:
    """Create mock OHLCV data with high volatility."""
    return create_mock_ohlcv(n_bars=n_bars, volatility=0.05)


class MockBacktestResult:
    """Mock backtest result for testing."""
    
    def __init__(self, **kwargs):
        self.total_return = kwargs.get('total_return', 0.15)
        self.sharpe_ratio = kwargs.get('sharpe_ratio', 1.5)
        self.max_drawdown = kwargs.get('max_drawdown', -0.20)
        self.win_rate = kwargs.get('win_rate', 0.55)
        self.profit_factor = kwargs.get('profit_factor', 1.8)
        self.num_trades = kwargs.get('num_trades', 100)
        self.avg_trade = kwargs.get('avg_trade', 0.0015)


if __name__ == "__main__":
    # Quick test
    mock_ex = MockExchange()
    data = mock_ex.fetch_ohlcv("BTC/USDT", "1h", limit=100)
    print(f"Generated {len(data)} bars")
    
    df = create_mock_ohlcv(n_bars=50)
    print(f"\nMock OHLCV shape: {df.shape}")
    print(df.head())

