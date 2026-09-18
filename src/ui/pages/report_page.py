"""
Trang 4: Xuất Báo Cáo Phân Tích (Report Generator Page)
Tự động tổng hợp dữ liệu thị trường, phân tích kỹ thuật, dự báo giá
và xuất bản báo cáo hoàn chỉnh dưới định dạng HTML hoặc Markdown.
"""
from datetime import datetime
import streamlit as st

from config.settings import DEFAULT_TICKERS
from src.database.tinydb_manager import watchlist_db
from src.ui.cache import get_cached_report_content


def render_report_page():
    """Hiển thị toàn bộ nội dung trang Xuất Báo Cáo Phân Tích."""
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
