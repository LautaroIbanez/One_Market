import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from app.service.daily_recommendation import DailyRecommendationService

service = DailyRecommendationService()
rec = service.get_daily_recommendation("BTC/USDT", "2024-01-15", use_strategy_ranking=False)

print("Direction:", rec.direction)
print("Confidence:", rec.confidence)
print("Rationale:", rec.rationale)
print("Entry Price:", rec.entry_price)
