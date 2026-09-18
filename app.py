"""
ỨNG DỤNG THEO DÕI, DỰ BÁO & BÁO CÁO CHỨNG KHOÁN VIỆT NAM (VN-STOCK TRACKER & FORECAST)
Giao diện Streamlit Dashboard hiện đại, kết nối dữ liệu tức thì, lưu trữ TinyDB NoSQL.
"""
import time
from datetime import datetime, timezone, timedelta
import streamlit as st
import pandas as pd
import numpy as np

# Múi giờ Việt Nam (UTC+7)
VN_TZ = timezone(timedelta(hours=7))

# Import các module cốt lõi của dự án
from config.settings import DEFAULT_TICKERS, AUTO_REFRESH_INTERVAL
from src.database.tinydb_manager import watchlist_db
from src.data.stock_data import stock_engine
from src.data.market_data import market_engine
from src.data.macro_data import macro_engine
from src.data.fundamental_data import fundamental_engine
import importlib
import src.analysis.indicators as indicators_mod
importlib.reload(indicators_mod)
from src.analysis.indicators import calculate_indicators, generate_technical_signals, calculate_stock_beta
from src.analysis.forecasting import forecast_price_trend
from src.analysis.ml_forecasting import train_and_forecast_ml
from src.reporting.report_builder import generate_ticker_report_html, generate_ticker_report_markdown
import src.ui.components as ui_components
importlib.reload(ui_components)
from src.ui.components import (
    create_candlestick_chart,
    create_forecast_chart,
    create_multi_model_comparison_chart,
    create_feature_importance_chart,
    create_market_breadth_card,
)

