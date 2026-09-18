"""
Module Bộ đệm Dữ liệu Streamlit (Data Caching Layer)
Cung cấp các hàm tải dữ liệu và phân tích được tối ưu hóa với @st.cache_data,
giúp chuyển đổi giữa các trang và các tab mượt mà, hạn chế tối đa độ trễ.
"""
from typing import Dict, Any, Tuple, Optional, List
import streamlit as st

from src.database.tinydb_manager import watchlist_db
from src.data.stock_data import stock_engine
from src.data.market_data import market_engine
from src.data.macro_data import macro_engine
from src.data.fundamental_data import fundamental_engine
from src.analysis.indicators import calculate_indicators, generate_technical_signals, calculate_stock_beta
from src.analysis.forecasting import forecast_price_trend
from src.analysis.ml_forecasting import train_and_forecast_ml
from src.reporting.report_builder import generate_ticker_report_html, generate_ticker_report_markdown


@st.cache_data(ttl=15)
def get_cached_quotes_map(tickers_tuple: Tuple[str, ...]) -> Dict[str, Any]:
    """Lấy snapshot bảng giá theo batch cho nhiều mã và lưu đệm 15s để chuyển trang mượt mà"""
    if not tickers_tuple:
        return {}
    quotes = stock_engine.get_quotes_batch(list(tickers_tuple))
    return {q["ticker"]: q for q in quotes}


@st.cache_data(ttl=30)
def get_cached_market_overview() -> Dict[str, Any]:
    """Lấy chỉ số VN-Index, VN30, HNX và độ rộng thị trường (lưu đệm 30s)"""
    return market_engine.get_market_overview()


@st.cache_data(ttl=300)
def get_cached_macro_data() -> Dict[str, Any]:
    """Lấy dữ liệu kinh tế vĩ mô, lãi suất điều hành, CPI, GDP và tỷ giá USD/VND (lưu đệm 300s)"""
    return macro_engine.get_macro_indicators()


@st.cache_data(ttl=60)
def get_cached_institutional_flow(quotes_tuple: Tuple[Any, ...]) -> Dict[str, Any]:
    """Lấy số liệu mua/bán ròng của Khối ngoại và Khối Tự doanh (lưu đệm 60s)"""
    q_list = list(quotes_tuple) if quotes_tuple else []
    return macro_engine.get_institutional_flow(q_list)


@st.cache_data(ttl=120)
def get_stock_technical_summary(ticker: str) -> Optional[Dict[str, Any]]:
    """Tính toán nhanh chỉ báo kỹ thuật, tín hiệu và các ngưỡng hỗ trợ/kháng cự (lưu đệm 120s)"""
    try:
        df = stock_engine.get_historical_ohlcv(ticker, days=90)
        if df.empty or len(df) < 15:
            return None
        df_ind = calculate_indicators(df)
        sig = generate_technical_signals(df_ind)
        latest = df_ind.iloc[-1]
        rsi = float(latest.get("RSI14", 50.0))
        sma20 = float(latest.get("SMA20", latest["close"]))
        close_p = float(latest["close"])
        return {
            "action": sig["action"],
            "score": sig["score"],
            "reasons": sig.get("reasons", []),
            "support": float(sig.get("support", 0.0)),
            "resistance": float(sig.get("resistance", 0.0)),
            "rsi": rsi,
            "sma20": sma20,
            "ma20_status": "Trên SMA20 (Tích cực)" if close_p >= sma20 else "Dưới SMA20 (Thận trọng)",
            "primary_reason": sig.get("reasons", ["Tín hiệu đang cập nhật"])[0] if sig.get("reasons") else "Tín hiệu ổn định",
        }
    except Exception:
        return None


@st.cache_data(ttl=300)
def get_cached_ticker_analysis(ticker: str, days: int = 180, forecast_days: int = 7) -> Tuple[Any, ...]:
    """Huấn luyện mô hình, tính chỉ báo, Beta và định giá cơ bản (lưu đệm 300s tránh khựng khi đổi tab)"""
    df = stock_engine.get_historical_ohlcv(ticker, days=days)
    df_ind = calculate_indicators(df)
    signals = generate_technical_signals(df_ind)
    beta_info = calculate_stock_beta(df)
    forecast = forecast_price_trend(df_ind, forecast_days=forecast_days)
    ml_result = train_and_forecast_ml(df_ind, forecast_days=forecast_days, target_ticker=ticker)
    return df, df_ind, signals, forecast, ml_result, beta_info


@st.cache_data(ttl=300)
def get_cached_report_content(rep_ticker: str) -> Tuple[str, str]:
    """Tổng hợp nội dung báo cáo HTML/Markdown kèm FA và Beta (lưu đệm 300s)"""
    quote = stock_engine.get_realtime_quote(rep_ticker)
    df = stock_engine.get_historical_ohlcv(rep_ticker, days=180)
    df_ind = calculate_indicators(df)
    signals = generate_technical_signals(df_ind)
    beta_info = calculate_stock_beta(df)
    fund_info = fundamental_engine.get_stock_fundamentals(rep_ticker, quote["price"])
    forecast = forecast_price_trend(df_ind, forecast_days=7)
    wl_info = watchlist_db.get_by_ticker(rep_ticker)
    md_report = generate_ticker_report_markdown(rep_ticker, quote, signals, forecast, wl_info, fund_info=fund_info, beta_info=beta_info)
    html_report = generate_ticker_report_html(rep_ticker, quote, signals, forecast, wl_info, fund_info=fund_info, beta_info=beta_info)
    return md_report, html_report


