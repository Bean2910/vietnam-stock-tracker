"""
Package Các Biểu Đồ & Widget Giao Diện (Charts Package)
Tách nhỏ từ components.py thành các module chuyên biệt:
- technical_charts: Nến Candlestick & Volume Profile POC
- forecast_charts: Monte Carlo Fan Chart & Multi-model ML Comparison
- market_charts: Market Breadth, Sector Treemap & Valuation Bands
"""
from src.ui.charts.technical_charts import (
    create_candlestick_chart,
    create_volume_profile_chart,
)
from src.ui.charts.forecast_charts import (
    create_forecast_chart,
    create_multi_model_comparison_chart,
    create_ml_forecast_chart,
    create_feature_importance_chart,
)
from src.ui.charts.market_charts import (
    create_market_breadth_card,
    create_sector_treemap_chart,
    create_valuation_bands_chart,
)

__all__ = [
    "create_candlestick_chart",
    "create_volume_profile_chart",
    "create_forecast_chart",
    "create_multi_model_comparison_chart",
    "create_ml_forecast_chart",
    "create_feature_importance_chart",
    "create_market_breadth_card",
    "create_sector_treemap_chart",
    "create_valuation_bands_chart",
]
