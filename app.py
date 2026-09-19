"""
ỨNG DỤNG THEO DÕI, DỰ BÁO & BÁO CÁO CHỨNG KHOÁN VIỆT NAM (VN-STOCK TRACKER & FORECAST)
Điểm khởi chạy ứng dụng (Main Entrypoint & Router)
Được cấu trúc theo mô hình module tinh gọn, phân tách các trang chức năng vào src/ui/pages/.
"""
import time
import sys
import importlib
import streamlit as st

# 0. Ép buộc nạp lại toàn bộ code mới nhất của tất cả module trong src/ trên mỗi lượt F5 / Rerun (Hot Reload)
for mod_name in list(sys.modules.keys()):
    if mod_name.startswith("src."):
        try:
            importlib.reload(sys.modules[mod_name])
        except Exception:
            pass

from config.settings import DEFAULT_TICKERS
from src.database.tinydb_manager import watchlist_db
import src.ui.styles as ui_styles
import src.ui.sidebar as ui_sidebar
import src.ui.pages.market_overview as market_overview_page
import src.ui.pages.screener_page as screener_page
import src.ui.pages.watchlist_page as watchlist_page
import src.ui.pages.detail_analysis as detail_analysis_page
import src.ui.pages.portfolio_risk_page as portfolio_risk_page
import src.ui.pages.report_page as report_page

# 1. Cấu hình trang Streamlit
st.set_page_config(
    page_title="VN-Stock Tracker & Forecast",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# 2. Áp dụng bảng style CSS tùy chỉnh hiện đại
ui_styles.apply_custom_styles()

# 3. Khởi tạo dữ liệu mẫu nếu watchlist đang trống
watchlist_db.init_defaults_if_empty(DEFAULT_TICKERS)

# 4. Render thanh bên điều hướng, cảnh báo giá & cấu hình làm mới
navigation, auto_refresh, refresh_rate = ui_sidebar.render_sidebar()

# 5. Bộ định tuyến hiển thị trang tương ứng (Page Router)
if navigation == "📊 Tổng quan Thị trường":
    market_overview_page.render_market_overview_page()

elif navigation == "🎯 Bộ Lọc CANSLIM & SEPA":
    screener_page.render_screener_page()

elif navigation == "⭐ Danh mục Yêu thích (Watchlist)":
    watchlist_page.render_watchlist_page()

elif navigation == "🔍 Phân tích Chi tiết & Dự báo":
    detail_analysis_page.render_detail_analysis_page()

elif navigation == "💼 Quản Trị Rủi Ro & Lịch Sự Kiện":
    portfolio_risk_page.render_portfolio_risk_page()

elif navigation == "📑 Xuất Báo cáo Phân tích":
    report_page.render_report_page()

# 6. Xử lý tự động làm mới nếu được bật
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
