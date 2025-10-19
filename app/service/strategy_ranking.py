"""Strategy Ranking Service - Daily strategy selection and tracking.

This service:
- Runs daily backtests on all strategies
- Ranks them by performance metrics
- Persists rankings to database
- Provides recommendations for the best strategy to use
"""
import pandas as pd
from typing import Optional, Dict, List
from datetime import datetime, date
from pydantic import BaseModel, Field
import logging

from app.service.strategy_orchestrator import StrategyOrchestrator, StrategyBacktestResult
from app.service.paper_trading import PaperTradingDB
from app.service.decision import DecisionEngine, DailyDecision
from app.data.store import DataStore

logger = logging.getLogger(__name__)


class StrategyRecommendation(BaseModel):
    """Daily strategy recommendation."""
    
    date: str
    symbol: str
    timeframe: str
    
    # Best strategy
    best_strategy_name: str
    composite_score: float
    rank: int = 1
    
    # Key metrics
    sharpe_ratio: float
    win_rate: float
    max_drawdown: float
    expectancy: float
    
    # Trade recommendation
    signal_direction: int  # 1 (long), -1 (short), 0 (flat)
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    quantity: Optional[float] = None
    risk_amount: Optional[float] = None
    
    # Confidence
    confidence_level: str  # "HIGH", "MEDIUM", "LOW"
    confidence_description: str
    
    class Config:
        arbitrary_types_allowed = True


