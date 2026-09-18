"""
Trang: Bộ Lọc Cổ Phiếu Thông Minh (Smart Stock Screener - CANSLIM / SEPA / RS O'Neil)
Tự động quét và sàng lọc các cổ phiếu đạt chuẩn tăng trưởng cao và sức mạnh kỹ thuật vượt trội.
"""
import streamlit as st
import pandas as pd

from src.database.tinydb_manager import watchlist_db


def render_screener_page():
    """Hiển thị toàn bộ giao diện Bộ Lọc Cổ Phiếu Thông Minh."""
    from src.ui.cache import get_cached_screener_results

    st.title("🎯 Bộ Lọc Cổ Phiếu Thông Minh (CANSLIM & SEPA)")
    st.caption("Chiến lược lọc kết hợp Tăng Trưởng Cơ Bản (FA) & Động Lượng Kỹ Thuật (TA) theo trường phái William O'Neil và Mark Minervini")

    # Bảng điều khiển bộ lọc
    with st.expander("⚙️ **Tùy Chỉnh Tiêu Chí Lọc Cổ Phiếu**", expanded=True):
        f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
        min_rs = f_col1.slider("Sức mạnh giá tối thiểu (RS O'Neil 1-99):", min_value=50, max_value=95, value=70, step=5, help="RS > 80 là nhóm cổ phiếu dẫn dắt thị trường (Leader stocks)")
        min_roe = f_col2.slider("Tỷ suất sinh lời trên vốn (ROE %):", min_value=8.0, max_value=25.0, value=12.0, step=1.0, help="Đo lường hiệu quả sử dụng vốn của ban lãnh đạo doanh nghiệp")
        filter_grade = f_col3.selectbox("Hạng cổ phiếu tối thiểu:", ["Tất cả cổ phiếu đạt tiêu chí", "Chỉ Siêu Cổ Phiếu (5/5)", "Từ Hạng Ưu Tú trở lên (>= 4/5)"], index=0)

    # Nạp dữ liệu qua Cache
    with st.spinner("Đang quét toàn bộ dữ liệu cơ bản và kỹ thuật các mã cổ phiếu..."):
        all_screened = get_cached_screener_results(min_rs=min_rs, min_roe=min_roe)

    # Lọc theo hạng
    if filter_grade == "Chỉ Siêu Cổ Phiếu (5/5)":
        results = [r for r in all_screened if r["passed_criteria"] == "5/5"]
    elif filter_grade == "Từ Hạng Ưu Tú trở lên (>= 4/5)":
        results = [r for r in all_screened if r["passed_criteria"] in ["5/5", "4/5"]]
    else:
        results = all_screened

    # Thống kê nhanh
    m1, m2, m3, m4 = st.columns(4)
    count_5 = len([r for r in all_screened if r["passed_criteria"] == "5/5"])
    count_4 = len([r for r in all_screened if r["passed_criteria"] == "4/5"])
    max_rs = max([r["rs_rating"] for r in all_screened]) if all_screened else 0
    top_ticker = all_screened[0]["ticker"] if all_screened else "N/A"

    m1.metric("🥇 Siêu Cổ Phiếu (5/5)", f"{count_5} mã", "Đạt chuẩn tuyệt đối")
    m2.metric("🥈 Cổ Phiếu Ưu Tú (4/5)", f"{count_4} mã", "Tiềm năng bứt phá")
    m3.metric("⭐ RS Rating Cao Nhất", f"{max_rs}/99", f"Mã dẫn dắt: {top_ticker}")
    m4.metric("📋 Tổng Số Mã Đạt Bộ Lọc", f"{len(results)} mã", f"Từ rổ theo dõi")

    st.markdown("---")

    # Bảng kết quả chi tiết
    st.subheader(f"📋 Danh Sách Cổ Phiếu Được Sàng Lọc ({len(results)} mã)")
    if results:
        table_rows = []
        for r in results:
            table_rows.append({
                "Mã CK": r["ticker"],
                "Tên Doanh Nghiệp": r["name"],
                "Ngành": r["sector"],
                "Giá Hiện Tại": f"{r['price']:,.2f}",
                "% Thay Đổi": f"{'+' if r['change'] >= 0 else ''}{r['change']:.2f}%",
                "Điểm RS": f"{r['rs_rating']}/99",
                "ROE (%)": f"{r['roe']:.1f}%",
                "EPS YoY": f"{'+' if r['eps_growth'] >= 0 else ''}{r['eps_growth']:.1f}%",
                "Doanh Thu YoY": f"{'+' if r['rev_growth'] >= 0 else ''}{r['rev_growth']:.1f}%",
                "P/E": f"{r['pe']:.1f}x",
                "Cách Đỉnh 52W": f"-{r['pct_from_52w_high']:.1f}%",
                "Đạt Tiêu Chí": r["passed_criteria"],
                "Phân Hạng": f"{r['badge']} ({r['grade'].split(' ')[1]})",
            })
        st.dataframe(pd.DataFrame(table_rows), width="stretch", hide_index=True)

        st.markdown("##### ⚡ Phân Tích Nhanh & Thêm Vào Danh Mục Theo Dõi:")
        card_cols = st.columns(min(len(results), 3))
        for idx, item in enumerate(results[:6]):
            c_idx = idx % len(card_cols)
            sym = item["ticker"]
            with card_cols[c_idx]:
                st.markdown(f"""
                <div style="background: #1e293b; border: 1px solid {item['badge_color']}; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="font-size: 18px; color: #f8fafc;">{sym}</strong>
                        <span style="font-size: 12px; font-weight: 700; color: {item['badge_color']};">{item['badge']}</span>
                    </div>
                    <div style="font-size: 13px; color: #cbd5e1; margin-top: 4px;">
                        {item['name']} ({item['sector']})
                    </div>
                    <div style="font-size: 13px; color: #94a3b8; margin-top: 6px; line-height: 1.6;">
                        🚀 <b>RS Rating:</b> {item['rs_rating']}/99 | <b>ROE:</b> {item['roe']:.1f}%<br>
                        📈 <b>Tăng trưởng EPS:</b> +{item['eps_growth']:.1f}% | <b>P/E:</b> {item['pe']:.1f}x<br>
                        🎯 <b>Tiêu chí đạt:</b> {item['passed_criteria']} | <b>Cách đỉnh 52W:</b> -{item['pct_from_52w_high']:.1f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
                btn_c1, btn_c2 = st.columns(2)
                if btn_c1.button(f"🔍 Soi sâu {sym}", key=f"screen_deep_{sym}", width="stretch"):
                    st.session_state["target_sym"] = sym
                    st.session_state["redirect_page"] = "🔍 Phân tích Chi tiết & Dự báo"
                    st.rerun()
                if btn_c2.button(f"➕ Thêm WL", key=f"screen_add_{sym}", width="stretch"):
                    watchlist_db.add_or_update(sym, tier="TIER_1_FOCUS", note="Thêm từ Bộ lọc CANSLIM")
                    st.toast(f"Đã thêm {sym} vào Watchlist Tier 1!", icon="✅")
    else:
        st.info("Không có cổ phiếu nào thỏa mãn đầy đủ các tiêu chí lọc khắt khe hiện tại. Hãy thử hạ bớt ngưỡng RS hoặc ROE.")
