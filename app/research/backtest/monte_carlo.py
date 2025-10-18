"""Monte Carlo simulation and stability analysis.

This module provides Monte Carlo simulation for:
- Return permutation by blocks
- Risk of ruin estimation
- Expected drawdown
- Confidence intervals
- Stability metrics
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Tuple
from pydantic import BaseModel, Field
import warnings

warnings.filterwarnings('ignore')


class MonteCarloResult(BaseModel):
    """Monte Carlo simulation result."""
    
    # Returns distribution
    mean_return: float = Field(..., description="Mean return across simulations")
    median_return: float = Field(..., description="Median return")
    std_return: float = Field(..., description="Standard deviation of returns")
    
    # Confidence intervals
    ci_95_lower: float = Field(..., description="95% CI lower bound")
    ci_95_upper: float = Field(..., description="95% CI upper bound")
    ci_99_lower: float = Field(..., description="99% CI lower bound")
    ci_99_upper: float = Field(..., description="99% CI upper bound")
    
    # Drawdown statistics
    mean_max_dd: float = Field(..., description="Mean maximum drawdown")
    median_max_dd: float = Field(..., description="Median maximum drawdown")
    worst_dd: float = Field(..., description="Worst drawdown observed")
    dd_95_percentile: float = Field(..., description="95th percentile drawdown")
    
    # Risk metrics
    risk_of_ruin: float = Field(..., description="Probability of ruin")
    probability_of_profit: float = Field(..., description="Probability of positive return")
    
    # Sharpe distribution
    mean_sharpe: float = Field(..., description="Mean Sharpe ratio")
    median_sharpe: float = Field(..., description="Median Sharpe ratio")
    sharpe_95_lower: float = Field(..., description="95% CI Sharpe lower")
    sharpe_95_upper: float = Field(..., description="95% CI Sharpe upper")
    
    # Stability metrics
    consistency_score: float = Field(..., description="Consistency score (0-1)")
    stability_index: float = Field(..., description="Stability index")
    
    # Simulation metadata
    num_simulations: int = Field(..., description="Number of simulations")
    block_size: int = Field(..., description="Block size used")
    
    # Raw results
    all_returns: List[float] = Field(default_factory=list, description="All simulated returns")
    all_max_dds: List[float] = Field(default_factory=list, description="All max drawdowns")
    all_sharpes: List[float] = Field(default_factory=list, description="All Sharpe ratios")


def permute_returns_by_blocks(
    returns: pd.Series,
    block_size: int = 5,
    num_simulations: int = 1000,
    seed: Optional[int] = None
) -> List[pd.Series]:
    """Permute returns by blocks to preserve autocorrelation.
    
    Args:
        returns: Original returns series
        block_size: Size of blocks to permute
        num_simulations: Number of simulations
        seed: Random seed for reproducibility
        
    Returns:
        List of permuted return series
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Split returns into blocks
    n_returns = len(returns)
    n_blocks = n_returns // block_size
    
    # Trim to fit blocks
    trimmed_returns = returns.iloc[:n_blocks * block_size].values
    blocks = trimmed_returns.reshape(n_blocks, block_size)
    
    # Simulate
    simulated_returns = []
    
    for _ in range(num_simulations):
        # Randomly permute blocks
        shuffled_blocks = blocks[np.random.permutation(n_blocks)]
        
        # Flatten back to series
        shuffled_returns = shuffled_blocks.flatten()
        simulated_returns.append(pd.Series(shuffled_returns))
    
    return simulated_returns


def calculate_risk_of_ruin(
    equity_curves: List[pd.Series],
    ruin_threshold: float = 0.5
) -> float:
    """Calculate risk of ruin (probability of losing X% of capital).
    
    Args:
        equity_curves: List of equity curve series
        ruin_threshold: Threshold for ruin (0.5 = 50% loss)
        
    Returns:
        Probability of ruin (0-1)
    """
    num_ruined = 0
    
    for equity in equity_curves:
        # Calculate drawdown
        running_max = equity.expanding().max()
        drawdown = (equity - running_max) / running_max
        
        # Check if ruin occurred
        if abs(drawdown.min()) >= ruin_threshold:
            num_ruined += 1
    
    risk = num_ruined / len(equity_curves)
    return float(risk)


def calculate_stability_index(returns_list: List[float]) -> float:
    """Calculate stability index.
    
    Measures consistency of returns across simulations.
    Lower coefficient of variation = higher stability.
    
    Args:
        returns_list: List of returns from simulations
        
    Returns:
        Stability index (higher is better)
    """
    if len(returns_list) == 0:
        return 0.0
    
    mean_return = np.mean(returns_list)
    std_return = np.std(returns_list)
    
    if mean_return == 0:
        return 0.0
    
    # Coefficient of variation
    cv = std_return / abs(mean_return)
    
    # Stability index (inverse of CV, capped at 10)
    stability = min(1 / cv, 10) if cv > 0 else 10
    
    return float(stability)


