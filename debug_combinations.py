#!/usr/bin/env python3
"""Debug script to test strategy combinations."""

from app.service.strategy_orchestrator import StrategyOrchestrator

def test_combinations():
    """Test strategy combinations for 1d."""
    print("=== Testing Strategy Combinations ===")
    
    orchestrator = StrategyOrchestrator()
    
    # Test 1d combinations
    print("\n--- Testing 1d combinations ---")
    results = orchestrator.run_strategy_combinations('BTC/USDT', '1d')
    print(f"Combination results: {len(results)} combinations")
    
    for result in results:
        print(f"- {result.strategy_name}: {result.total_trades} trades, Sharpe={result.sharpe_ratio:.2f}")
    
    # Test 4h combinations
    print("\n--- Testing 4h combinations ---")
    results = orchestrator.run_strategy_combinations('BTC/USDT', '4h')
    print(f"Combination results: {len(results)} combinations")
    
    for result in results:
        print(f"- {result.strategy_name}: {result.total_trades} trades, Sharpe={result.sharpe_ratio:.2f}")

if __name__ == "__main__":
    test_combinations()
