"""
Module Giao diện & Đồ thị Trực quan hóa (UI Components Facade)
Tập hợp và tái xuất (re-export) các biểu đồ tài chính và widget giao diện
được module hóa chuyên sâu vào src/ui/charts/:
- technical_charts: Nến Candlestick & Volume Profile POC
- forecast_charts: Monte Carlo Fan Chart & Multi-model ML Comparison
- market_charts: Market Breadth, Sector Treemap & Valuation Bands
"""
from src.ui.charts import (
    create_candlestick_chart,
    create_volume_profile_chart,
    render_tradingview_widget,
    render_lightweight_tv_chart,
    create_forecast_chart,
    create_multi_model_comparison_chart,
    create_ml_forecast_chart,
    create_feature_importance_chart,
    create_market_breadth_card,
    create_sector_treemap_chart,
    create_valuation_bands_chart,
)

__all__ = [
    "create_candlestick_chart",
    "create_volume_profile_chart",
    "render_tradingview_widget",
    "render_lightweight_tv_chart",
    "create_forecast_chart",
    "create_multi_model_comparison_chart",
    "create_ml_forecast_chart",
    "create_feature_importance_chart",
    "create_market_breadth_card",
    "create_sector_treemap_chart",
    "create_valuation_bands_chart",
]
