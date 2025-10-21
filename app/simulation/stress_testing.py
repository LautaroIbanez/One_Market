"""Stress Testing Engine for Trading Strategies.

This module implements stress testing and scenario analysis:
- Pre-defined shock scenarios (crash, volatility spike, liquidity crunch)
- Custom scenario builder
- Monte Carlo simulation of extreme events
- Survival metrics and drawdown analysis
- Stress test reports
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
import logging

from app.research.backtest.engine import BacktestEngine, BacktestConfig
from app.research.signals import generate_signal

logger = logging.getLogger(__name__)


class ShockType(str, Enum):
    """Types of shock scenarios."""
    CRASH = "crash"
    VOLATILITY_SPIKE = "volatility_spike"
    LIQUIDITY_CRUNCH = "liquidity_crunch"
    FLASH_CRASH = "flash_crash"
    TRENDING_REVERSAL = "trending_reversal"
    GRADUAL_DECLINE = "gradual_decline"


class ShockScenario(BaseModel):
    """Definition of a stress test scenario."""
    name: str = Field(..., description="Scenario name")
    shock_type: ShockType
    price_change_pct: float = Field(..., description="Price change percentage")
    volatility_multiplier: float = Field(default=1.0, description="Volatility multiplier")
    duration_bars: int = Field(default=1, description="Duration in bars")
    recovery_bars: int = Field(default=0, description="Recovery period bars")
    description: str = Field(default="", description="Scenario description")


class StressTestResult(BaseModel):
    """Result of a single stress test."""
    scenario_name: str
    strategy_name: str
    survived: bool = Field(..., description="Whether strategy survived")
    final_capital: float
    max_drawdown: float
    recovery_time_bars: Optional[int] = None
    total_trades_during_stress: int = 0
    worst_trade_pct: float = 0.0
    
    class Config:
        arbitrary_types_allowed = True


class StressTestReport(BaseModel):
    """Comprehensive stress test report."""
    timestamp: datetime = Field(default_factory=datetime.now)
    symbol: str
    timeframe: str
    num_scenarios: int
    num_strategies: int
    overall_survival_rate: float
    strategy_rankings: Dict[str, float] = Field(default_factory=dict)
    worst_scenario: Optional[str] = None
    best_performing_strategy: Optional[str] = None
    results: List[StressTestResult] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True


class StressTestEngine:
    """Engine for running stress tests on trading strategies."""
    
    def __init__(
        self,
        capital: float = 100000.0,
        ruin_threshold: float = 0.5
    ):
        """Initialize stress test engine.
        
        Args:
            capital: Initial capital
            ruin_threshold: Threshold for considering strategy "ruined" (e.g., 0.5 = 50% loss)
        """
        self.capital = capital
        self.ruin_threshold = ruin_threshold
        
        # Pre-defined scenarios
        self.standard_scenarios = self._create_standard_scenarios()
    
    def _create_standard_scenarios(self) -> List[ShockScenario]:
        """Create standard stress test scenarios.
        
        Returns:
            List of ShockScenario definitions
        """
        return [
            ShockScenario(
                name="Market Crash -20%",
                shock_type=ShockType.CRASH,
                price_change_pct=-0.20,
                volatility_multiplier=2.5,
                duration_bars=5,
                recovery_bars=10,
                description="Severe market crash with 20% drop in 5 bars"
            ),
            ShockScenario(
                name="Flash Crash -10%",
                shock_type=ShockType.FLASH_CRASH,
                price_change_pct=-0.10,
                volatility_multiplier=5.0,
                duration_bars=1,
                recovery_bars=3,
                description="Sudden flash crash recovering quickly"
            ),
            ShockScenario(
                name="Volatility Spike 3x",
                shock_type=ShockType.VOLATILITY_SPIKE,
                price_change_pct=0.0,
                volatility_multiplier=3.0,
                duration_bars=10,
                recovery_bars=5,
                description="Volatility increases 3x without directional bias"
            ),
            ShockScenario(
                name="Liquidity Crunch -15%",
                shock_type=ShockType.LIQUIDITY_CRUNCH,
                price_change_pct=-0.15,
                volatility_multiplier=4.0,
                duration_bars=3,
                recovery_bars=15,
                description="Liquidity dries up, wide spreads, slow recovery"
            ),
            ShockScenario(
                name="Trend Reversal",
                shock_type=ShockType.TRENDING_REVERSAL,
                price_change_pct=-0.25,
                volatility_multiplier=1.5,
                duration_bars=20,
                recovery_bars=0,
                description="Strong trend reverses sharply"
            ),
            ShockScenario(
                name="Gradual Decline -30%",
                shock_type=ShockType.GRADUAL_DECLINE,
                price_change_pct=-0.30,
                volatility_multiplier=1.2,
                duration_bars=50,
                recovery_bars=0,
                description="Slow, grinding decline over extended period"
            )
        ]
    
    def apply_shock_to_data(
        self,
        df: pd.DataFrame,
        scenario: ShockScenario,
        start_idx: int
    ) -> pd.DataFrame:
        """Apply shock scenario to price data.
        
        Args:
            df: Original DataFrame
            scenario: Shock scenario to apply
            start_idx: Index to start applying shock
            
        Returns:
            Modified DataFrame with shock applied
        """
        df_shocked = df.copy()
        
        if start_idx >= len(df):
            logger.warning("Start index beyond data length")
            return df_shocked
        
        # Calculate base volatility
        returns = df['close'].pct_change()
        base_volatility = returns.std()
        
        # Apply shock
        shock_end_idx = min(start_idx + scenario.duration_bars, len(df))
        
        for i in range(start_idx, shock_end_idx):
            if i == 0:
                continue
            
            # Price shock
            if scenario.shock_type == ShockType.CRASH:
                # Gradual crash
                progress = (i - start_idx + 1) / scenario.duration_bars
                shock_return = scenario.price_change_pct * progress
            
            elif scenario.shock_type == ShockType.FLASH_CRASH:
                # Immediate drop
                shock_return = scenario.price_change_pct
            
            elif scenario.shock_type == ShockType.VOLATILITY_SPIKE:
                # No directional bias, just higher volatility
                shock_return = np.random.normal(0, base_volatility * scenario.volatility_multiplier)
            
            elif scenario.shock_type == ShockType.LIQUIDITY_CRUNCH:
                # Price drop with high volatility
                progress = (i - start_idx + 1) / scenario.duration_bars
                shock_return = scenario.price_change_pct * progress + np.random.normal(0, base_volatility * scenario.volatility_multiplier)
            
            elif scenario.shock_type == ShockType.TRENDING_REVERSAL:
                # Gradual reversal
                progress = (i - start_idx + 1) / scenario.duration_bars
                shock_return = scenario.price_change_pct * progress
            
            elif scenario.shock_type == ShockType.GRADUAL_DECLINE:
                # Slow decline
                shock_return = scenario.price_change_pct / scenario.duration_bars
            
            else:
                shock_return = 0.0
            
            # Apply to prices
            df_shocked.loc[i, 'close'] = df_shocked.loc[i-1, 'close'] * (1 + shock_return)
            df_shocked.loc[i, 'open'] = df_shocked.loc[i-1, 'close']
            df_shocked.loc[i, 'high'] = df_shocked.loc[i, 'close'] * 1.01
            df_shocked.loc[i, 'low'] = df_shocked.loc[i, 'close'] * 0.99
        
        # Recovery phase
        if scenario.recovery_bars > 0:
            recovery_end_idx = min(shock_end_idx + scenario.recovery_bars, len(df))
            recovery_target = df.loc[start_idx, 'close']  # Original price before shock
            
            for i in range(shock_end_idx, recovery_end_idx):
                if i == 0:
                    continue
                progress = (i - shock_end_idx + 1) / scenario.recovery_bars
                target_price = df_shocked.loc[shock_end_idx - 1, 'close'] + (recovery_target - df_shocked.loc[shock_end_idx - 1, 'close']) * progress
                
                df_shocked.loc[i, 'close'] = target_price
                df_shocked.loc[i, 'open'] = df_shocked.loc[i-1, 'close']
                df_shocked.loc[i, 'high'] = df_shocked.loc[i, 'close'] * 1.01
                df_shocked.loc[i, 'low'] = df_shocked.loc[i, 'close'] * 0.99
        
        return df_shocked
    
    def run_stress_test(
        self,
        df: pd.DataFrame,
        strategy_name: str,
        scenario: ShockScenario,
        start_idx: Optional[int] = None
    ) -> StressTestResult:
        """Run stress test for a single strategy and scenario.
        
        Args:
            df: Original DataFrame
            strategy_name: Strategy to test
            scenario: Shock scenario
            start_idx: Index to apply shock (defaults to middle of data)
            
        Returns:
            StressTestResult with outcomes
        """
        if start_idx is None:
            start_idx = len(df) // 2
        
        logger.info(f"Stress testing {strategy_name} with {scenario.name}")
        
        # Apply shock
        df_shocked = self.apply_shock_to_data(df, scenario, start_idx)
        
        # Generate signals
        try:
            signal_output = generate_signal(strategy_name, df_shocked)
        except Exception as e:
            logger.error(f"Error generating signals for {strategy_name}: {e}")
            return StressTestResult(
                scenario_name=scenario.name,
                strategy_name=strategy_name,
                survived=False,
                final_capital=0.0,
                max_drawdown=-1.0
            )
        
        # Run backtest
        config = BacktestConfig(
            initial_capital=self.capital,
            risk_per_trade=0.02,
            commission_pct=0.001
        )
        engine = BacktestEngine(config)
        
        try:
            result = engine.run(
                df=df_shocked,
                signals=signal_output.signal,
                strategy_name=strategy_name,
                verbose=False
            )
            
            # Determine survival
            loss_pct = abs(result.max_drawdown) if result.max_drawdown < 0 else 0.0
            survived = loss_pct < self.ruin_threshold
            
            # Calculate recovery time
            recovery_time = None
            if not survived:
                # Strategy was ruined, no recovery
                recovery_time = None
            elif result.max_drawdown < 0:
                # Try to estimate recovery time (simplified)
                recovery_time = int(abs(result.max_drawdown) * 100)  # Rough estimate
            
            return StressTestResult(
                scenario_name=scenario.name,
                strategy_name=strategy_name,
                survived=survived,
                final_capital=self.capital * (1 + result.total_return),
                max_drawdown=result.max_drawdown,
                recovery_time_bars=recovery_time,
                total_trades_during_stress=result.total_trades,
                worst_trade_pct=result.avg_loss if result.avg_loss else 0.0
            )
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return StressTestResult(
                scenario_name=scenario.name,
                strategy_name=strategy_name,
                survived=False,
                final_capital=0.0,
                max_drawdown=-1.0
            )
    
    def run_comprehensive_stress_test(
        self,
        df: pd.DataFrame,
        strategies: List[str],
        scenarios: Optional[List[ShockScenario]] = None,
        symbol: str = "Unknown",
        timeframe: str = "1h"
    ) -> StressTestReport:
        """Run comprehensive stress test across multiple strategies and scenarios.
        
        Args:
            df: DataFrame with OHLCV data
            strategies: List of strategy names to test
            scenarios: Custom scenarios (defaults to standard scenarios)
            symbol: Trading symbol
            timeframe: Timeframe
            
        Returns:
            StressTestReport with comprehensive results
        """
        if scenarios is None:
            scenarios = self.standard_scenarios
        
        logger.info(f"Running comprehensive stress test: {len(strategies)} strategies × {len(scenarios)} scenarios")
        
        results = []
        survival_count = 0
        total_tests = 0
        
        strategy_scores = {s: 0 for s in strategies}
        scenario_difficulty = {sc.name: 0 for sc in scenarios}
        
        for strategy in strategies:
            for scenario in scenarios:
                result = self.run_stress_test(df, strategy, scenario)
                results.append(result)
                
                total_tests += 1
                if result.survived:
                    survival_count += 1
                    strategy_scores[strategy] += 1
                else:
                    scenario_difficulty[scenario.name] += 1
        
        # Calculate metrics
        overall_survival_rate = survival_count / total_tests if total_tests > 0 else 0.0
        
        # Rank strategies
        strategy_rankings = {
            name: score / len(scenarios) for name, score in strategy_scores.items()
        }
        
        # Find worst scenario
        worst_scenario = max(scenario_difficulty.items(), key=lambda x: x[1])[0] if scenario_difficulty else None
        
        # Find best strategy
        best_strategy = max(strategy_scores.items(), key=lambda x: x[1])[0] if strategy_scores else None
        
        report = StressTestReport(
            timestamp=datetime.now(),
            symbol=symbol,
            timeframe=timeframe,
            num_scenarios=len(scenarios),
            num_strategies=len(strategies),
            overall_survival_rate=overall_survival_rate,
            strategy_rankings=strategy_rankings,
            worst_scenario=worst_scenario,
            best_performing_strategy=best_strategy,
            results=results
        )
        
        logger.info(f"Stress test complete: {survival_count}/{total_tests} survived ({overall_survival_rate:.1%})")
        logger.info(f"Best strategy: {best_strategy}")
        logger.info(f"Worst scenario: {worst_scenario}")
        
        return report
    
    def get_survival_matrix(
        self,
        report: StressTestReport
    ) -> pd.DataFrame:
        """Get survival matrix (strategies × scenarios).
        
        Args:
            report: StressTestReport
            
        Returns:
            DataFrame with survival matrix
        """
        # Extract unique strategies and scenarios
        strategies = sorted(set(r.strategy_name for r in report.results))
        scenarios = sorted(set(r.scenario_name for r in report.results))
        
        # Create matrix
        matrix = pd.DataFrame(index=strategies, columns=scenarios)
        
        for result in report.results:
            matrix.loc[result.strategy_name, result.scenario_name] = "✓" if result.survived else "✗"
        
        return matrix
    
    def generate_stress_report_text(
        self,
        report: StressTestReport
    ) -> str:
        """Generate text summary of stress test.
        
        Args:
            report: StressTestReport
            
        Returns:
            Formatted text report
        """
        lines = [
            "="*80,
            "STRESS TEST REPORT",
            "="*80,
            f"Symbol: {report.symbol}",
            f"Timeframe: {report.timeframe}",
            f"Timestamp: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"Scenarios Tested: {report.num_scenarios}",
            f"Strategies Tested: {report.num_strategies}",
            f"Overall Survival Rate: {report.overall_survival_rate:.1%}",
            "",
            "="*80,
            "STRATEGY RANKINGS (Survival Rate)",
            "="*80
        ]
        
        for strategy, score in sorted(report.strategy_rankings.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {strategy:40s} {score:.1%}")
        
        lines.extend([
            "",
            "="*80,
            "BEST/WORST",
            "="*80,
            f"Best Performing Strategy: {report.best_performing_strategy}",
            f"Worst (Most Difficult) Scenario: {report.worst_scenario}",
            "",
            "="*80,
            "SURVIVAL MATRIX",
            "="*80
        ])
        
        matrix = self.get_survival_matrix(report)
        lines.append(matrix.to_string())
        
        lines.append("="*80)
        
        return "\n".join(lines)