@st.cache_data(ttl=60)
def get_cached_sentiment_and_margin() -> Dict[str, Any]:
    """Lấy dữ liệu đòn bẩy Margin, tài khoản F0 và phái sinh VN30F1M Basis & OI (lưu đệm 60s)"""
    from src.analysis.supply_demand import get_market_sentiment_and_margin
    return get_market_sentiment_and_margin()


@st.cache_data(ttl=60)
def get_cached_distribution_analysis() -> Dict[str, Any]:
    """Phân tích số phiên phân phối (Distribution Days) và phiên bùng nổ FTD của VN-Index (lưu đệm 60s)"""
    from src.analysis.supply_demand import analyze_distribution_and_ftd
    return analyze_distribution_and_ftd()


@st.cache_data(ttl=60)
def get_cached_sector_rotation(tickers_tuple: Tuple[str, ...]) -> Dict[str, Any]:
    """Phân tích luân chuyển dòng tiền ngành (Chu kỳ vs Phòng thủ vs Penny) và Leader stocks (lưu đệm 60s)"""
    from src.analysis.supply_demand import analyze_sector_rotation
    quotes_map = get_cached_quotes_map(tickers_tuple) if tickers_tuple else {}
    return analyze_sector_rotation(quotes_map)


@st.cache_data(ttl=120)
def get_cached_volume_profile(ticker: str) -> Dict[str, Any]:
    """Tính toán Volume Profile và vùng kiểm soát POC của cổ phiếu (lưu đệm 120s)"""
    from src.analysis.supply_demand import calculate_volume_profile
    df = stock_engine.get_historical_ohlcv(ticker, days=90)
    return calculate_volume_profile(df)


@st.cache_data(ttl=120)
def get_cached_vsa_patterns(ticker: str) -> List[Dict[str, Any]]:
    """Phát hiện các mẫu hình hành động giá VSA (No Supply, Bull/Bear Trap) (lưu đệm 120s)"""
    from src.analysis.supply_demand import detect_vsa_price_action_patterns
    df = stock_engine.get_historical_ohlcv(ticker, days=45)
    return detect_vsa_price_action_patterns(df)


@st.cache_data(ttl=300)
def get_cached_screener_results(min_rs: int = 70, min_roe: float = 12.0) -> List[Dict[str, Any]]:
    """Bộ lọc cổ phiếu CANSLIM / SEPA / RS O'Neil (lưu đệm 300s)"""
    from src.analysis.screener import screen_canslim_sepa_stocks
    return screen_canslim_sepa_stocks(min_rs=min_rs, min_roe=min_roe)


@st.cache_data(ttl=300)
def get_cached_corporate_events(ticker: Optional[str] = None) -> Dict[str, Any]:
    """Lịch sự kiện doanh nghiệp, GDKHQ cổ tức, đáo hạn phái sinh & ETF (lưu đệm 300s)"""
    from src.analysis.events_valuation import get_corporate_events_and_calendar
    return get_corporate_events_and_calendar(ticker=ticker)


@st.cache_data(ttl=300)
def get_cached_valuation_bands(ticker: str) -> Dict[str, Any]:
    """Tính toán dải định giá lịch sử P/E & P/B Bands (+-1SD, +-2SD) (lưu đệm 300s)"""
    from src.analysis.events_valuation import calculate_historical_valuation_bands
    quote = stock_engine.get_realtime_quote(ticker)
    fund = fundamental_engine.get_stock_fundamentals(ticker, quote["price"])
    return calculate_historical_valuation_bands(
        ticker=ticker,
        current_price=quote["price"],
        current_pe=fund.get("pe", 14.5),
        current_pb=fund.get("pb", 1.8),
    )


@st.cache_data(ttl=120)
def get_cached_technical_alerts(tickers_tuple: Tuple[str, ...]) -> List[Dict[str, Any]]:
    """Quét toàn diện các cảnh báo kỹ thuật (Breakout, Vi phạm MA, Phân kỳ RSI) cho danh mục (lưu đệm 120s)"""
    from src.analysis.alerts import (
        scan_technical_breakouts,
        scan_risk_violations,
        detect_rsi_macd_divergence,
        scan_unusual_institutional_activity,
    )
    alerts = []
    for sym in tickers_tuple:
        df = stock_engine.get_historical_ohlcv(sym, days=60)
        if df is not None and not df.empty:
            bo = scan_technical_breakouts(df, sym)
            if bo:
                alerts.append(bo)
            vio = scan_risk_violations(df, sym)
            if vio:
                alerts.append(vio)
            div = detect_rsi_macd_divergence(df, sym)
            if div:
                alerts.append(div)
        inst = scan_unusual_institutional_activity(sym)
        if inst:
            alerts.append(inst)
    return alerts


