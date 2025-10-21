"""Strategy Orchestrator - Automated backtesting and ranking of all strategies.

This module runs backtests on all registered strategies and ranks them by performance.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

from app.research.signals import (
    ma_crossover,
    rsi_regime_pullback,
    trend_following_ema,
    SignalOutput
)
from app.research.backtest.engine import BacktestEngine, BacktestConfig
from app.data.store import DataStore

logger = logging.getLogger(__name__)


class DataValidationStatus(BaseModel):
    """Status of data validation for a timeframe."""
    
    timeframe: str
    has_data: bool
    num_bars: int = 0
    reason: Optional[str] = None
    is_sufficient: bool = False


class StrategyDefinition(BaseModel):
    """Definition of a strategy for orchestration."""
    
    name: str = Field(..., description="Strategy name")
    func_name: str = Field(..., description="Function name in signals module")
    params: Dict = Field(default_factory=dict, description="Strategy parameters")
    enabled: bool = Field(default=True, description="Whether strategy is enabled")


class StrategyBacktestResult(BaseModel):
    """Results from a strategy backtest."""
    
    strategy_name: str
    timestamp: datetime
    timeframe: Optional[str] = None  # Added for multi-timeframe support
    
    # Performance metrics
    total_return: float
    cagr: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    expectancy: float
    
    # Risk metrics
    volatility: float
    calmar_ratio: float
    sortino_ratio: float
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    
    # Configuration used
    capital: float
    risk_pct: float
    lookback_days: int
    
    class Config:
        arbitrary_types_allowed = True


class StrategyOrchestrator:
    """Orchestrates backtesting of multiple strategies and ranks them."""
    
    # Registry of available strategies
    STRATEGY_REGISTRY: List[StrategyDefinition] = [
        StrategyDefinition(
            name="MA Crossover",
            func_name="ma_crossover",
            params={"fast_period": 10, "slow_period": 20},
            enabled=True
        ),
        StrategyDefinition(
            name="RSI Regime Pullback",
            func_name="rsi_regime_pullback",
            params={},
            enabled=True
        ),
        StrategyDefinition(
            name="Triple EMA Trend Following",
            func_name="trend_following_ema",
            params={},
            enabled=True
        ),
    ]
    
    def __init__(
        self,
        capital: float = 1000.0,
        max_risk_pct: float = 0.02,
        lookback_days: int = 90
    ):
        """Initialize orchestrator.
        
        Args:
            capital: Starting capital for backtest
            max_risk_pct: Maximum risk per trade
            lookback_days: Days of historical data to test
        """
        self.capital = capital
        self.max_risk_pct = max_risk_pct
        self.lookback_days = lookback_days
        self.store = DataStore()
    
    def run_all_backtests(
        self,
        symbol: str,
        timeframe: str,
        end_date: Optional[datetime] = None
    ) -> List[StrategyBacktestResult]:
        """Run backtests for all enabled strategies.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe to test
            end_date: End date for backtest (default: now)
            
        Returns:
            List of backtest results for each strategy
        """
        if end_date is None:
            end_date = datetime.now()
        
        logger.info(f"Running backtests for {symbol} {timeframe}")
        
        # Load data
        df = self._load_data(symbol, timeframe, end_date)
        if df is None or len(df) < 100:
            logger.warning(f"Insufficient data for {symbol} {timeframe}")
            return []
        
        results = []
        
        for strategy_def in self.STRATEGY_REGISTRY:
            if not strategy_def.enabled:
                continue
            
            try:
                result = self._backtest_strategy(strategy_def, df, symbol, timeframe)
                if result:
                    results.append(result)
                    logger.info(f"✅ {strategy_def.name}: Sharpe={result.sharpe_ratio:.2f}, WR={result.win_rate:.1%}")
            except Exception as e:
                logger.error(f"Failed to backtest {strategy_def.name}: {e}")
        
        return results
    
    def validate_data_availability(
        self,
        symbol: str,
        timeframes: List[str],
        end_date: Optional[datetime] = None,
        min_bars: int = 100
    ) -> Dict[str, DataValidationStatus]:
        """Validate data availability for multiple timeframes.
        
        Args:
            symbol: Trading symbol
            timeframes: List of timeframes to validate
            end_date: End date for validation (default: now)
            min_bars: Minimum number of bars required
            
        Returns:
            Dictionary mapping timeframe to validation status
        """
        if end_date is None:
            end_date = datetime.now()
        
        validation_results = {}
        
        for timeframe in timeframes:
            try:
                # Try to load data
                df = self._load_data(symbol, timeframe, end_date)
                
                if df is None or len(df) == 0:
                    validation_results[timeframe] = DataValidationStatus(
                        timeframe=timeframe,
                        has_data=False,
                        num_bars=0,
                        reason="No data available",
                        is_sufficient=False
                    )
                elif len(df) < min_bars:
                    validation_results[timeframe] = DataValidationStatus(
                        timeframe=timeframe,
                        has_data=True,
                        num_bars=len(df),
                        reason=f"Insufficient data: {len(df)} bars (minimum {min_bars})",
                        is_sufficient=False
                    )
                else:
                    validation_results[timeframe] = DataValidationStatus(
                        timeframe=timeframe,
                        has_data=True,
                        num_bars=len(df),
                        reason=None,
                        is_sufficient=True
                    )
                    
            except Exception as e:
                validation_results[timeframe] = DataValidationStatus(
                    timeframe=timeframe,
                    has_data=False,
                    num_bars=0,
                    reason=f"Error loading data: {str(e)}",
                    is_sufficient=False
                )
        
        return validation_results
    
    def run_multi_timeframe_backtests(
        self,
        symbol: str,
        timeframes: List[str],
        end_date: Optional[datetime] = None
    ) -> Dict[str, List[StrategyBacktestResult]]:
        """Run backtests across multiple timeframes with validation.
        
        Args:
            symbol: Trading symbol
            timeframes: List of timeframes to test
            end_date: End date for backtest (default: now)
            
        Returns:
            Dictionary mapping timeframe to list of results
        """
        if end_date is None:
            end_date = datetime.now()
        
        logger.info(f"Running multi-timeframe backtests for {symbol}")
        
        # Validate data availability first
        validation_results = self.validate_data_availability(symbol, timeframes, end_date)
        
        all_results = {}
        
        for timeframe in timeframes:
            validation = validation_results.get(timeframe)
            
            if not validation or not validation.is_sufficient:
                reason = validation.reason if validation else "Unknown error"
                logger.warning(f"⚠️ {timeframe}: Skipping - {reason}")
                all_results[timeframe] = []
                continue
            
            try:
                logger.info(f"Testing {symbol} on {timeframe} ({validation.num_bars} bars)")
                results = self.run_all_backtests(symbol, timeframe, end_date)
                
                if results:
                    # Add timeframe to each result
                    for result in results:
                        result.timeframe = timeframe
                    
                    all_results[timeframe] = results
                    logger.info(f"✅ {timeframe}: {len(results)} strategies tested")
                else:
                    logger.warning(f"⚠️ {timeframe}: No results")
                    all_results[timeframe] = []
                    
            except Exception as e:
                logger.error(f"❌ {timeframe}: {e}")
                all_results[timeframe] = []
        
        return all_results
    
    def generate_strategy_combinations(self, k_min: int = 2) -> List[Tuple[str, callable]]:
        """Generate strategy combinations for testing.
        
        Args:
            k_min: Minimum number of strategies in combination
            
        Returns:
            List of (name, callable) tuples for combinations
        """
        import itertools
        from app.research.signals import combine_signals
        
        combinations = []
        
        # Get all enabled strategies
        enabled_strategies = [s for s in self.STRATEGY_REGISTRY if s.enabled]
        
        # Generate combinations of size k_min and higher
        for k in range(k_min, len(enabled_strategies) + 1):
            for combo in itertools.combinations(enabled_strategies, k):
                # Create combination name
                combo_name = " + ".join([s.name for s in combo])
                
                # Create combination function
                def create_combo_func(strategies):
                    def combo_func(close_prices):
                        signals = []
                        for strategy in strategies:
                            try:
                                signal_func = getattr(__import__('app.research.signals', fromlist=[strategy.func_name]), strategy.func_name)
                                signal_output = signal_func(close_prices, **strategy.params)
                                signals.append(signal_output.signal)
                            except Exception as e:
                                logger.warning(f"Failed to load {strategy.func_name}: {e}")
                                continue
                        
                        if signals:
                            return combine_signals(signals, method="consensus")
                        else:
                            return None
                    
                    return combo_func
                
                combinations.append((combo_name, create_combo_func(combo)))
        
        return combinations
    
    def run_strategy_combinations(
        self,
        symbol: str,
        timeframe: str,
        end_date: Optional[datetime] = None
    ) -> List[StrategyBacktestResult]:
        """Run backtests for strategy combinations.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe to test
            end_date: End date for backtest (default: now)
            
        Returns:
            List of backtest results for combinations
        """
        if end_date is None:
            end_date = datetime.now()
        
        logger.info(f"Running strategy combinations for {symbol} {timeframe}")
        
        # Load data
        df = self._load_data(symbol, timeframe, end_date)
        if df is None or len(df) < 100:
            logger.warning(f"Insufficient data for {symbol} {timeframe}")
            return []
        
        # Generate combinations
        combinations = self.generate_strategy_combinations(k_min=2)
        
        results = []
        
        for combo_name, combo_func in combinations:
            try:
                # Generate signals for combination
                signal_output = combo_func(df['close'])
                if signal_output is None:
                    continue
                
                # Run backtest
                config = BacktestConfig(
                    initial_capital=self.capital,
                    risk_per_trade=self.max_risk_pct,
                    commission=0.001,
                    slippage=0.0005
                )
                
                engine = BacktestEngine(config)
                trades = engine.run(df, signal_output.signal, combo_name, verbose=False)
                
                if not trades:
                    continue
                
                # Calculate metrics from trades
                metrics = self._calculate_metrics_from_trades(trades)
                
                result = StrategyBacktestResult(
                    strategy_name=combo_name,
                    timestamp=end_date,
                    timeframe=timeframe,
                    **metrics
                )
                
                results.append(result)
                logger.info(f"✅ {combo_name}: Sharpe={result.sharpe_ratio:.2f}, WR={result.win_rate:.1%}")
                
            except Exception as e:
                logger.error(f"Failed to backtest combination {combo_name}: {e}")
                continue
        
        return results
    
    def _load_data(
        self,
        symbol: str,
        timeframe: str,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Load historical data for backtesting with homogeneous candle counts."""
        try:
            from app.config.settings import settings
            
            # Get target number of candles for this timeframe
            max_bars = settings.TIMEFRAME_CANDLE_TARGETS.get(timeframe, 365)
            
            bars = self.store.read_bars(symbol, timeframe, max_bars=max_bars)
            
            if not bars:
                return None
            
            df = pd.DataFrame([bar.to_dict() for bar in bars])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Filter by date range (if needed)
            end_timestamp = int(end_date.timestamp() * 1000)
            start_timestamp = int((end_date - timedelta(days=self.lookback_days)).timestamp() * 1000)
            
            df = df[(df['timestamp'] >= start_timestamp) & (df['timestamp'] <= end_timestamp)]
            
            return df if len(df) > 0 else None
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return None
    
    def _backtest_strategy(
        self,
        strategy_def: StrategyDefinition,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str
    ) -> Optional[StrategyBacktestResult]:
        """Run backtest for a single strategy."""
        try:
            # Generate signals
            signals = self._generate_signals(strategy_def, df)
            if signals is None:
                return None
            
            # Run backtest
            config = BacktestConfig(
                initial_capital=self.capital,
                risk_per_trade=self.max_risk_pct,
                commission=0.001,
                slippage=0.0005
            )
            
            engine = BacktestEngine(config)
            backtest_result = engine.run(df, signals.signal, strategy_def.name, verbose=True)
            
            if not backtest_result or backtest_result.total_trades == 0:
                logger.warning(f"No trades for {strategy_def.name}")
                return None
            
            # Create StrategyBacktestResult from BacktestResult
            result = StrategyBacktestResult(
                strategy_name=strategy_def.name,
                timestamp=datetime.now(),
                
                # Performance (from BacktestResult)
                total_return=backtest_result.total_return,
                cagr=backtest_result.cagr,
                sharpe_ratio=backtest_result.sharpe_ratio,
                max_drawdown=backtest_result.max_drawdown,
                win_rate=backtest_result.win_rate,
                profit_factor=backtest_result.profit_factor,
                expectancy=backtest_result.expectancy,
                
                # Risk (from BacktestResult)
                volatility=backtest_result.volatility,
                calmar_ratio=backtest_result.calmar_ratio,
                sortino_ratio=backtest_result.sortino_ratio,
                
                # Trade stats (from BacktestResult)
                total_trades=backtest_result.total_trades,
                winning_trades=backtest_result.winning_trades,
                losing_trades=backtest_result.losing_trades,
                avg_win=backtest_result.avg_win,
                avg_loss=backtest_result.avg_loss,
                
                # Config
                capital=self.capital,
                risk_pct=self.max_risk_pct,
                lookback_days=self.lookback_days
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in backtest for {strategy_def.name}: {e}")
            return None
    
    def _generate_signals(
        self,
        strategy_def: StrategyDefinition,
        df: pd.DataFrame
    ) -> Optional[SignalOutput]:
        """Generate signals for a strategy."""
        try:
            # Map function name to actual function
            func_map = {
                'ma_crossover': ma_crossover,
                'rsi_regime_pullback': rsi_regime_pullback,
                'trend_following_ema': trend_following_ema,
            }
            
            func = func_map.get(strategy_def.func_name)
            if func is None:
                logger.error(f"Unknown strategy function: {strategy_def.func_name}")
                return None
            
            # Call strategy function
            return func(df['close'], **strategy_def.params)
            
        except Exception as e:
            logger.error(f"Error generating signals for {strategy_def.name}: {e}")
            return None
    
    def rank_strategies(
        self,
        results: List[StrategyBacktestResult],
        ranking_method: str = "composite"
    ) -> List[Tuple[StrategyBacktestResult, float]]:
        """Rank strategies by performance.
        
        Args:
            results: List of backtest results
            ranking_method: Method to use for ranking
                - "composite": Weighted combination of metrics
                - "sharpe": By Sharpe ratio
                - "win_rate": By win rate
                - "drawdown": By minimum drawdown (inverted)
                
        Returns:
            List of (result, score) tuples sorted by score descending
        """
        if not results:
            return []
        
        if ranking_method == "sharpe":
            ranked = [(r, r.sharpe_ratio) for r in results]
        elif ranking_method == "win_rate":
            ranked = [(r, r.win_rate) for r in results]
        elif ranking_method == "drawdown":
            ranked = [(r, -r.max_drawdown) for r in results]  # Lower is better
        else:  # composite
            ranked = [(r, self._calculate_composite_score(r)) for r in results]
        
        # Sort by score descending
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        return ranked
    
    def _calculate_composite_score(self, result: StrategyBacktestResult) -> float:
        """Calculate composite score for ranking.
        
        Weights:
        - Sharpe Ratio: 30%
        - Win Rate: 25%
        - Max Drawdown (inverted): 20%
        - Profit Factor: 15%
        - Expectancy: 10%
        """
        # Normalize metrics to 0-100 scale
        sharpe_score = min(max(result.sharpe_ratio * 20, 0), 100)  # Sharpe 0-5 -> 0-100
        win_rate_score = result.win_rate * 100
        drawdown_score = max((1 - abs(result.max_drawdown)) * 100, 0)
        pf_score = min(max((result.profit_factor - 1) * 50, 0), 100)  # PF 1-3 -> 0-100
        expectancy_score = min(max(result.expectancy * 10, 0), 100)
        
        # Weighted average
        composite = (
            sharpe_score * 0.30 +
            win_rate_score * 0.25 +
            drawdown_score * 0.20 +
            pf_score * 0.15 +
            expectancy_score * 0.10
        )
        
        return composite
    
    def _calculate_metrics_from_trades(self, trades: List) -> Dict:
        """Calculate performance metrics from trade list with normalization.
        
        Args:
            trades: List of Trade objects or dicts from BacktestEngine
            
        Returns:
            Dictionary with calculated metrics (all fields guaranteed)
        """
        if not trades:
            return self._get_complete_empty_metrics()
        
        # Normalize trades to dict format
        normalized_trades = []
        for t in trades:
            if isinstance(t, dict):
                normalized_trades.append(t)
            else:
                # Convert object to dict
                trade_dict = {
                    'pnl': getattr(t, 'pnl', 0.0),
                    'pnl_pct': getattr(t, 'pnl_pct', 0.0)
                }
                normalized_trades.append(trade_dict)
        
        # Extract PnL series with safe defaults
        pnls = [t.get('pnl', 0.0) if isinstance(t, dict) else getattr(t, 'pnl', 0.0) for t in normalized_trades]
        pnl_pcts = [t.get('pnl_pct', 0.0) if isinstance(t, dict) else getattr(t, 'pnl_pct', 0.0) for t in normalized_trades]
        
        # Calculate equity curve
        equity = self.capital
        equity_curve = [equity]
        for pnl in pnls:
            equity += pnl
            equity_curve.append(equity)
        
        equity_series = pd.Series(equity_curve)
        
        # Total return
        total_return = (equity_curve[-1] - self.capital) / self.capital
        
        # CAGR (approximate)
        days = len(trades) * 2  # Approximate 2 days per trade
        years = days / 365.25
        cagr = ((1 + total_return) ** (1 / years) - 1) if years > 0 else 0
        
        # Sharpe ratio
        returns_series = pd.Series(pnl_pcts)
        sharpe_ratio = (returns_series.mean() / returns_series.std() * np.sqrt(252)) if returns_series.std() > 0 else 0
        
        # Sortino ratio (downside deviation)
        downside_returns = returns_series[returns_series < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else returns_series.std()
        sortino_ratio = (returns_series.mean() / downside_std * np.sqrt(252)) if downside_std > 0 else 0
        
        # Max drawdown
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Volatility
        volatility = returns_series.std() * np.sqrt(252)
        
        # Calmar ratio
        calmar_ratio = cagr / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Win rate
        winning_trades = [t for t in trades if t.pnl > 0] if trades and hasattr(trades[0], 'pnl') else []
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        # Profit factor
        total_wins = sum([t.pnl for t in trades if t.pnl > 0]) if trades and hasattr(trades[0], 'pnl') else 0
        total_losses = abs(sum([t.pnl for t in trades if t.pnl < 0])) if trades and hasattr(trades[0], 'pnl') else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        # Expectancy (average PnL per trade)
        expectancy = np.mean(pnls) if pnls else 0
        
        return {
            'total_return': total_return,
            'cagr': cagr,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'calmar_ratio': calmar_ratio,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'expectancy': expectancy
        }
    
    def _empty_metrics(self) -> Dict:
        """Return empty metrics dict (basic fields)."""
        return {
            'total_return': 0.0,
            'cagr': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'max_drawdown': 0.0,
            'volatility': 0.0,
            'calmar_ratio': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'expectancy': 0.0
        }
    
    def _get_complete_empty_metrics(self) -> Dict:
        """Return complete empty metrics dict with all required fields."""
        return {
            'total_return': 0.0,
            'cagr': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'max_drawdown': 0.0,
            'volatility': 0.0,
            'calmar_ratio': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'expectancy': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'capital': self.capital,
            'risk_pct': self.max_risk_pct,
            'lookback_days': self.lookback_days
        }
    
    def get_best_strategy(
        self,
        symbol: str,
        timeframe: str,
        ranking_method: str = "composite"
    ) -> Optional[StrategyBacktestResult]:
        """Get the best performing strategy for a symbol/timeframe.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            ranking_method: Ranking method to use
            
        Returns:
            Best strategy result or None
        """
        results = self.run_all_backtests(symbol, timeframe)
        
        if not results:
            return None
        
        ranked = self.rank_strategies(results, ranking_method)
        
        if ranked:
            best_strategy, score = ranked[0]
            logger.info(f"🏆 Best strategy: {best_strategy.strategy_name} (score: {score:.1f})")
            return best_strategy
        
        return None

