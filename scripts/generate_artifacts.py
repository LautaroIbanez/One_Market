"""Generate artifacts for One Market platform.

This script generates example artifacts including:
- recommendations.csv (last 14 days)
- metrics.json
- Dashboard screenshots
"""
import asyncio
import json
import csv
import pandas as pd
from datetime import datetime, timezone, timedelta
from pathlib import Path
import logging

from app.service.daily_recommendation import DailyRecommendationService
from app.api.routes.backtest import UnifiedBacktestClient
from app.api.routes.recommendation import RecommendationClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ArtifactGenerator:
    """Generate artifacts for One Market platform."""
    
    def __init__(self):
        """Initialize artifact generator."""
        self.recommendation_service = DailyRecommendationService()
        self.backtest_client = UnifiedBacktestClient()
        self.recommendation_client = RecommendationClient()
        self.output_dir = Path("artifacts")
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_recommendations_csv(self, symbol: str = "BTC/USDT", days: int = 14):
        """Generate recommendations CSV for last N days.
        
        Args:
            symbol: Trading symbol
            days: Number of days to generate
        """
        logger.info(f"Generating recommendations CSV for {symbol} ({days} days)")
        
        # Generate recommendations for last N days
        recommendations = []
        end_date = datetime.now(timezone.utc)
        
        for i in range(days):
            date = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
            
            try:
                recommendation = self.recommendation_service.get_daily_recommendation(symbol, date)
                recommendations.append({
                    'date': recommendation.date,
                    'symbol': recommendation.symbol,
                    'timeframe': recommendation.timeframe,
                    'direction': recommendation.direction.value,
                    'entry_price': recommendation.entry_price,
                    'entry_band_min': recommendation.entry_band[0] if recommendation.entry_band else None,
                    'entry_band_max': recommendation.entry_band[1] if recommendation.entry_band else None,
                    'stop_loss': recommendation.stop_loss,
                    'take_profit': recommendation.take_profit,
                    'quantity': recommendation.quantity,
                    'risk_amount': recommendation.risk_amount,
                    'risk_percentage': recommendation.risk_percentage,
                    'rationale': recommendation.rationale,
                    'confidence': recommendation.confidence,
                    'dataset_hash': recommendation.dataset_hash,
                    'params_hash': recommendation.params_hash,
                    'created_at': recommendation.created_at.isoformat(),
                    'expires_at': recommendation.expires_at.isoformat() if recommendation.expires_at else None
                })
                
            except Exception as e:
                logger.warning(f"Failed to generate recommendation for {date}: {e}")
                # Add failed recommendation
                recommendations.append({
                    'date': date,
                    'symbol': symbol,
                    'timeframe': '1h',
                    'direction': 'HOLD',
                    'entry_price': None,
                    'entry_band_min': None,
                    'entry_band_max': None,
                    'stop_loss': None,
                    'take_profit': None,
                    'quantity': None,
                    'risk_amount': None,
                    'risk_percentage': None,
                    'rationale': f"Failed to generate: {str(e)}",
                    'confidence': 0,
                    'dataset_hash': 'error_hash',
                    'params_hash': 'error_params',
                    'created_at': datetime.utcnow().isoformat(),
                    'expires_at': None
                })
        
        # Write to CSV
        csv_path = self.output_dir / "recommendations.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            if recommendations:
                fieldnames = recommendations[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(recommendations)
        
        logger.info(f"Generated {len(recommendations)} recommendations in {csv_path}")
        return csv_path
    
    def generate_metrics_json(self, symbol: str = "BTC/USDT", timeframe: str = "1h"):
        """Generate metrics JSON with backtest results.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
        """
        logger.info(f"Generating metrics JSON for {symbol} {timeframe}")
        
        # Get available strategies
        strategies = self.backtest_client.get_available_strategies()
        if not strategies:
            strategies = ["ma_crossover", "rsi_regime_pullback", "trend_following_ema"]
        
        # Run backtests for each strategy
        metrics = {
            "symbol": symbol,
            "timeframe": timeframe,
            "generated_at": datetime.utcnow().isoformat(),
            "strategies": {}
        }
        
        for strategy in strategies:
            try:
                logger.info(f"Running backtest for {strategy}")
                result = self.backtest_client.run_backtest(
                    symbol=symbol,
                    timeframe=timeframe,
                    strategy=strategy,
                    initial_capital=10000.0,
                    risk_per_trade=0.02
                )
                
                if result:
                    metrics["strategies"][strategy] = {
                        "total_return": result["total_return"],
                        "cagr": result["cagr"],
                        "sharpe_ratio": result["sharpe_ratio"],
                        "max_drawdown": result["max_drawdown"],
                        "win_rate": result["win_rate"],
                        "profit_factor": result["profit_factor"],
                        "expectancy": result["expectancy"],
                        "total_trades": result["total_trades"],
                        "winning_trades": result["winning_trades"],
                        "losing_trades": result["losing_trades"],
                        "avg_win": result["avg_win"],
                        "avg_loss": result["avg_loss"],
                        "volatility": result["volatility"],
                        "calmar_ratio": result["calmar_ratio"],
                        "sortino_ratio": result["sortino_ratio"],
                        "initial_capital": result["initial_capital"],
                        "final_capital": result["final_capital"],
                        "profit": result["profit"],
                        "execution_time": result["execution_time"]
                    }
                else:
                    metrics["strategies"][strategy] = {
                        "error": "Backtest failed"
                    }
                    
            except Exception as e:
                logger.error(f"Error running backtest for {strategy}: {e}")
                metrics["strategies"][strategy] = {
                    "error": str(e)
                }
        
        # Write to JSON
        json_path = self.output_dir / "metrics.json"
        with open(json_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(metrics, jsonfile, indent=2, ensure_ascii=False)
        
        logger.info(f"Generated metrics JSON in {json_path}")
        return json_path
    
    def generate_dashboard_summary(self):
        """Generate dashboard summary with key metrics."""
        logger.info("Generating dashboard summary")
        
        # Get recommendation stats
        stats = self.recommendation_client.get_recommendation_stats("BTC/USDT")
        
        # Get backtest health
        backtest_health = self.backtest_client.get_backtest_health()
        
        # Create summary
        summary = {
            "generated_at": datetime.utcnow().isoformat(),
            "platform_status": {
                "backtest_service": backtest_health.get("status", "unknown"),
                "recommendation_service": "active" if stats else "unknown"
            },
            "recommendation_stats": stats,
            "available_strategies": self.backtest_client.get_available_strategies(),
            "data_quality": {
                "recommendations_generated": stats.get("total_recommendations", 0),
                "average_confidence": stats.get("average_confidence", 0),
                "date_range": stats.get("date_range", "N/A")
            }
        }
        
        # Write summary
        summary_path = self.output_dir / "dashboard_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(summary, jsonfile, indent=2, ensure_ascii=False)
        
        logger.info(f"Generated dashboard summary in {summary_path}")
        return summary_path
    
    def generate_all_artifacts(self):
        """Generate all artifacts."""
        logger.info("Starting artifact generation")
        
        artifacts = {}
        
        try:
            # Generate recommendations CSV
            artifacts["recommendations_csv"] = self.generate_recommendations_csv()
        except Exception as e:
            logger.error(f"Failed to generate recommendations CSV: {e}")
            artifacts["recommendations_csv"] = None
        
        try:
            # Generate metrics JSON
            artifacts["metrics_json"] = self.generate_metrics_json()
        except Exception as e:
            logger.error(f"Failed to generate metrics JSON: {e}")
            artifacts["metrics_json"] = None
        
        try:
            # Generate dashboard summary
            artifacts["dashboard_summary"] = self.generate_dashboard_summary()
        except Exception as e:
            logger.error(f"Failed to generate dashboard summary: {e}")
            artifacts["dashboard_summary"] = None
        
        # Create artifacts manifest
        manifest = {
            "generated_at": datetime.utcnow().isoformat(),
            "artifacts": artifacts,
            "status": "completed"
        }
        
        manifest_path = self.output_dir / "artifacts_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(manifest, jsonfile, indent=2, ensure_ascii=False)
        
        logger.info(f"Artifact generation completed. Manifest: {manifest_path}")
        return artifacts


def main():
    """Main function to generate artifacts."""
    generator = ArtifactGenerator()
    artifacts = generator.generate_all_artifacts()
    
    print("\n" + "="*50)
    print("ARTIFACTS GENERATED")
    print("="*50)
    
    for name, path in artifacts.items():
        if path:
            print(f"✅ {name}: {path}")
        else:
            print(f"❌ {name}: Failed to generate")
    
    print(f"\nAll artifacts saved in: {generator.output_dir}")
    print("="*50)


if __name__ == "__main__":
    main()