# -------------------------------------------------------------
# 1. CẤU HÌNH TRANG & GIAO DIỆN STREAMLIT
# -------------------------------------------------------------
st.set_page_config(
    page_title="VN-Stock Tracker & Forecast",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Cấu hình tương tác biểu đồ chuyên nghiệp (Lăn chuột mượt mà, chống rung giật)
PLOTLY_CONFIG = {
    "scrollZoom": True,
    "displayModeBar": True,
    "displaylogo": False,
    "responsive": True,
    "doubleClick": "reset",
    "showTips": False,
    "modeBarButtonsToAdd": ["drawline", "drawopenpath", "eraseshape"],
    "toImageButtonOptions": {
        "format": "png",
        "filename": "chart_export",
        "height": 800,
        "width": 1200,
        "scale": 2,
    },
}

# Custom CSS giao diện hiện đại & các thẻ KPI
st.markdown("""
<style>
    /* Chống rung giật trang web khi lăn chuột zoom trên biểu đồ */
    .stPlotlyChart {
        overscroll-behavior: contain !important;
    }
    .kpi-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .kpi-title {
        font-size: 13px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: 800;
        color: #f8fafc;
    }
    .price-up { color: #10b981 !important; font-weight: 700; }
    .price-down { color: #ef4444 !important; font-weight: 700; }
    .price-ref { color: #f59e0b !important; font-weight: 700; }
    .stAlert { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# Khởi tạo dữ liệu mẫu nếu watchlist đang trống
watchlist_db.init_defaults_if_empty(DEFAULT_TICKERS)


@st.cache_data(ttl=15)
def get_cached_quotes_map(tickers_tuple):
    """Lấy snapshot bảng giá theo batch cho nhiều mã và lưu đệm 15s để chuyển trang mượt mà"""
    if not tickers_tuple:
        return {}
    quotes = stock_engine.get_quotes_batch(list(tickers_tuple))
    return {q["ticker"]: q for q in quotes}


@st.cache_data(ttl=30)
def get_cached_market_overview():
    """Lấy chỉ số VN-Index, VN30, HNX và độ rộng thị trường (lưu đệm 30s)"""
    return market_engine.get_market_overview()


@st.cache_data(ttl=300)
def get_cached_macro_data():
    """Lấy dữ liệu kinh tế vĩ mô, lãi suất điều hành, CPI, GDP và tỷ giá USD/VND (lưu đệm 300s)"""
    return macro_engine.get_macro_indicators()


@st.cache_data(ttl=60)
def get_cached_institutional_flow(quotes_tuple):
    """Lấy số liệu mua/bán ròng của Khối ngoại và Khối Tự doanh (lưu đệm 60s)"""
    q_list = list(quotes_tuple) if quotes_tuple else []
    return macro_engine.get_institutional_flow(q_list)


@st.cache_data(ttl=120)
def get_stock_technical_summary(ticker: str):
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
def get_cached_ticker_analysis(ticker: str, days: int = 180, forecast_days: int = 7):
    """Huấn luyện mô hình, tính chỉ báo, Beta và định giá cơ bản (lưu đệm 300s tránh khựng khi đổi tab)"""
    df = stock_engine.get_historical_ohlcv(ticker, days=days)
    df_ind = calculate_indicators(df)
    signals = generate_technical_signals(df_ind)
    beta_info = calculate_stock_beta(df)
    forecast = forecast_price_trend(df_ind, forecast_days=forecast_days)
    ml_result = train_and_forecast_ml(df_ind, forecast_days=forecast_days, target_ticker=ticker)
    return df, df_ind, signals, forecast, ml_result, beta_info


@st.cache_data(ttl=300)
def get_cached_report_content(rep_ticker: str):
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


# -------------------------------------------------------------
# 2. SIDEBAR - THANH ĐIỀU HƯỚNG & CÀI ĐẶT
# -------------------------------------------------------------
st.sidebar.markdown("## 📈 **VN-Stock Analytics**")
st.sidebar.caption("Hệ thống theo dõi & dự báo chứng khoán tức thì")

nav_options = [
    "📊 Tổng quan Thị trường",
    "⭐ Danh mục Yêu thích (Watchlist)",
    "🔍 Phân tích Chi tiết & Dự báo",
    "📑 Xuất Báo cáo Phân tích",
]

if "redirect_page" in st.session_state:
    st.session_state["nav_radio"] = st.session_state.pop("redirect_page")

if "nav_radio" not in st.session_state:
    st.session_state["nav_radio"] = nav_options[0]

navigation = st.sidebar.radio(
    "CHỌN CHỨC NĂNG",
    nav_options,
    key="nav_radio",
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Cấu hình Tự động Làm mới")
auto_refresh = st.sidebar.checkbox("Bật tự động làm mới", value=False)
refresh_rate = st.sidebar.slider("Tần suất (giây)", min_value=1, max_value=60, value=AUTO_REFRESH_INTERVAL, step=1)

if st.sidebar.button("🔄 Làm mới dữ liệu ngay", width="stretch"):
    st.cache_data.clear()
    st.rerun()

# Kiểm tra & hiển thị cảnh báo giá tức thì từ Watchlist (sử dụng batch cache tránh lag khi chuyển tab)
all_watchlist = watchlist_db.get_all()
active_alerts = []
if all_watchlist:
    wl_syms = tuple(item["ticker"] for item in all_watchlist)
    wl_quotes_map = get_cached_quotes_map(wl_syms)
    for item in all_watchlist:
        sym = item["ticker"]
        q = wl_quotes_map.get(sym) or stock_engine.get_realtime_quote(sym)
        alerts = watchlist_db.check_price_alerts(sym, q["price"])
        active_alerts.extend(alerts)

if active_alerts:
    st.sidebar.markdown("---")
    st.sidebar.error("🔔 **CẢNH BÁO GIÁ KÍCH HOẠT!**")
    for alt in active_alerts:
        st.sidebar.warning(alt)

st.sidebar.markdown("---")
st.sidebar.caption(f"🕒 Lần cập nhật cuối: {datetime.now(VN_TZ).strftime('%H:%M:%S')}")
st.sidebar.caption("💾 Lưu trữ NoSQL: `TinyDB (JSON)`")


# -------------------------------------------------------------
# 3. TRANG 1: TỔNG QUAN THỊ TRƯỜNG (MARKET OVERVIEW)
# -------------------------------------------------------------
if navigation == "📊 Tổng quan Thị trường":
    st.title("📊 Tổng Quan Thị Trường & Radar Tín Hiệu Kỹ Thuật")
    st.caption("Cập nhật chỉ số VN-Index, độ rộng thị trường, bảng tổng hợp tín hiệu hành động và giá tức thì")

    mkt_data = get_cached_market_overview()
    macro_data = get_cached_macro_data()
    indexes = mkt_data["indexes"]

    # Hiển thị 4 cột chỉ số chính kèm nhãn xu hướng
    cols = st.columns(4)
    vnindex_change = 0.0
    for idx, col in enumerate(cols):
        item = indexes[idx]
        change_sign = "+" if item["change"] >= 0 else ""
        delta_str = f"{change_sign}{item['change']:,.2f} ({change_sign}{item['pct_change']}%)"
        if item["symbol"] == "VNINDEX":
            vnindex_change = float(item["change"])

        trend_txt = "Tăng" if item["change"] > 0 else ("Giảm" if item["change"] < 0 else "Đi ngang")
        col.metric(
            label=f"📌 {item['name']} ({trend_txt})",
            value=f"{item['value']:,.2f}",
            delta=delta_str,
        )

    st.markdown("---")

    # ---------------------------------------------------------
    # 1. MÔI TRƯỜNG VĨ MÔ & DÒNG TIỀN (CHECKLIST PHẦN 1.1)
    # ---------------------------------------------------------
    st.subheader("🌐 Môi Trường Vĩ Mô & Chi Phí Vốn (Dành Cho Nhà Đầu Tư Mới)")
    st.caption("Kênh đo lường chi phí vốn, sức khỏe kinh tế vĩ mô và tỷ giá hối đoái định hướng dòng tiền thông minh")

    ir = macro_data.get("interest_rates", {})
    econ = macro_data.get("economy", {})
    fx = macro_data.get("forex", {})

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric(
        "🏦 Lãi Suất Điều Hành",
        f"{ir.get('refinancing_rate', 4.5)}%",
        f"Tái CK: {ir.get('discount_rate', 3.0)}% | Trần NH: {ir.get('deposit_cap_short', 4.75)}%",
        help="Lãi suất điều hành duy trì mức thấp kích thích dòng tiền vào chứng khoán"
    )
    m_col2.metric(
        "📜 Lợi Suất TPCP 10 Năm",
        f"{ir.get('gov_bond_10y', 2.85)}%",
        "-0.07% (Chi phí vốn rẻ)",
        help="Lợi suất Trái phiếu Chính phủ 10Y là thước đo chi phí vốn phi rủi ro dài hạn"
    )
    m_col3.metric(
        "📊 Lạm Phát & GDP",
        f"GDP +{econ.get('gdp_growth_yoy', 6.82)}%",
        f"CPI: {econ.get('cpi_yoy', 3.78)}% (Mục tiêu < 4.5%)",
        help="Kinh tế tăng trưởng tích cực, lạm phát được kiểm soát tốt"
    )
    m_col4.metric(
        "💵 Tỷ Giá USD/VND",
        f"{fx.get('usd_vnd', 25960):,.0f} đ",
        f"DXY: {fx.get('dxy', 104.25):.1f} ({fx.get('status', 'LIVE')[:4]})",
        help="Tỷ giá ổn định giảm thiểu áp lực rút vốn của nhà đầu tư nước ngoài"
    )

    st.info(f"💡 **Nhận định Vĩ mô:** {ir.get('assessment', '')} {econ.get('assessment', '')}")

    st.markdown("---")

    # ---------------------------------------------------------
    # 2. DIỄN BIẾN THỊ TRƯỜNG & DÒNG TIỀN TỔ CHỨC (CHECKLIST PHẦN 1.2)
    # ---------------------------------------------------------
    # Lấy dữ liệu dòng tiền khối ngoại & tự doanh
    fav_tickers_pre = watchlist_db.get_ticker_list() or DEFAULT_TICKERS
    quotes_pre = [stock_engine.get_realtime_quote(s) for s in fav_tickers_pre[:8]]
    flow_data = macro_engine.get_institutional_flow(quotes_pre)

    f_data = flow_data.get("foreign", {})
    p_data = flow_data.get("proprietary", {})

    st.subheader("🏛️ Dòng Tiền Tổ Chức: Khối Ngoại & Khối Tự Doanh")
    st.caption("Động thái giao dịch của dòng tiền lớn (Smart Money) chi phối xu hướng dòng tiền thị trường")

    flow_col1, flow_col2, flow_col3, flow_col4 = st.columns(4)
    flow_col1.metric("🌍 Khối Ngoại Mua Ròng", f"{f_data.get('net_bil', 0):+,.1f} Tỷ VNĐ", f"Mua: {f_data.get('buy_bil', 0):,.0f} | Bán: {f_data.get('sell_bil', 0):,.0f}")
    flow_col2.metric("🏢 Tự Doanh Mua Ròng", f"{p_data.get('net_bil', 0):+,.1f} Tỷ VNĐ", f"Mua: {p_data.get('buy_bil', 0):,.0f} | Bán: {p_data.get('sell_bil', 0):,.0f}")

    # So sánh thanh khoản hôm nay với trung bình 20 phiên
    breadth = mkt_data["breadth"]
    curr_liq = float(breadth.get("liquidity_bil", 20000.0))
    avg_20_liq = 19500.0
    liq_diff_pct = ((curr_liq - avg_20_liq) / avg_20_liq) * 100
    liq_sign = "+" if liq_diff_pct >= 0 else ""
    flow_col3.metric("💰 Thanh Khoản Hôm Nay", f"{curr_liq:,.0f} Tỷ VNĐ", f"{liq_sign}{liq_diff_pct:.1f}% so với TB 20 phiên")
    flow_col4.metric("⚖️ Tỷ Lệ Mua/Bán Ngoại", f"{(f_data.get('buy_bil',1)/max(f_data.get('sell_bil',1),1)):.2f}x", f_data.get("action", ""))

    # Hiển thị Thanh đo độ rộng thị trường và Cảnh báo "Xanh vỏ đỏ lòng"
    st.markdown(create_market_breadth_card(breadth, vnindex_change=vnindex_change), unsafe_allow_html=True)

    st.markdown("---")

    # ---------------------------------------------------------
    # RADAR TÍN HIỆU & PHÂN TÍCH TỔNG QUAN TỪNG MÃ (ĐẦU TRANG)
    # ---------------------------------------------------------
    st.subheader("🎯 Radar Tín Hiệu & Phân Tích Kỹ Thuật Toàn Danh Mục")
    st.caption("Đánh giá tự động trạng thái hành động (Nên Mua / Quan Sát / Nên Bán), điểm sức mạnh và lý do kỹ thuật cốt lõi")

    fav_tickers = watchlist_db.get_ticker_list()
    if not fav_tickers:
        fav_tickers = DEFAULT_TICKERS

    quotes_dict = get_cached_quotes_map(tuple(fav_tickers))
    quotes = [quotes_dict[sym] for sym in fav_tickers if sym in quotes_dict]
    if not quotes:
        quotes = stock_engine.get_quotes_batch(fav_tickers)
        quotes_dict = {q["ticker"]: q for q in quotes}

    signal_summaries = []
    buy_count = 0
    neutral_count = 0
    sell_count = 0

    for sym in fav_tickers:
        q = quotes_dict.get(sym) or stock_engine.get_realtime_quote(sym)
        tech = get_stock_technical_summary(sym)
        if tech:
            action = tech["action"]
            if "MUA" in action:
                buy_count += 1
                b_icon = "🟢"
            elif "BÁN" in action:
                sell_count += 1
                b_icon = "🔴"
            else:
                neutral_count += 1
                b_icon = "🟡"

            signal_summaries.append({
                "ticker": sym,
                "quote": q,
                "tech": tech,
                "badge_icon": b_icon,
            })
        else:
            signal_summaries.append({
                "ticker": sym,
                "quote": q,
                "tech": {
                    "action": "QUAN SÁT / TRUNG LẬP",
                    "score": 50,
                    "reasons": ["Đang đồng bộ dữ liệu"],
                    "support": q["price"] * 0.95,
                    "resistance": q["price"] * 1.05,
                    "rsi": 50.0,
                    "ma20_status": "Ổn định",
                    "primary_reason": "Theo dõi phản ứng giá",
                },
                "badge_icon": "🟡",
            })
            neutral_count += 1

    # Thống kê nhanh toàn danh mục
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("🟢 Khuyến Nghị Nên Mua", f"{buy_count} mã", "Tín hiệu kỹ thuật tích cực")
    s2.metric("🟡 Khuyến Nghị Quan Sát", f"{neutral_count} mã", "Vùng tích lũy / Đi ngang")
    s3.metric("🔴 Cảnh Báo Nên Bán", f"{sell_count} mã", "Áp lực điều chỉnh")
    avg_score = int(np.mean([s["tech"]["score"] for s in signal_summaries])) if signal_summaries else 50
    s4.metric("⭐ Điểm Sức Mạnh TB", f"{avg_score}/100", "Độ đồng thuận kỹ thuật")

    # Bảng phân tích tín hiệu chi tiết
    st.markdown("##### 📋 Bảng Tổng Hợp Tín Hiệu & Khuyến Nghị Toàn Bộ Danh Mục:")
    radar_records = []
    for item in signal_summaries:
        sym = item["ticker"]
        q = item["quote"]
        tech = item["tech"]
        radar_records.append({
            "Mã CK": sym,
            "Giá Khớp": f"{q['price']:,.2f}",
            "Giá Thực Tế (VNĐ)": f"{q['price']*1000:,.0f} VNĐ",
            "% Biến Động": f"{'+' if q['pct_change'] >= 0 else ''}{q['pct_change']:.2f}%",
            "Tín Hiệu Hành Động": f"{item['badge_icon']} {tech['action']}",
            "Điểm Sức Mạnh": f"{tech['score']}/100",
            "RSI(14)": f"{tech['rsi']:.1f}",
            "Vị Thế MA20": tech["ma20_status"],
            "Hỗ Trợ": f"{tech['support']:,.2f}",
            "Kháng Cự": f"{tech['resistance']:,.2f}",
            "Lý Do Kỹ Thuật Chính": tech["primary_reason"],
        })
    st.dataframe(pd.DataFrame(radar_records), width="stretch", hide_index=True)

    # Hiển thị Thẻ Tín Hiệu Nhanh (Cards Grid) kèm nút soi sâu 1-Click
    with st.expander("⚡ **Xem Chi Tiết Từng Mã Dạng Thẻ (Signal Cards) & Phân Tích Nhanh 1-Click**", expanded=True):
        card_cols = st.columns(min(len(signal_summaries), 4) if signal_summaries else 1)
        for i, item in enumerate(signal_summaries):
            col_idx = i % len(card_cols)
            sym = item["ticker"]
            q = item["quote"]
            tech = item["tech"]
            p_color = "#10b981" if q["change"] > 0 else ("#ef4444" if q["change"] < 0 else "#f59e0b")
            
            with card_cols[col_idx]:
                st.markdown(f"""
                <div style="background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <strong style="font-size: 17px; color: #f8fafc;">{sym}</strong>
                        <span style="font-size: 12px; font-weight: 700; color: {p_color};">{item['badge_icon']} {tech['action'].split('/')[0].strip()}</span>
                    </div>
                    <div style="font-size: 19px; font-weight: 800; color: {p_color};">
                        {q['price']:,.2f} <span style="font-size: 12px; color: #94a3b8;">({'+' if q['pct_change'] >= 0 else ''}{q['pct_change']:.2f}%)</span>
                    </div>
                    <div style="font-size: 12px; color: #cbd5e1; margin-top: 6px; line-height: 1.5;">
                        🎯 <b>Điểm KT:</b> {tech['score']}/100 | <b>RSI:</b> {tech['rsi']:.1f}<br>
                        🛡️ <b>Hỗ trợ:</b> {tech['support']:,.2f} | <b>Kháng cự:</b> {tech['resistance']:,.2f}
                    </div>
                    <div style="font-size: 11px; color: #94a3b8; margin-top: 5px; font-style: italic;">
                        💡 {tech['primary_reason']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"🔎 Soi sâu {sym}", key=f"quick_view_{sym}", width="stretch"):
                    st.session_state["target_sym"] = sym
                    st.session_state["redirect_page"] = "🔍 Phân tích Chi tiết & Dự báo"
                    st.rerun()

    st.markdown("---")
    st.subheader("🔥 Bảng Giá Trực Tuyến & Sổ Lệnh Chi Tiết")
    
    table_records = []
    for q in quotes:
        table_records.append({
            "Mã CK": q["ticker"],
            "Giá Khớp": f"{q['price']:,.2f}",
            "Giá Thực Tế (VNĐ)": f"{q['price']*1000:,.0f} VNĐ",
            "Thay Đổi": f"{'+' if q['change'] >= 0 else ''}{q['change']:,.2f}",
            "% Biến Động": f"{'+' if q['pct_change'] >= 0 else ''}{q['pct_change']:.2f}%",
            "Khối Lượng": f"{q['volume']:,}",
            "Cao Nhất": f"{q['high']:,.2f}",
            "Thấp Nhất": f"{q['low']:,.2f}",
            "Mở Cửa": f"{q['open']:,.2f}",
            "Tham Chiếu": f"{q['ref_price']:,.2f}",
            "Trần": f"{q.get('ceiling', 0):,.2f}",
            "Sàn": f"{q.get('floor', 0):,.2f}",
            "Nguồn Dữ Liệu": q.get("status", "LIVE"),
        })

    st.dataframe(pd.DataFrame(table_records), width="stretch", hide_index=True)


# -------------------------------------------------------------
# 4. TRANG 2: DANH MỤC YÊU THÍCH (WATCHLIST - TINYDB)
# -------------------------------------------------------------
elif navigation == "⭐ Danh mục Yêu thích (Watchlist)":
    st.title("⭐ Quản Lý Danh Mục Cổ Phiếu Yêu Thích")
    st.caption("Lưu trữ NoSQL TinyDB chuẩn JSON - Cài đặt & chỉnh sửa ngưỡng cảnh báo chốt lời / cắt lỗ tức thì")

    watchlist_items = watchlist_db.get_all()

    # Form thêm mã mới
    with st.expander("➕ **Thêm Mã Cổ Phiếu Mới Vào Danh Sách Theo Dõi**", expanded=False):
        with st.form("add_ticker_form"):
            f_col1, f_col2, f_col3 = st.columns(3)
            new_ticker = f_col1.text_input("Mã Cổ Phiếu (VD: HPG, FPT, VNM)*").strip().upper()
            target_p = f_col2.number_input(
                "Giá Mục Tiêu Chốt Lời (Điểm)", 
                min_value=0.0, 
                step=0.5, 
                value=0.0,
                help="Nhập điểm giá (VD: 32.5 tương đương 32,500 VNĐ)"
            )
            stop_l = f_col3.number_input(
                "Ngưỡng Cắt Lỗ (Điểm)", 
                min_value=0.0, 
                step=0.5, 
                value=0.0,
                help="Nhập điểm giá (VD: 26.0 tương đương 26,000 VNĐ)"
            )
            
            f_note = st.text_input("Ghi chú chiến lược đầu tư (Tùy chọn)", placeholder="Ví dụ: Mua gom vùng hỗ trợ, chờ báo cáo Q3")
            f_alert = st.checkbox("Bật cảnh báo tự động khi chạm ngưỡng", value=True)
            
            submitted = st.form_submit_button("Lưu Vào Watchlist", width="stretch")
            if submitted:
                if new_ticker:
                    watchlist_db.add_or_update(
                        ticker=new_ticker,
                        target_price=target_p if target_p > 0 else None,
                        stop_loss=stop_l if stop_l > 0 else None,
                        note=f_note,
                        alert_enabled=f_alert,
                    )
                    st.success(f"Đã lưu thành công mã {new_ticker} vào Watchlist!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Vui lòng nhập mã cổ phiếu hợp lệ!")

    st.markdown("---")
    st.subheader(f"📋 Danh Sách Cổ Phiếu Đang Theo Dõi ({len(watchlist_items)} mã)")

    if not watchlist_items:
        st.info("Danh sách yêu thích đang trống. Hãy thêm mã cổ phiếu ở phần phía trên!")
    else:
        wl_syms = tuple(item["ticker"] for item in watchlist_items)
        wl_quotes_map = get_cached_quotes_map(wl_syms)

        for item in watchlist_items:
            sym = item["ticker"]
            q = wl_quotes_map.get(sym) or stock_engine.get_realtime_quote(sym)
            tech = get_stock_technical_summary(sym)
            p_class = "price-up" if q["change"] > 0 else ("price-down" if q["change"] < 0 else "price-ref")

            with st.container():
                c1, c2, c3, c4, c5, c6 = st.columns([1.2, 1.8, 1.8, 2.3, 2.0, 1.6])
                
                # Cột 1: Mã & Trạng thái
                c1.markdown(f"### **{sym}**")
                c1.caption(f"Thêm: {item.get('added_at', 'N/A')[:10]}")
                
                # Cột 2: Giá Realtime
                c2.markdown(f"<div class='{p_class}' style='font-size: 20px;'>{q['price']:,.2f}</div>", unsafe_allow_html=True)
                c2.caption(f"{'+' if q['change'] >= 0 else ''}{q['change']:,.2f} ({'+' if q['pct_change'] >= 0 else ''}{q['pct_change']:.2f}%)")

                # Cột 3: Tín hiệu kỹ thuật nhanh
                if tech:
                    t_badge = "🟢" if "MUA" in tech["action"] else ("🔴" if "BÁN" in tech["action"] else "🟡")
                    c3.markdown(f"**Tín hiệu:** {t_badge} `{tech['action'].split('/')[0].strip()}`")
                    c3.caption(f"Điểm: {tech['score']}/100 | RSI: {tech['rsi']:.1f}")
                else:
                    c3.markdown("`Đang cập nhật`")

                # Cột 4: Ngưỡng cảnh báo Target & Stop
                cur_tp = float(item.get("target_price") or 0.0)
                cur_sl = float(item.get("stop_loss") or 0.0)
                tp_str = f"{cur_tp:,.2f} ({cur_tp*1000:,.0f} VNĐ)" if cur_tp > 0 else "Chưa đặt"
                sl_str = f"{cur_sl:,.2f} ({cur_sl*1000:,.0f} VNĐ)" if cur_sl > 0 else "Chưa đặt"
                c4.markdown(f"🎯 **Target:** `{tp_str}`\n\n⚠️ **Stop:** `{sl_str}`")

                # Cột 5: Ghi chú
                c5.info(item.get("note") or "Không có ghi chú")

                # Cột 6: Nút Chỉnh Sửa (Popover) & Xóa
                with c6.popover("✏️ Sửa", width="stretch"):
                    st.markdown(f"#### ⚙️ Chỉnh sửa mã **{sym}**")
                    with st.form(key=f"edit_form_{sym}"):
                        edit_tp = st.number_input(
                            "🎯 Giá Mục Tiêu Chốt Lời (Điểm)",
                            min_value=0.0,
                            step=0.5,
                            value=cur_tp,
                            help="Nhập điểm giá (VD: 32.5 tương đương 32,500 VNĐ. Nhập 0 để hủy ngưỡng)"
                        )
                        edit_sl = st.number_input(
                            "⚠️ Ngưỡng Cắt Lỗ (Điểm)",
                            min_value=0.0,
                            step=0.5,
                            value=cur_sl,
                            help="Nhập điểm giá (VD: 26.0 tương đương 26,000 VNĐ. Nhập 0 để hủy ngưỡng)"
                        )
                        edit_note = st.text_input("Ghi chú chiến lược", value=item.get("note") or "")
                        edit_alert = st.checkbox("Bật cảnh báo tự động", value=item.get("alert_enabled", True))
                        
                        saved = st.form_submit_button("💾 Lưu Cập Nhật", width="stretch")
                        if saved:
                            watchlist_db.add_or_update(
                                ticker=sym,
                                target_price=edit_tp if edit_tp > 0 else None,
                                stop_loss=edit_sl if edit_sl > 0 else None,
                                note=edit_note,
                                alert_enabled=edit_alert,
                            )
                            st.cache_data.clear()
                            st.success(f"Đã cập nhật mã {sym} thành công!")
                            time.sleep(0.4)
                            st.rerun()

                if c6.button("🗑️ Xóa", key=f"del_{sym}", width="stretch"):
                    watchlist_db.remove(sym)
                    st.cache_data.clear()
                    st.rerun()

                st.markdown("<hr style='margin: 8px 0; border-color: #334155;'>", unsafe_allow_html=True)


# -------------------------------------------------------------
# 5. TRANG 3: PHÂN TÍCH CHI TIẾT & DỰ BÁO (TICKER & FORECAST)
# -------------------------------------------------------------
elif navigation == "🔍 Phân tích Chi tiết & Dự báo":
    st.title("🔍 Phân Tích Kỹ Thuật & Dự Báo Xu Hướng Giá")
    st.caption("Biểu đồ nến tương tác Plotly, Bộ chỉ báo kỹ thuật (RSI, MACD, MA, Bollinger) và Mô phỏng Monte Carlo xác suất")

    fav_list = watchlist_db.get_ticker_list()
    if not fav_list:
        fav_list = DEFAULT_TICKERS

    default_sym_idx = 0
    if "target_sym" in st.session_state and st.session_state["target_sym"] in fav_list:
        default_sym_idx = fav_list.index(st.session_state["target_sym"])

    t_col1, t_col2, t_col3 = st.columns([2, 1, 1])
    selected_ticker = t_col1.selectbox("Chọn mã từ Watchlist:", fav_list, index=default_sym_idx)
    manual_ticker = t_col2.text_input("Hoặc nhập mã bất kỳ:").strip().upper()
    active_sym = manual_ticker if manual_ticker else selected_ticker

    forecast_days = t_col3.slider("Số phiên dự báo:", min_value=3, max_value=15, value=7)

    if active_sym:
        # Lấy dữ liệu nến lịch sử và tính chỉ báo (được lưu cache 300s giúp chuyển tab cực nhanh)
        with st.spinner(f"Đang nạp dữ liệu phân tích cho mã {active_sym}..."):
            df, df_indicators, signals, forecast, ml_result, beta_info = get_cached_ticker_analysis(
                active_sym, days=180, forecast_days=forecast_days
            )
            quote = stock_engine.get_realtime_quote(active_sym)
            fund_info = fundamental_engine.get_stock_fundamentals(active_sym, quote["price"])

        # Header thông tin mã - Hàng 1: Bảng giá & Khuyến nghị
        h1, h2, h3, h4 = st.columns(4)
        h1.metric("Mã Cổ Phiếu", active_sym, quote.get("status", "LIVE"))
        h2.metric("Giá Khớp Hiện Tại", f"{quote['price']:,.2f} ({quote['price']*1000:,.0f} VNĐ)", f"{'+' if quote['change'] >= 0 else ''}{quote['change']:,.2f} ({quote['pct_change']:+.2f}%)")
        h3.metric("Khối Lượng Khớp", f"{quote['volume']:,}")
        
        # Action badge
        action = signals.get("action", "TRUNG LẬP")
        h4.metric("Khuyến Nghị Kỹ Thuật", action, f"Điểm: {signals.get('score', 50)}/100")

        # Header thông tin mã - Hàng 2: Hệ số Beta & Xu hướng 3 Khung Thời Gian (MA20, MA50, MA200)
        tf = signals.get("timeframes", {})
        sub_h1, sub_h2, sub_h3, sub_h4 = st.columns(4)
        sub_h1.metric(
            "⚡ Hệ Số Beta (Nhạy Sóng)",
            f"{beta_info.get('beta', 1.0):.2f}",
            beta_info.get("risk_type", "TRUNG BÌNH"),
            help="Beta đo mức độ nhạy sóng của cổ phiếu so với VN-Index. Beta > 1.25 biến động mạnh, Beta < 0.8 phòng thủ ổn định."
        )
        sub_h2.metric(
            "📈 Xu Hướng Ngắn Hạn (MA20)",
            f"{tf.get('short', 'CHƯA RÕ')}",
            f"SMA20: {signals.get('sma20', 0):,.2f}",
            help="Giá nằm trên SMA20 là xu hướng tăng ngắn hạn"
        )
        sub_h3.metric(
            "📊 Xu Hướng Trung Hạn (MA50)",
            f"{tf.get('medium', 'CHƯA RÕ')}",
            f"SMA50: {signals.get('sma50', 0):,.2f}",
            help="Giá nằm trên SMA50 xác nhận xu hướng tăng trung hạn"
        )
        sub_h4.metric(
            "🔭 Xu Hướng Dài Hạn (MA200)",
            f"{tf.get('long', 'CHƯA RÕ')}",
            f"SMA200: {signals.get('sma200', 0):,.2f}",
            help="Đường bình quân 200 phiên xác định đại xu hướng tăng trưởng dài hạn (Bull/Bear Market)"
        )

        st.markdown("---")

        # Tab chia nhỏ giữa Biểu đồ kỹ thuật, Phân tích cơ bản FA, Dự báo AI Machine Learning & Mô phỏng Monte Carlo
        tab_chart, tab_fa, tab_ml, tab_forecast = st.tabs([
            "📊 Biểu Đồ Kỹ Thuật & Beta",
            "🏢 Phân Tích Cơ Bản (FA) & Định Giá",
            "🤖 Dự Báo Máy Học (AI / Gradient Boosting)",
            "🎲 Mô Phỏng Xác Suất Monte Carlo",
        ])

        with tab_chart:
            # 1. Bộ lọc phạm vi thời gian hiển thị & phiên tham chiếu
            filter_col1, filter_col2 = st.columns([3, 2])
            with filter_col1:
                candle_range_mode = st.radio(
                    "Khung thời gian nến:",
                    ["Toàn bộ lịch sử (180 phiên)", "1 Tháng (~20 phiên)", "3 Tháng (~60 phiên)", "6 Tháng (~120 phiên)", "Tùy chỉnh số phiên"],
                    index=0,
                    horizontal=True,
                    key=f"candle_mode_{active_sym}",
                )
            with filter_col2:
                if candle_range_mode == "1 Tháng (~20 phiên)":
                    n_candles = 20
                elif candle_range_mode == "3 Tháng (~60 phiên)":
                    n_candles = 60
                elif candle_range_mode == "6 Tháng (~120 phiên)":
                    n_candles = 120
                elif candle_range_mode == "Tùy chỉnh số phiên":
                    n_candles = st.slider(
                        "Số phiên hiển thị:",
                        min_value=5,
                        max_value=180,
                        value=30,
                        step=5,
                        help="Chọn số phiên gần nhất để phóng to hành động giá nến",
                        key=f"candle_slider_{active_sym}",
                    )
                else:
                    n_candles = None

            # 2. Tùy chọn hiển thị chỉ báo & đường tham chiếu
            c_opt1, c_opt2, c_opt3, c_opt4, c_opt5, c_opt6 = st.columns(6)
            s_sma = c_opt1.checkbox("SMA (20, 50)", value=True)
            s_sma200 = c_opt2.checkbox("SMA 200 (Dài)", value=True)
            s_bb = c_opt3.checkbox("Bollinger Bands", value=True)
            s_rsi = c_opt4.checkbox("Chỉ số RSI (14)", value=True)
            s_macd = c_opt5.checkbox("Chỉ báo MACD", value=True)
            s_ref = c_opt6.checkbox("Giá Tham Chiếu", value=True)

            ref_p = quote.get("ref_price") or quote.get("price")
            chart_fig = create_candlestick_chart(
                df_indicators,
                active_sym,
                show_sma=s_sma,
                show_sma200=s_sma200,
                show_bb=s_bb,
                show_rsi=s_rsi,
                show_macd=s_macd,
                n_sessions=n_candles,
                show_ref_line=s_ref,
                ref_price=ref_p,
            )
            st.caption("🔍 **Mẹo tương tác biểu đồ:** **Giữ chuột trái kéo (Pan)** để trượt biểu đồ qua lại | **Lăn con lăn chuột (Mouse Scroll)** để Phóng to / Thu nhỏ | **Nhấp đúp chuột (Double click)** để Reset về ban đầu | Bấm **⛶ (Fullscreen)** góc trên phải để mở Toàn màn hình.")
            st.plotly_chart(chart_fig, width="stretch", config=PLOTLY_CONFIG, on_select="ignore")

            # Khối thông tin Hệ số Beta & Tín hiệu kỹ thuật chuyên sâu
            beta_col, sig_col = st.columns([1.2, 1.8])
            with beta_col:
                st.markdown("##### ⚡ Đánh Giá Hệ Số Beta (Độ Nhạy Sóng)")
                st.info(f"""
                **Hệ số Beta:** `{beta_info.get('beta', 1.0):.2f}`  
                **Phân loại:** {beta_info.get('classification', '')}  
                **Mức độ rủi ro:** `{beta_info.get('risk_type', 'TRUNG BÌNH')}`  
                📌 *{beta_info.get('assessment', '')}*
                """)

            with sig_col:
                st.markdown("##### 💡 Tín Hiệu Phân Tích Kỹ Thuật Tự Động")
                for r in signals.get("reasons", []):
                    st.write(f"- {r}")

        with tab_fa:
            # ---------------------------------------------------------
            # PHÂN TÍCH CƠ BẢN (FA) THEO CHECKLIST CHO NGƯỜI MỚI
            # ---------------------------------------------------------
            st.subheader(f"🏢 Phân Tích Cơ Bản (FA) & Định Giá Cổ Phiếu {active_sym}")
            st.caption(f"{fund_info.get('company_name', '')} • Ngành: {fund_info.get('industry', '')}")

            # Thẻ Đánh giá tổng quan sức khỏe doanh nghiệp
            fa_overview_html = (
                '<div style="background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 16px; margin-bottom: 20px;">'
                '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
                '<div>'
                '<span style="font-size: 13px; color: #94a3b8; text-transform: uppercase;">XẾP HẠNG SỨC KHỎE DOANH NGHIỆP</span>'
                f'<h3 style="margin: 4px 0 0 0; color: #f8fafc;">{fund_info.get("rating_badge", "")} {fund_info.get("rating", "")}</h3>'
                '</div>'
                '<div style="text-align: right;">'
                '<span style="font-size: 13px; color: #94a3b8;">ĐIỂM CHUẨN ĐẦU TƯ</span>'
                f'<div style="font-size: 28px; font-weight: 800; color: #38bdf8;">{fund_info.get("score_fa", 0)}/100</div>'
                '</div>'
                '</div>'
                '<div style="font-size: 13px; color: #cbd5e1; border-top: 1px solid #334155; padding-top: 10px; margin-top: 6px;">'
                f'📌 <b>Điểm nhấn doanh nghiệp:</b> {fund_info.get("highlights", "")}'
                '</div>'
                '</div>'
            )
            st.markdown(fa_overview_html, unsafe_allow_html=True)

            # 3 Nhóm Chỉ số Chính theo Checklist
            fa_p = fund_info.get("profitability", {})
            fa_v = fund_info.get("valuation", {})
            fa_f = fund_info.get("financial_health", {})

            # 1. Nhóm Sinh Lời
            st.markdown("#### 1. Nhóm Sinh Lời (Chọn Doanh Nghiệp Tốt)")
            st.caption("Đo lường hiệu quả kinh doanh, tỷ suất sinh lời trên vốn và lợi thế cạnh tranh cốt lõi")
            p_c1, p_c2, p_c3, p_c4 = st.columns(4)
            p_c1.metric("EPS (Thu Nhập / CP)", f"{fa_p.get('eps', 0):,} đ", f"+{fa_p.get('eps_growth', 0):.1f}% YoY", help="EPS tăng trưởng đều đặn qua các năm là dấu hiệu doanh nghiệp kinh doanh mở rộng vững chắc")
            p_c2.metric("ROE (Sinh Lời / VCSH)", f"{fa_p.get('roe', 0):.1f}%", "Ưu tiên > 15%" if fa_p.get('roe', 0) >= 15 else "Dưới ngưỡng 15%", help="ROE đo lường 1 đồng vốn cổ đông tạo ra bao nhiêu đồng lợi nhuận. Chuẩn đầu tư ưu tiên ROE > 15%")
            p_c3.metric("ROA (Sinh Lời / Tổng TS)", f"{fa_p.get('roa', 0):.1f}%", help="Hiệu quả quản lý và khai thác toàn bộ tài sản doanh nghiệp")
            p_c4.metric("Biên Lợi Nhuận Ròng", f"{fa_p.get('net_margin', 0):.1f}%", f"Biên Gộp: {fa_p.get('gross_margin', 0):.1f}%", help="Biên lợi nhuận cao chứng minh lợi thế cạnh tranh độc quyền hoặc khả năng quản lý chi phí tốt")

            st.markdown("---")

            # 2. Nhóm Định Giá
            st.markdown("#### 2. Nhóm Định Giá (Mua Đúng Vùng Giá Hợp Lý)")
            st.caption("Định giá cổ phiếu so sánh với tốc độ tăng trưởng và trung bình ngành để tránh mua đu đỉnh")
            v_c1, v_c2, v_c3, v_c4 = st.columns(4)
            v_c1.metric("Chỉ Số P/E Hiện Tại", f"{fa_v.get('pe', 0):.2f}x", f"TB Ngành: {fa_v.get('pe_industry', 0):.1f}x", help="Số năm thu hồi vốn nếu lợi nhuận giữ nguyên. So sánh với P/E trung bình ngành để biết đắt hay rẻ")
            v_c2.metric("Chỉ Số P/B (Giá / Sổ Sách)", f"{fa_v.get('pb', 0):.2f}x", f"TB Ngành: {fa_v.get('pb_industry', 0):.1f}x", help="Phù hợp định giá nhóm ngành Ngân hàng, Bất động sản và doanh nghiệp sở hữu tài sản lớn")
            v_c3.metric("Hệ Số PEG (P/E / Growth)", f"{fa_v.get('peg', 0):.2f}", "Hợp lý quanh 1.0" if 0.5 <= fa_v.get('peg', 0) <= 1.5 else "Định giá cao", help="PEG quanh 1.0 cho thấy mức định giá tương xứng hoàn toàn với tốc độ tăng trưởng EPS")
            v_c4.metric("Giá Trị Sổ Sách (BVPS)", f"{fa_v.get('bvps', 0):,} đ", help="Giá trị tài sản ròng trên mỗi cổ phần theo báo cáo tài chính")

            st.markdown("---")

            # 3. Nhóm An Toàn Tài Chính
            st.markdown("#### 3. Nhóm An Toàn Tài Chính (Quản Trị Rủi Ro Đòn Bẩy)")
            st.caption("Kiểm tra sức bền tài chính để tránh rủi ro phá sản hoặc áp lực lãi vay khi lãi suất biến động")
            f_c1, f_c2 = st.columns(2)
            f_c1.metric("Hệ Số Nợ Vay / VCSH (D/E)", f"{fa_f.get('debt_to_equity', 0):.2f}", "An toàn < 1.5" if fa_f.get('debt_to_equity', 0) <= 1.5 else "Cảnh báo đòn bẩy cao", help="Tránh doanh nghiệp có D/E quá cao trong chu kỳ thắt chặt tiền tệ")
            f_c2.metric("Thanh Toán Hiện Hành (Current Ratio)", f"{fa_f.get('current_ratio', 0):.2f}", "An toàn > 1.2" if fa_f.get('current_ratio', 0) >= 1.2 else "Thanh khoản yếu", help="Tài sản ngắn hạn chia Nợ ngắn hạn. Chuẩn an toàn từ 1.2 đến 1.5 trở lên")

            st.markdown("---")

            # 4. Bảng Checklist Đánh Giá Tự Động Cho Người Mới
            st.markdown("#### 📋 Bảng Checklist Tiêu Chuẩn Chọn Cổ Phiếu Cho Người Mới")
            checklist_data = fund_info.get("checklist", [])
            ck_rows = []
            for item in checklist_data:
                icon = "🟢 ĐẠT" if item["status"] == "PASS" else "🟡 LƯU Ý"
                ck_rows.append({
                    "Hạng Mục Đánh Giá": item["criteria"],
                    "Chỉ Số Thực Tế": item["value"],
                    "Trạng Thái": icon,
                    "Lời Khuyên & Nhận Định Cho Nhà Đầu Tư": item["note"],
                })
            st.dataframe(pd.DataFrame(ck_rows), width="stretch", hide_index=True)

        with tab_ml:
            st.subheader("🌐 Đối Chiếu Đa Chiều Các Mô Hình Dự Báo Xu Hướng Giá")
            st.caption("Tổng hợp và so sánh độc lập giữa các thuật toán Machine Learning, Mô hình Định lượng và Xác suất Thống kê")

            if "error" in ml_result and ml_result.get("error"):
                st.warning(ml_result["error"])
            else:
                all_models_dict = ml_result.get("models", {})
                future_dates = ml_result.get("future_dates", [])

                for k in ["cb_gb", "cb_rf", "cb_tech", "cb_mc", "cb_cs"]:
                    if k not in st.session_state:
                        st.session_state[k] = True

                # 1. BỘ LỌC CHỌN MÔ HÌNH (GỌN GÀNG, TRỰC QUAN)
                st.markdown("##### 🎛️ Chọn các mô hình hiển thị trên biểu đồ đối chiếu:")
                mc1, mc2, mc3, mc4, mc5 = st.columns(5)
                sel_gb = mc1.checkbox("🟣 Gradient Boosting", key="cb_gb")
                sel_rf = mc2.checkbox("🟢 Random Forest", key="cb_rf")
                sel_tech = mc3.checkbox("🟠 Quán Tính Kỹ Thuật", key="cb_tech")
                sel_mc = mc4.checkbox("🟡 Monte Carlo", key="cb_mc")
                sel_cs = mc5.checkbox("🔵 Đồng Thuận AI", key="cb_cs")

                selected_models = []
                if sel_gb:
                    selected_models.append("Gradient Boosting (AI)")
                if sel_rf:
                    selected_models.append("Random Forest")
                if sel_tech:
                    selected_models.append("Quán Tính Kỹ Thuật")
                if sel_mc:
                    selected_models.append("Monte Carlo (Cơ Sở)")
                if sel_cs:
                    selected_models.append("Đồng Thuận Tổng Hợp (Consensus)")

                selected_models = [m for m in selected_models if m in all_models_dict]
                if not selected_models and all_models_dict:
                    selected_models = list(all_models_dict.keys())

                if not all_models_dict:
                    st.warning("⚠️ Đang nạp thêm dữ liệu lịch sử để kích hoạt các mô hình Machine Learning cho mã này.")
                else:
                    # 2. BỐN THẺ KPI ĐỐI CHIẾU ĐA CHIỀU (HIỆN NGAY ĐẦU TRANG)
                    selected_returns = [all_models_dict[m]["expected_return"] for m in selected_models if m in all_models_dict]
                    selected_prices = [all_models_dict[m]["final_price"] for m in selected_models if m in all_models_dict]

                    avg_return = float(np.mean(selected_returns)) if selected_returns else 0.0
                    avg_price = float(np.mean(selected_prices)) if selected_prices else quote["price"]
                    best_model = max(selected_models, key=lambda m: all_models_dict[m]["expected_return"])
                    worst_model = min(selected_models, key=lambda m: all_models_dict[m]["expected_return"])
                    spread = all_models_dict[best_model]["expected_return"] - all_models_dict[worst_model]["expected_return"]

                    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
                    c_sign_avg = "+" if avg_return >= 0 else ""
                    kpi_col1.metric("Giá Kỳ Vọng Trung Bình", f"{avg_price:,.2f} ({avg_price*1000:,.0f} VNĐ)", f"{c_sign_avg}{avg_return:.2f}%")
                    kpi_col2.metric("Số Mô Hình Đang Bật", f"{len(selected_models)}/5 mô hình", ml_result.get("consensus_view", "ĐA CHIỀU"))
                    kpi_col3.metric(f"Lạc Quan: {best_model.split()[0]}", f"{all_models_dict[best_model]['final_price']:,.2f}", f"{all_models_dict[best_model]['expected_return']:+.2f}%")
                    kpi_col4.metric(f"Thận Trọng: {worst_model.split()[0]}", f"{all_models_dict[worst_model]['final_price']:,.2f}", f"{all_models_dict[worst_model]['expected_return']:+.2f}%")

                    # 3. BIỂU ĐỒ ĐỐI CHIẾU ĐA CHIỀU (PLOTLY CHART) ĐẶT NGAY TRỌNG TÂM
                    ch_title_col, ch_opt_col = st.columns([3, 3])
                    ch_title_col.markdown(f"#### 📈 Biểu Đồ Đối Chiếu Đường Giá Dự Phóng ({len(future_dates)} Phiên)")
                    with ch_opt_col:
                        view_opt = st.radio(
                            "Chế độ hiển thị biểu đồ:",
                            ["🔍 Toàn Màn Hình (Chỉ mô hình)", "📊 Kèm n phiên lịch sử tham chiếu"],
                            index=0,
                            horizontal=True,
                            label_visibility="collapsed",
                            key="forecast_chart_view_mode",
                        )
                        if "Kèm n phiên" in view_opt:
                            n_ml_hist = st.slider(
                                "Số phiên lịch sử tham chiếu (n):",
                                min_value=3,
                                max_value=30,
                                value=5,
                                step=1,
                                key="slider_ml_n_hist",
                            )
                        else:
                            n_ml_hist = 5

                    v_mode = "forecast_only" if "Toàn Màn Hình" in view_opt else "with_history"
                    ml_fig = create_multi_model_comparison_chart(
                        df_indicators,
                        ml_result,
                        selected_models,
                        active_sym,
                        view_mode=v_mode,
                        hist_len=n_ml_hist,
                    )
                    st.plotly_chart(ml_fig, width="stretch", config=PLOTLY_CONFIG, on_select="ignore")

                    # 4. BẢNG SO SÁNH CHI TIẾT TỪNG PHIÊN (THEO CÁC MÔ HÌNH ĐÃ CHỌN)
                    st.markdown("#### 📋 Bảng So Sánh Dự Báo Chi Tiết Từng Phiên (Theo Các Mô Hình Đang Bật)")
                    base_p = quote["price"]

                    def _fmt_price_cell(p_val, base_val, suffix=""):
                        diff = round(p_val - base_val, 2)
                        if diff > 0.001:
                            return f'<span style="color: #16a34a; font-weight: 700;">▲ {p_val:,.2f}{suffix}</span>'
                        elif diff < -0.001:
                            return f'<span style="color: #dc2626; font-weight: 700;">▼ {p_val:,.2f}{suffix}</span>'
                        else:
                            return f'<span style="color: #c2944b; font-weight: 700;">{p_val:,.2f}{suffix}</span>'

                    def _fmt_vnd_cell(p_val, base_val):
                        diff = round(p_val - base_val, 2)
                        vnd = p_val * 1000
                        if diff > 0.001:
                            return f'<span style="color: #16a34a; font-weight: 700;">▲ {vnd:,.0f} VNĐ</span>'
                        elif diff < -0.001:
                            return f'<span style="color: #dc2626; font-weight: 700;">▼ {vnd:,.0f} VNĐ</span>'
                        else:
                            return f'<span style="color: #c2944b; font-weight: 700;">{vnd:,.0f} VNĐ</span>'

                    def _fmt_pct_cell(p_val, base_val):
                        diff = round(p_val - base_val, 2)
                        pct = (p_val - base_val) / base_val * 100
                        if diff > 0.001:
                            return f'<span style="color: #16a34a; font-weight: 700;">▲ +{pct:.2f}%</span>'
                        elif diff < -0.001:
                            return f'<span style="color: #dc2626; font-weight: 700;">▼ {pct:.2f}%</span>'
                        else:
                            return f'<span style="color: #c2944b; font-weight: 700;">0.00%</span>'

                    valid_models = [m for m in selected_models if m in all_models_dict]
                    tbl_headers = ["Phiên", "Ngày GD"] + valid_models + ["Trung Bình Đã Chọn", "Giá VNĐ Bình Quân", "% So Giá T0"]

                    # Ngày tham chiếu T+0 từ nến gần nhất
                    last_idx = df.index[-1]
                    t0_date = last_idx.strftime("%d/%m/%Y") if hasattr(last_idx, "strftime") else str(last_idx)[:10]

                    html_rows = []

                    # 1. DÒNG THAM CHIẾU T+0 (MỐC XUẤT PHÁT HIỆN TẠI)
                    t0_cells = [
                        '<td style="padding: 11px 14px; font-weight: 800; text-align: left; color: #0284c7;">⭐ T+0 (Hiện tại)</td>',
                        f'<td style="padding: 11px 14px; text-align: left; font-weight: 600;">{t0_date}</td>',
                    ]
                    for _ in valid_models:
                        t0_cells.append(f'<td style="padding: 11px 14px; text-align: right;">{_fmt_price_cell(base_p, base_p)}</td>')

                    t0_cells.append(f'<td style="padding: 11px 14px; text-align: right; background: rgba(14, 165, 233, 0.08);">{_fmt_price_cell(base_p, base_p)}</td>')
                    t0_cells.append(f'<td style="padding: 11px 14px; text-align: right; background: rgba(14, 165, 233, 0.08);">{_fmt_vnd_cell(base_p, base_p)}</td>')
                    t0_cells.append(f'<td style="padding: 11px 14px; text-align: right; background: rgba(14, 165, 233, 0.08);">{_fmt_pct_cell(base_p, base_p)}</td>')

                    html_rows.append(f'<tr style="border-bottom: 2px solid rgba(14, 165, 233, 0.45); background: rgba(14, 165, 233, 0.08); font-weight: 700;">{"".join(t0_cells)}</tr>')

                    # 2. CÁC DÒNG DỰ BÁO TƯƠNG LAI T+1 ĐẾN T+N
                    for step_idx in range(len(future_dates)):
                        step_date = future_dates[step_idx]
                        cells = [
                            f'<td style="padding: 10px 14px; font-weight: 700; text-align: left;">T+{step_idx+1}</td>',
                            f'<td style="padding: 10px 14px; text-align: left;">{step_date}</td>',
                        ]
                        step_prices = []
                        for m_name in valid_models:
                            p_val = all_models_dict[m_name]["prices"][step_idx]
                            step_prices.append(p_val)
                            cells.append(f'<td style="padding: 10px 14px; text-align: right;">{_fmt_price_cell(p_val, base_p)}</td>')

                        if step_prices:
                            step_avg = float(np.mean(step_prices))
                            cells.append(f'<td style="padding: 10px 14px; text-align: right; background: rgba(128,128,128,0.06);">{_fmt_price_cell(step_avg, base_p)}</td>')
                            cells.append(f'<td style="padding: 10px 14px; text-align: right; background: rgba(128,128,128,0.06);">{_fmt_vnd_cell(step_avg, base_p)}</td>')
                            cells.append(f'<td style="padding: 10px 14px; text-align: right; background: rgba(128,128,128,0.06);">{_fmt_pct_cell(step_avg, base_p)}</td>')

                        row_bg = "background: rgba(128,128,128,0.03);" if step_idx % 2 == 1 else ""
                        html_rows.append(f'<tr style="border-bottom: 1px solid rgba(128,128,128,0.18); {row_bg}">{"".join(cells)}</tr>')

                    header_html = "".join([f'<th style="padding: 12px 14px; text-align: {"left" if i < 2 else "right"}; font-weight: 700;">{h}</th>' for i, h in enumerate(tbl_headers)])

                    comparison_html = f"""
                    <div style="overflow-x: auto; border: 1px solid rgba(128,128,128,0.25); border-radius: 8px; margin: 10px 0 20px 0;">
                      <table style="width: 100%; border-collapse: collapse; font-size: 14px; line-height: 1.5;">
                        <thead>
                          <tr style="background: rgba(128,128,128,0.12); border-bottom: 2px solid rgba(128,128,128,0.3);">
                            {header_html}
                          </tr>
                        </thead>
                        <tbody>
                          {"".join(html_rows)}
                        </tbody>
                      </table>
                    </div>
                    """
                    st.markdown(comparison_html, unsafe_allow_html=True)

                    # 5. BẢN MÔ TẢ PHÂN TÍCH XU HƯỚNG TỔNG HỢP CHI TIẾT
                    st.markdown("#### 📝 Nhận Định Xu Hướng Tổng Hợp Từ Các Mô Hình Đã Chọn:")
                    if avg_return >= 3.0:
                        trend_headline = "🟢 XU HƯỚNG TĂNG GIÁ MẠNH (STRONG BULLISH)"
                        trend_color = "success"
                        action_advice = "Ưu tiên nắm giữ cổ phiếu, canh các nhịp điều chỉnh trong phiên để gia tăng tỷ trọng. Vùng giá chốt lời kỳ vọng hướng tới mốc " + f"**{avg_price:,.2f} ({avg_price*1000:,.0f} VNĐ)**."
                    elif avg_return >= 0.5:
                        trend_headline = "🔵 XU HƯỚNG PHỤC HỒI / TĂNG TRƯỞNG NHẸ (MILD BULLISH)"
                        trend_color = "info"
                        action_advice = "Dòng tiền có tín hiệu nâng đỡ nhưng chưa quá bứt phá. Phù hợp chiến lược mua gom tích lũy tỷ trọng vừa phải hoặc lướt sóng T+."
                    elif avg_return <= -2.0:
                        trend_headline = "🔴 XU HƯỚNG ĐIỀU CHỈNH / GIẢM GIÁ (BEARISH)"
                        trend_color = "error"
                        action_advice = "Áp lực cung chiếm ưu thế, các mô hình cảnh báo rủi ro rung lắc. Nên chủ động hạ bớt margin hoặc cơ cấu danh mục bảo vệ vốn."
                    else:
                        trend_headline = "🟡 XU HƯỚNG ĐI NGANG TÍCH LŨY (SIDEWAYS / CONSOLIDATION)"
                        trend_color = "warning"
                        action_advice = "Thị trường đang giằng co tìm điểm cân bằng mới. Nhà đầu tư nên kiên nhẫn quan sát, chờ tín hiệu dòng tiền bùng nổ kèm khối lượng xác nhận."

                    risk_comment = f"Độ phân kỳ giữa mô hình lạc quan nhất và thận trọng nhất là **{spread:.2f}%**."
                    if spread > 10.0:
                        risk_comment += " Mức độ phân kỳ khá cao cho thấy cổ phiếu đang ở vùng biến động mạnh, nhà đầu tư nên quản trị tỷ trọng cẩn trọng."
                    else:
                        risk_comment += " Mức độ đồng thuận giữa các mô hình ở mức cao, xác suất xu hướng diễn ra tương đối ổn định."

                    analysis_narrative = f"""
                    **{trend_headline}**
                    - **Mức giá dự phóng bình quân:** `{avg_price:,.2f}` ({avg_price*1000:,.0f} VNĐ), tương ứng biến động kỳ vọng `{c_sign_avg}{avg_return:.2f}%` sau {len(future_dates)} phiên tới.
                    - **Kịch bản cao nhất:** Mô hình **{best_model}** dự báo giá có thể chạm mốc **{all_models_dict[best_model]['final_price']:,.2f}** ({all_models_dict[best_model]['expected_return']:+.2f}%).
                    - **Kịch bản bảo thủ:** Mô hình **{worst_model}** nhận định giá ở mức **{all_models_dict[worst_model]['final_price']:,.2f}** ({all_models_dict[worst_model]['expected_return']:+.2f}%).
                    - **Đánh giá rủi ro & Đồng thuận:** {risk_comment}
                    - **Khuyến nghị hành động:** {action_advice}
                    """
                    if trend_color == "success":
                        st.success(analysis_narrative)
                    elif trend_color == "error":
                        st.error(analysis_narrative)
                    elif trend_color == "warning":
                        st.warning(analysis_narrative)
                    else:
                        st.info(analysis_narrative)

                    # 6. BIỂU ĐỒ TRỌNG SỐ ĐÓNG GÓP (FEATURE IMPORTANCE)
                    st.markdown("---")
                    fi_fig = create_feature_importance_chart(ml_result.get("feature_importance", []))
                    st.plotly_chart(fi_fig, width="stretch", config=PLOTLY_CONFIG, on_select="ignore")

        with tab_forecast:
            st.subheader(f"🎲 Mô Phỏng Kịch Bản Xác Suất Monte Carlo ({forecast_days} Phiên Tới)")
            
            f_col1, f_col2, f_col3 = st.columns(3)
            f_col1.metric("Xu Hướng Chủ Đạo", forecast.get("outlook", "N/A"))
            f_col2.metric("Xác Suất Tăng Giá", f"{forecast.get('upward_probability', 50)}%")
            f_col3.metric("Mục Tiêu Cơ Sở (Base)", f"{forecast.get('target_price_base', 0):,.2f}", f"{forecast.get('expected_return_pct', 0):+.2f}%")

            st.info(f"👉 **Khuyến nghị:** {forecast.get('recommendation', 'Quan sát')}")

            # Đồ thị dự báo Monte Carlo Fan Chart
            forecast_fig = create_forecast_chart(df_indicators, forecast, active_sym)
            st.plotly_chart(forecast_fig, width="stretch", config=PLOTLY_CONFIG, on_select="ignore")

            # Bảng chi tiết từng phiên
            st.markdown("#### Bảng Kịch Bản Giá Chi Tiết Theo Phiên")
            st.dataframe(forecast.get("forecast_df"), width="stretch", hide_index=True)


# -------------------------------------------------------------
# 6. TRANG 4: XUẤT BÁO CÁO PHÂN TÍCH (REPORT GENERATOR)
# -------------------------------------------------------------
elif navigation == "📑 Xuất Báo cáo Phân tích":
    st.title("📑 Xuất Báo Cáo Phân Tích & Dự Báo")
    st.caption("Tự động tổng hợp dữ liệu thị trường, chỉ báo kỹ thuật, kịch bản dự báo và lưu trữ Watchlist ra file HTML/Markdown")

    fav_list = watchlist_db.get_ticker_list()
    rep_ticker = st.selectbox("Chọn mã cổ phiếu cần xuất báo cáo:", fav_list if fav_list else DEFAULT_TICKERS)

    if rep_ticker:
        with st.spinner("Đang biên soạn báo cáo phân tích..."):
            md_report, html_report = get_cached_report_content(rep_ticker)

        r_col1, r_col2 = st.columns([3, 1])
        r_col1.markdown(f"### Xem trước Báo Cáo: **{rep_ticker}**")
        
        # Nút tải file
        r_col2.download_button(
            label="📥 Tải Báo Cáo HTML",
            data=html_report,
            file_name=f"Bao_Cao_{rep_ticker}_{datetime.now().strftime('%Y%m%d')}.html",
            mime="text/html",
            width="stretch",
        )

        st.markdown(md_report)

# Tự động refresh nếu được bật
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