def run_monte_carlo(
    returns: pd.Series,
    initial_capital: float = 100000.0,
    block_size: int = 5,
    num_simulations: int = 1000,
    ruin_threshold: float = 0.5,
    seed: Optional[int] = None,
    verbose: bool = True
) -> MonteCarloResult:
    """Run Monte Carlo simulation.
    
    Args:
        returns: Historical returns series
        initial_capital: Initial capital
        block_size: Block size for permutation
        num_simulations: Number of simulations
        ruin_threshold: Threshold for risk of ruin
        seed: Random seed
        verbose: Print progress
        
    Returns:
        MonteCarloResult with all metrics
    """
    if verbose:
        print(f"\n{'='*60}")
        print(f"Monte Carlo Simulation")
        print(f"{'='*60}")
        print(f"Simulations: {num_simulations}")
        print(f"Block size: {block_size}")
        print(f"Ruin threshold: {ruin_threshold:.0%}")
    
    # Permute returns
    if verbose:
        print(f"\nPermuting returns...")
    
    simulated_returns_list = permute_returns_by_blocks(
        returns, block_size, num_simulations, seed
    )
    
    # Run simulations
    if verbose:
        print(f"Running simulations...")
    
    all_returns = []
    all_max_dds = []
    all_sharpes = []
    all_equity_curves = []
    
    for i, sim_returns in enumerate(simulated_returns_list):
        if verbose and (i + 1) % 100 == 0:
            print(f"  Completed: {i+1}/{num_simulations}")
        
        # Calculate metrics
        total_return = (1 + sim_returns).prod() - 1
        all_returns.append(total_return)
        
        # Sharpe
        sharpe = (sim_returns.mean() / sim_returns.std() * np.sqrt(252)) if sim_returns.std() > 0 else 0
        all_sharpes.append(sharpe)
        
        # Max drawdown
        equity = (1 + sim_returns).cumprod() * initial_capital
        running_max = equity.expanding().max()
        drawdown = (equity - running_max) / running_max
        max_dd = abs(drawdown.min())
        all_max_dds.append(max_dd)
        
        # Store equity curve
        all_equity_curves.append(equity)
    
    # Calculate statistics
    if verbose:
        print(f"\nCalculating statistics...")
    
    # Returns distribution
    mean_return = np.mean(all_returns)
    median_return = np.median(all_returns)
    std_return = np.std(all_returns)
    
    # Confidence intervals
    ci_95_lower, ci_95_upper = np.percentile(all_returns, [2.5, 97.5])
    ci_99_lower, ci_99_upper = np.percentile(all_returns, [0.5, 99.5])
    
    # Drawdown stats
    mean_max_dd = np.mean(all_max_dds)
    median_max_dd = np.median(all_max_dds)
    worst_dd = max(all_max_dds)
    dd_95_percentile = np.percentile(all_max_dds, 95)
    
    # Risk metrics
    risk_ruin = calculate_risk_of_ruin(all_equity_curves, ruin_threshold)
    prob_profit = sum(1 for r in all_returns if r > 0) / len(all_returns)
    
    # Sharpe distribution
    mean_sharpe = np.mean(all_sharpes)
    median_sharpe = np.median(all_sharpes)
    sharpe_95_lower, sharpe_95_upper = np.percentile(all_sharpes, [2.5, 97.5])
    
    # Stability
    consistency = prob_profit
    stability = calculate_stability_index(all_returns)
    
    result = MonteCarloResult(
        mean_return=float(mean_return),
        median_return=float(median_return),
        std_return=float(std_return),
        ci_95_lower=float(ci_95_lower),
        ci_95_upper=float(ci_95_upper),
        ci_99_lower=float(ci_99_lower),
        ci_99_upper=float(ci_99_upper),
        mean_max_dd=float(mean_max_dd),
        median_max_dd=float(median_max_dd),
        worst_dd=float(worst_dd),
        dd_95_percentile=float(dd_95_percentile),
        risk_of_ruin=float(risk_ruin),
        probability_of_profit=float(prob_profit),
        mean_sharpe=float(mean_sharpe),
        median_sharpe=float(median_sharpe),
        sharpe_95_lower=float(sharpe_95_lower),
        sharpe_95_upper=float(sharpe_95_upper),
        consistency_score=float(consistency),
        stability_index=float(stability),
        num_simulations=num_simulations,
        block_size=block_size,
        all_returns=all_returns,
        all_max_dds=all_max_dds,
        all_sharpes=all_sharpes
    )
    
    if verbose:
        print_monte_carlo_summary(result)
    
    return result