class StrategyRankingService:
    """Service for daily strategy selection and recommendation."""
    
    def __init__(
        self,
        capital: float = 1000.0,
        max_risk_pct: float = 0.02,
        lookback_days: int = 90
    ):
        """Initialize ranking service.
        
        Args:
            capital: Capital for backtesting
            max_risk_pct: Maximum risk per trade
            lookback_days: Days of historical data for backtesting
        """
        self.orchestrator = StrategyOrchestrator(capital, max_risk_pct, lookback_days)
        self.db = PaperTradingDB()
        self.store = DataStore()
    
    def get_daily_recommendation(
        self,
        symbol: str,
        timeframe: str,
        capital: float = 1000.0,
        ranking_method: str = "composite"
    ) -> Optional[StrategyRecommendation]:
        """Get daily strategy recommendation.
        
        This is the main entry point for getting today's best strategy and trade plan.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            capital: Trading capital
            ranking_method: Method for ranking strategies
            
        Returns:
            StrategyRecommendation with best strategy and trade plan
        """
        logger.info(f"Generating daily recommendation for {symbol} {timeframe}")
        
        # Run backtests
        results = self.orchestrator.run_all_backtests(symbol, timeframe)
        
        if not results:
            logger.warning("No backtest results available")
            return None
        
        # Rank strategies
        ranked = self.orchestrator.rank_strategies(results, ranking_method)
        
        if not ranked:
            logger.warning("No strategies ranked")
            return None
        
        # Get best strategy
        best_result, best_score = ranked[0]
        
        # Save rankings to database
        self._save_rankings(ranked, symbol, timeframe)
        
        # Generate trade recommendation using best strategy
        trade_plan = self._generate_trade_plan(
            best_result.strategy_name,
            symbol,
            timeframe,
            capital
        )
        
        # Determine confidence level
        confidence_level, confidence_desc = self._calculate_confidence(best_result)
        
        # Create recommendation
        recommendation = StrategyRecommendation(
            date=datetime.now().strftime('%Y-%m-%d'),
            symbol=symbol,
            timeframe=timeframe,
            
            best_strategy_name=best_result.strategy_name,
            composite_score=best_score,
            rank=1,
            
            sharpe_ratio=best_result.sharpe_ratio,
            win_rate=best_result.win_rate,
            max_drawdown=best_result.max_drawdown,
            expectancy=best_result.expectancy,
            
            signal_direction=trade_plan.get('signal', 0),
            entry_price=trade_plan.get('entry_price'),
            stop_loss=trade_plan.get('stop_loss'),
            take_profit=trade_plan.get('take_profit'),
            quantity=trade_plan.get('quantity'),
            risk_amount=trade_plan.get('risk_amount'),
            
            confidence_level=confidence_level,
            confidence_description=confidence_desc
        )
        
        logger.info(f"🏆 Best strategy: {best_result.strategy_name} (score: {best_score:.1f})")
        
        return recommendation
    
    def _save_rankings(
        self,
        ranked: List,
        symbol: str,
        timeframe: str
    ):
        """Save strategy rankings to database."""
        for i, (result, score) in enumerate(ranked):
            # Update result with symbol/timeframe (for database)
            # We'll need to modify save_strategy_ranking to accept these
            try:
                # Save to database with rank
                self.db.save_strategy_ranking(result, score, i + 1)
                
                # Also save individual metrics for trending
                today = datetime.now().strftime('%Y-%m-%d')
                self.db.save_strategy_performance_metric(
                    today, symbol, timeframe, result.strategy_name, 'sharpe_ratio', result.sharpe_ratio
                )
                self.db.save_strategy_performance_metric(
                    today, symbol, timeframe, result.strategy_name, 'win_rate', result.win_rate
                )
                self.db.save_strategy_performance_metric(
                    today, symbol, timeframe, result.strategy_name, 'max_drawdown', result.max_drawdown
                )
            except Exception as e:
                logger.error(f"Failed to save ranking for {result.strategy_name}: {e}")
    
    def _generate_trade_plan(
        self,
        strategy_name: str,
        symbol: str,
        timeframe: str,
        capital: float
    ) -> Dict:
        """Generate specific trade plan using the selected strategy."""
        try:
            # Load data
            bars = self.store.read_bars(symbol, timeframe)
            if not bars or len(bars) < 100:
                return {'signal': 0}
            
            df = pd.DataFrame([bar.to_dict() for bar in bars])
            df = df.sort_values('timestamp').reset_index(drop=True)
            df = df.tail(500)
            
            # Generate signals for selected strategy
            signals = self.orchestrator._generate_signals(
                self._get_strategy_def(strategy_name),
                df
            )
            
            if signals is None:
                return {'signal': 0}
            
            # Use DecisionEngine to create trade plan
            engine = DecisionEngine()
            decision = engine.make_decision(
                df,
                signals.signal,
                capital=capital,
                risk_pct=self.orchestrator.max_risk_pct
            )
            
            # Extract trade plan
            plan = {
                'signal': decision.signal,
                'entry_price': decision.entry_price,
                'stop_loss': decision.stop_loss,
                'take_profit': decision.take_profit,
                'quantity': decision.position_size.quantity if decision.position_size else None,
                'risk_amount': decision.position_size.risk_amount if decision.position_size else None,
                'should_execute': decision.should_execute,
                'skip_reason': decision.skip_reason
            }
            
            return plan
            
        except Exception as e:
            logger.error(f"Error generating trade plan: {e}")
            return {'signal': 0}
    
    def _get_strategy_def(self, strategy_name: str):
        """Get strategy definition by name."""
        for strat in self.orchestrator.STRATEGY_REGISTRY:
            if strat.name == strategy_name:
                return strat
        return None
    
    def _calculate_confidence(
        self,
        result: StrategyBacktestResult
    ) -> tuple[str, str]:
        """Calculate confidence level for a strategy.
        
        Returns:
            Tuple of (level, description)
        """
        # Score based on key metrics
        score = 0
        
        # Sharpe (40 points)
        if result.sharpe_ratio > 1.5:
            score += 40
        elif result.sharpe_ratio > 1.0:
            score += 30
        elif result.sharpe_ratio > 0.5:
            score += 20
        elif result.sharpe_ratio > 0:
            score += 10
        
        # Win rate (30 points)
        if result.win_rate > 0.6:
            score += 30
        elif result.win_rate > 0.55:
            score += 25
        elif result.win_rate > 0.5:
            score += 20
        elif result.win_rate > 0.45:
            score += 15
        else:
            score += 10
        
        # Max drawdown (30 points)
        if abs(result.max_drawdown) < 0.05:
            score += 30
        elif abs(result.max_drawdown) < 0.10:
            score += 25
        elif abs(result.max_drawdown) < 0.15:
            score += 20
        elif abs(result.max_drawdown) < 0.20:
            score += 15
        else:
            score += 10
        
        # Determine level
        if score >= 75:
            return "HIGH", f"Alta confianza ({score}/100): Sharpe {result.sharpe_ratio:.2f}, WR {result.win_rate:.1%}, DD {abs(result.max_drawdown):.1%}"
        elif score >= 50:
            return "MEDIUM", f"Confianza media ({score}/100): Sharpe {result.sharpe_ratio:.2f}, WR {result.win_rate:.1%}, DD {abs(result.max_drawdown):.1%}"
        else:
            return "LOW", f"Baja confianza ({score}/100): Sharpe {result.sharpe_ratio:.2f}, WR {result.win_rate:.1%}, DD {abs(result.max_drawdown):.1%}"
    
    def get_all_strategies_performance(
        self,
        symbol: str,
        timeframe: str
    ) -> List[StrategyBacktestResult]:
        """Get performance of all strategies for comparison.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            
        Returns:
            List of all strategy results
        """
        return self.orchestrator.run_all_backtests(symbol, timeframe)
    
    def compare_strategies(
        self,
        symbol: str,
        timeframe: str
    ) -> pd.DataFrame:
        """Compare all strategies in a DataFrame format.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            
        Returns:
            DataFrame with strategy comparison
        """
        results = self.get_all_strategies_performance(symbol, timeframe)
        
        if not results:
            return pd.DataFrame()
        
        # Build comparison dataframe
        comparison_data = []
        for result in results:
            comparison_data.append({
                'Strategy': result.strategy_name,
                'Sharpe': result.sharpe_ratio,
                'CAGR': result.cagr,
                'Win Rate': result.win_rate,
                'Max DD': result.max_drawdown,
                'Profit Factor': result.profit_factor,
                'Expectancy': result.expectancy,
                'Total Trades': result.total_trades,
                'Wins': result.winning_trades,
                'Losses': result.losing_trades
            })
        
        df = pd.DataFrame(comparison_data)
        
        # Sort by Sharpe descending
        df = df.sort_values('Sharpe', ascending=False).reset_index(drop=True)
        
        return df

