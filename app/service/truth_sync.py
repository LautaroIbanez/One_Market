"""Truth Data Synchronization - Compare real vs simulated performance.

This module:
- Imports executed trades from the trades table
- Compares them with backtest predictions
- Calculates divergence metrics
- Generates alerts when divergence exceeds thresholds
"""
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta, date
import logging

from app.service.paper_trading import PaperTradingDB
from app.data.schema import TradeRecord

logger = logging.getLogger(__name__)


class TruthSyncService:
    """Service for synchronizing and comparing real vs simulated performance."""
    
    def __init__(self):
        """Initialize truth sync service."""
        self.db = PaperTradingDB()
    
    def sync_daily_performance(
        self,
        target_date: Optional[date] = None,
        strategy_name: Optional[str] = None
    ) -> Dict:
        """Synchronize daily performance between real and simulated trades.
        
        Args:
            target_date: Date to sync (default: yesterday)
            strategy_name: Specific strategy to sync (default: all)
            
        Returns:
            Dictionary with sync results
        """
        if target_date is None:
            target_date = (datetime.now() - timedelta(days=1)).date()
        
        date_str = target_date.strftime('%Y-%m-%d')
        logger.info(f"Syncing performance for {date_str}")
        
        # Get executed trades for the date
        all_trades = self.db.get_all_trades()
        daily_trades = self._filter_trades_by_date(all_trades, target_date)
        
        if not daily_trades:
            logger.info(f"No trades found for {date_str}")
            return {"synced": 0, "alerts": []}
        
        # Group by symbol/timeframe/strategy
        grouped_trades = self._group_trades(daily_trades)
        
        synced_count = 0
        alerts = []
        
        for key, trades_list in grouped_trades.items():
            symbol, timeframe, strat_name = key
            
            # Skip if filtering by strategy and doesn't match
            if strategy_name and strat_name != strategy_name:
                continue
            
            # Calculate real performance
            real_metrics = self._calculate_real_metrics(trades_list)
            
            # Get simulated performance from rankings
            sim_metrics = self._get_simulated_metrics(symbol, timeframe, strat_name)
            
            # Save to truth_data table
            self.db.save_truth_data(
                date=date_str,
                symbol=symbol,
                timeframe=timeframe,
                strategy_name=strat_name,
                real_metrics=real_metrics,
                sim_metrics=sim_metrics
            )
            
            synced_count += 1
            
            # Check for alerts
            if real_metrics.get('pnl', 0) != 0 and sim_metrics.get('pnl', 0) != 0:
                pnl_div = abs((real_metrics['pnl'] - sim_metrics['pnl']) / sim_metrics['pnl']) * 100
                if pnl_div > 20:
                    alerts.append({
                        'date': date_str,
                        'strategy': strat_name,
                        'metric': 'pnl',
                        'divergence': pnl_div,
                        'real': real_metrics['pnl'],
                        'simulated': sim_metrics['pnl']
                    })
        
        logger.info(f"Synced {synced_count} strategy results, {len(alerts)} alerts")
        
        return {
            "synced": synced_count,
            "alerts": alerts,
            "date": date_str
        }
    
    def _filter_trades_by_date(
        self,
        trades: List[TradeRecord],
        target_date: date
    ) -> List[TradeRecord]:
        """Filter trades by entry date."""
        filtered = []
        for trade in trades:
            entry_dt = datetime.fromisoformat(trade.entry_time)
            if entry_dt.date() == target_date:
                filtered.append(trade)
        return filtered
    
    def _group_trades(
        self,
        trades: List[TradeRecord]
    ) -> Dict[tuple, List[TradeRecord]]:
        """Group trades by symbol/timeframe/strategy."""
        grouped = {}
        
        for trade in trades:
            # Extract strategy from decision_id or use default
            strategy_name = "Combined"  # TODO: Get from decision metadata
            
            key = (trade.symbol, "1h", strategy_name)  # TODO: Get timeframe from metadata
            
            if key not in grouped:
                grouped[key] = []
            
            grouped[key].append(trade)
        
        return grouped
    
    def _calculate_real_metrics(
        self,
        trades: List[TradeRecord]
    ) -> Dict:
        """Calculate metrics from real executed trades."""
        closed_trades = [t for t in trades if t.status == "closed" and t.realized_pnl is not None]
        
        if not closed_trades:
            return {
                'trades': len(trades),
                'wins': 0,
                'pnl': 0,
                'win_rate': 0
            }
        
        wins = [t for t in closed_trades if t.realized_pnl > 0]
        
        return {
            'trades': len(closed_trades),
            'wins': len(wins),
            'pnl': sum([t.realized_pnl for t in closed_trades]),
            'win_rate': len(wins) / len(closed_trades)
        }
    
    def _get_simulated_metrics(
        self,
        symbol: str,
        timeframe: str,
        strategy_name: str
    ) -> Dict:
        """Get simulated metrics from latest ranking."""
        rankings = self.db.get_strategy_rankings(symbol, timeframe, limit=10)
        
        # Find matching strategy
        for ranking in rankings:
            if ranking['strategy_name'] == strategy_name:
                # Estimate daily metrics from overall metrics
                # This is approximate - would need actual backtest trades for precision
                return {
                    'trades': ranking.get('total_trades', 0) / 90,  # Daily average
                    'wins': ranking.get('winning_trades', 0) / 90,
                    'pnl': ranking.get('expectancy', 0),  # Expected daily PnL
                    'win_rate': ranking.get('win_rate', 0)
                }
        
        # Default if not found
        return {'trades': 0, 'wins': 0, 'pnl': 0, 'win_rate': 0}
    
    def generate_daily_report(
        self,
        days: int = 1
    ) -> str:
        """Generate daily performance report comparing real vs simulated.
        
        Args:
            days: Number of days to include in report
            
        Returns:
            Formatted report string
        """
        report_lines = []
        report_lines.append("="*70)
        report_lines.append("  DAILY PERFORMANCE REPORT - Real vs Simulated")
        report_lines.append("="*70)
        report_lines.append("")
        
        # Get recent truth data
        for day in range(days):
            target_date = (datetime.now() - timedelta(days=day+1)).date()
            date_str = target_date.strftime('%Y-%m-%d')
            
            # Sync the day
            sync_result = self.sync_daily_performance(target_date)
            
            report_lines.append(f"📅 {date_str}")
            report_lines.append("-"*70)
            report_lines.append(f"  Synced strategies: {sync_result['synced']}")
            report_lines.append(f"  Alerts: {len(sync_result['alerts'])}")
            
            if sync_result['alerts']:
                for alert in sync_result['alerts']:
                    report_lines.append(f"  ⚠️ {alert['strategy']}: {alert['metric']} divergence {alert['divergence']:.1f}%")
            
            report_lines.append("")
        
        # Get overall alerts
        recent_alerts = self.db.get_truth_data_alerts(days=7)
        
        if recent_alerts:
            report_lines.append("🚨 ALERTAS RECIENTES (7 días)")
            report_lines.append("="*70)
            
            for alert in recent_alerts:
                report_lines.append(f"{alert['date']} - {alert['strategy_name']}")
                report_lines.append(f"  {alert['alert_reason']}")
                report_lines.append("")
        
        report_lines.append("="*70)
        
        return "\n".join(report_lines)


# Example usage
if __name__ == "__main__":
    service = TruthSyncService()
    
    # Sync yesterday's performance
    print("Synchronizing yesterday's performance...")
    result = service.sync_daily_performance()
    print(f"✅ Synced {result['synced']} strategies")
    
    if result['alerts']:
        print(f"⚠️ {len(result['alerts'])} alerts generated")
        for alert in result['alerts']:
            print(f"  - {alert['strategy']}: {alert['metric']} divergence {alert['divergence']:.1f}%")
    
    print()
    
    # Generate report
    print(service.generate_daily_report(days=3))

