"""
Package Giao diện các Trang Chức năng (UI Pages Package)
"""
from src.ui.pages.market_overview import render_market_overview_page
from src.ui.pages.screener_page import render_screener_page
from src.ui.pages.watchlist_page import render_watchlist_page
from src.ui.pages.detail_analysis import render_detail_analysis_page
from src.ui.pages.portfolio_risk_page import render_portfolio_risk_page
from src.ui.pages.report_page import render_report_page

__all__ = [
    "render_market_overview_page",
    "render_screener_page",
    "render_watchlist_page",
    "render_detail_analysis_page",
    "render_portfolio_risk_page",
    "render_report_page",
]

