"""
Module Thanh bên Điều hướng & Cảnh báo (Sidebar Navigation & Real-time Alerts)
Quản lý menu chuyển trang, cài đặt tự động làm mới và kiểm tra cảnh báo giá tức thì.
"""
from typing import Tuple
from datetime import datetime, timezone, timedelta
import streamlit as st

from config.settings import AUTO_REFRESH_INTERVAL
from src.database.tinydb_manager import watchlist_db
from src.data.stock_data import stock_engine
from src.ui.cache import get_cached_quotes_map, get_cached_technical_alerts

# Múi giờ Việt Nam (UTC+7)
VN_TZ = timezone(timedelta(hours=7))

NAV_OPTIONS = [
    "📊 Tổng quan Thị trường",
    "🎯 Bộ Lọc CANSLIM & SEPA",
    "⭐ Danh mục Yêu thích (Watchlist)",
    "🔍 Phân tích Chi tiết & Dự báo",
    "💼 Quản Trị Rủi Ro & Lịch Sự Kiện",
    "📑 Xuất Báo cáo Phân tích",
]


def render_sidebar() -> Tuple[str, bool, int]:
    """
    Render thanh bên điều hướng, cảnh báo giá và cấu hình làm mới.
    Trả về:
        (navigation_choice, auto_refresh_bool, refresh_rate_int)
    """
    st.sidebar.markdown("## 📈 **VN-Stock Analytics**")
    st.sidebar.caption("Hệ thống theo dõi & dự báo chứng khoán tức thì")

    if "redirect_page" in st.session_state:
        target = st.session_state.pop("redirect_page")
        if target in NAV_OPTIONS:
            st.session_state["nav_radio"] = target

    if "nav_radio" not in st.session_state or st.session_state["nav_radio"] not in NAV_OPTIONS:
        st.session_state["nav_radio"] = NAV_OPTIONS[0]

    navigation = st.sidebar.radio(
        "CHỌN CHỨC NĂNG",
        NAV_OPTIONS,
        key="nav_radio",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Cấu hình Tự động Làm mới")
    auto_refresh = st.sidebar.checkbox("Bật tự động làm mới", value=False)
    refresh_rate = st.sidebar.slider("Tần suất (giây)", min_value=1, max_value=60, value=AUTO_REFRESH_INTERVAL, step=1)

    if st.sidebar.button("🔄 Làm mới dữ liệu ngay", width="stretch"):
        st.cache_data.clear()
        st.rerun()

    # 1. Kiểm tra cảnh báo giá tức thì từ Watchlist
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

    # 2. Cảnh báo Kỹ thuật Tự Động (Breakout, Gãy MA, Phân kỳ RSI)
    if all_watchlist:
        top_syms = tuple(item["ticker"] for item in all_watchlist[:6])
        tech_alerts = get_cached_technical_alerts(top_syms)
        if tech_alerts:
            st.sidebar.markdown("---")
            st.sidebar.info("⚡ **CẢNH BÁO KỸ THUẬT & DÒNG TIỀN**")
            for t_alt in tech_alerts[:3]:
                b_color = "success" if t_alt.get("severity") == "SUCCESS" else ("error" if t_alt.get("severity") == "ERROR" else "warning")
                msg = f"**{t_alt.get('badge')}**\n\n{t_alt.get('message')}"
                if b_color == "success":
                    st.sidebar.success(msg)
                elif b_color == "error":
                    st.sidebar.error(msg)
                else:
                    st.sidebar.warning(msg)

    st.sidebar.markdown("---")
    st.sidebar.caption(f"🕒 Lần cập nhật cuối: {datetime.now(VN_TZ).strftime('%H:%M:%S')}")
    st.sidebar.caption("💾 Lưu trữ NoSQL: `TinyDB (JSON)`")

    return navigation, auto_refresh, refresh_rate