def print_monte_carlo_summary(result: MonteCarloResult):
    """Print Monte Carlo summary.
    
    Args:
        result: MonteCarloResult
    """
    print(f"\n{'='*60}")
    print(f"MONTE CARLO RESULTS")
    print(f"{'='*60}")
    
    print(f"\n📊 Returns Distribution:")
    print(f"  Mean: {result.mean_return:.2%}")
    print(f"  Median: {result.median_return:.2%}")
    print(f"  Std Dev: {result.std_return:.2%}")
    print(f"  95% CI: [{result.ci_95_lower:.2%}, {result.ci_95_upper:.2%}]")
    print(f"  99% CI: [{result.ci_99_lower:.2%}, {result.ci_99_upper:.2%}]")
    
    print(f"\n📉 Drawdown Statistics:")
    print(f"  Mean Max DD: {result.mean_max_dd:.2%}")
    print(f"  Median Max DD: {result.median_max_dd:.2%}")
    print(f"  Worst DD: {result.worst_dd:.2%}")
    print(f"  95th Percentile DD: {result.dd_95_percentile:.2%}")
    
    print(f"\n⚠️  Risk Metrics:")
    print(f"  Risk of Ruin: {result.risk_of_ruin:.2%}")
    print(f"  Probability of Profit: {result.probability_of_profit:.2%}")
    
    print(f"\n📈 Sharpe Distribution:")
    print(f"  Mean: {result.mean_sharpe:.2f}")
    print(f"  Median: {result.median_sharpe:.2f}")
    print(f"  95% CI: [{result.sharpe_95_lower:.2f}, {result.sharpe_95_upper:.2f}]")
    
    print(f"\n🎯 Stability:")
    print(f"  Consistency Score: {result.consistency_score:.2%}")
    print(f"  Stability Index: {result.stability_index:.2f}")
    
    print(f"\n📌 Simulation Info:")
    print(f"  Simulations: {result.num_simulations}")
    print(f"  Block Size: {result.block_size}")
    
    print(f"{'='*60}\n")


def generate_monte_carlo_report(result: MonteCarloResult) -> str:
    """Generate structured Monte Carlo report.
    
    Args:
        result: MonteCarloResult
        
    Returns:
        Formatted report string
    """
    report = f"""
MONTE CARLO ANALYSIS REPORT
{'='*60}

METHODOLOGY
-----------
- Simulations: {result.num_simulations:,}
- Block Size: {result.block_size} (preserves autocorrelation)
- Method: Block permutation

RETURNS ANALYSIS
----------------
Expected Return: {result.mean_return:.2%}
Median Return: {result.median_return:.2%}
Standard Deviation: {result.std_return:.2%}

Confidence Intervals:
  95% CI: {result.ci_95_lower:.2%} to {result.ci_95_upper:.2%}
  99% CI: {result.ci_99_lower:.2%} to {result.ci_99_upper:.2%}

DRAWDOWN ANALYSIS
-----------------
Expected Max Drawdown: {result.mean_max_dd:.2%}
Median Max Drawdown: {result.median_max_dd:.2%}
Worst Case Drawdown: {result.worst_dd:.2%}
95th Percentile: {result.dd_95_percentile:.2%}

RISK ASSESSMENT
---------------
Risk of Ruin (50% loss): {result.risk_of_ruin:.2%}
Probability of Profit: {result.probability_of_profit:.2%}

PERFORMANCE STABILITY
--------------------
Sharpe Ratio (mean): {result.mean_sharpe:.2f}
Sharpe 95% CI: {result.sharpe_95_lower:.2f} to {result.sharpe_95_upper:.2f}

Consistency Score: {result.consistency_score:.2%}
Stability Index: {result.stability_index:.2f}

INTERPRETATION
--------------
"""
    
    # Add interpretation
    if result.risk_of_ruin > 0.05:
        report += f"⚠️  HIGH RISK: {result.risk_of_ruin:.1%} chance of 50% loss\n"
    else:
        report += f"✅ LOW RISK: {result.risk_of_ruin:.1%} chance of 50% loss\n"
    
    if result.probability_of_profit > 0.7:
        report += f"✅ HIGH CONFIDENCE: {result.probability_of_profit:.0%} probability of profit\n"
    elif result.probability_of_profit > 0.5:
        report += f"➡️  MODERATE: {result.probability_of_profit:.0%} probability of profit\n"
    else:
        report += f"⚠️  LOW CONFIDENCE: {result.probability_of_profit:.0%} probability of profit\n"
    
    if result.stability_index > 2.0:
        report += f"✅ HIGH STABILITY: Index = {result.stability_index:.2f}\n"
    elif result.stability_index > 1.0:
        report += f"➡️  MODERATE STABILITY: Index = {result.stability_index:.2f}\n"
    else:
        report += f"⚠️  LOW STABILITY: Index = {result.stability_index:.2f}\n"
    
    report += f"\n{'='*60}\n"
    
    return report

