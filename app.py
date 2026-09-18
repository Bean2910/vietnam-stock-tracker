"""
ỨNG DỤNG THEO DÕI, DỰ BÁO & BÁO CÁO CHỨNG KHOÁN VIỆT NAM (VN-STOCK TRACKER & FORECAST)
Điểm khởi chạy ứng dụng (Main Entrypoint & Router)
Được cấu trúc theo mô hình module tinh gọn, phân tách các trang chức năng vào src/ui/pages/.
"""
import time
import streamlit as st

from config.settings import DEFAULT_TICKERS
from src.database.tinydb_manager import watchlist_db
from src.ui.styles import apply_custom_styles
from src.ui.sidebar import render_sidebar
from src.ui.pages.market_overview import render_market_overview_page
from src.ui.pages.screener_page import render_screener_page
from src.ui.pages.watchlist_page import render_watchlist_page
from src.ui.pages.detail_analysis import render_detail_analysis_page
from src.ui.pages.portfolio_risk_page import render_portfolio_risk_page
from src.ui.pages.report_page import render_report_page

# 1. Cấu hình trang Streamlit
st.set_page_config(
    page_title="VN-Stock Tracker & Forecast",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Áp dụng bảng style CSS tùy chỉnh hiện đại
apply_custom_styles()

# 3. Khởi tạo dữ liệu mẫu nếu watchlist đang trống
watchlist_db.init_defaults_if_empty(DEFAULT_TICKERS)

# 4. Render thanh bên điều hướng, cảnh báo giá & cấu hình làm mới
navigation, auto_refresh, refresh_rate = render_sidebar()

# 5. Bộ định tuyến hiển thị trang tương ứng (Page Router)
if navigation == "📊 Tổng quan Thị trường":
    render_market_overview_page()

elif navigation == "🎯 Bộ Lọc CANSLIM & SEPA":
    render_screener_page()

elif navigation == "⭐ Danh mục Yêu thích (Watchlist)":
    render_watchlist_page()

elif navigation == "🔍 Phân tích Chi tiết & Dự báo":
    render_detail_analysis_page()

elif navigation == "💼 Quản Trị Rủi Ro & Lịch Sự Kiện":
    render_portfolio_risk_page()

elif navigation == "📑 Xuất Báo cáo Phân tích":
    render_report_page()

# 6. Xử lý tự động làm mới nếu được bật
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
