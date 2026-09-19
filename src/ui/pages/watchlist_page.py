"""
Trang 2: Danh Mục Cổ Phiếu Theo Dõi Phân Tầng (3-Tier Watchlist & Sector Heatmap)
Phân loại thông minh:
- Tier 1 (Focus List): Cổ phiếu đạt chuẩn FA + nền giá đẹp, sẵn sàng điểm mua
- Tier 2 (Radar List): Cổ phiếu cơ bản xuất sắc, đang tích lũy / điều chỉnh
- Tier 3 (Warning / Review List): Đang nắm giữ tiệm cận ngưỡng cắt lỗ hoặc chạm chốt lời
- Ma trận tương quan ngành (Sector Treemap Heatmap)
"""
import time
import streamlit as st

from src.database.tinydb_manager import watchlist_db
from src.data.stock_data import stock_engine
from src.ui.cache import get_cached_quotes_map, get_stock_technical_summary
from src.ui.components import create_sector_treemap_chart
from src.ui.styles import PLOTLY_CONFIG


def render_watchlist_page():
    """Hiển thị toàn bộ nội dung trang Quản Lý Danh Mục Phân Tầng & Sector Heatmap."""
    st.title("⭐ Danh Mục Cổ Phiếu Theo Dõi (3-Tier Watchlist) & Sector Heatmap")
    st.caption("Phân tầng danh mục theo trạng thái hành động (Focus / Radar / Warning) & Bản đồ nhiệt dòng tiền ngành")

    watchlist_items = watchlist_db.get_all()

    # Form thêm mã mới
    with st.expander("➕ **Thêm Mã Cổ Phiếu Mới & Phân Tầng Danh Mục**", expanded=False):
        with st.form("add_ticker_form"):
            f_col1, f_col2, f_col3, f_col4 = st.columns([1.2, 1, 1, 1.5])
            new_ticker = f_col1.text_input("Mã Cổ Phiếu (VD: HPG, FPT, VNM)*").strip().upper()
            target_p = f_col2.number_input(
                "Giá Chốt Lời (Điểm)", 
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
            tier_choice = f_col4.selectbox(
                "Phân Tầng Danh Mục:",
                [
                    "Tier 1: Focus List (Chuẩn FA + Nền giá đẹp)",
                    "Tier 2: Radar List (Chờ tích lũy / Điều chỉnh)",
                    "Tier 3: Warning List (Cảnh báo Cắt lỗ / Chốt lời)",
                ],
                index=0,
            )
            tier_code = "TIER_1_FOCUS" if "Tier 1" in tier_choice else ("TIER_2_RADAR" if "Tier 2" in tier_choice else "TIER_3_WARNING")

            f_note = st.text_input("Ghi chú chiến lược đầu tư (Tùy chọn)", placeholder="Ví dụ: Vượt đỉnh 50 phiên, chờ giải ngân phiên FTD")
            f_alert = st.checkbox("Bật cảnh báo tự động khi chạm ngưỡng", value=True)

            submitted = st.form_submit_button("Lưu Vào Danh Mục Phân Tầng", width="stretch")
            if submitted:
                if new_ticker:
                    watchlist_db.add_or_update(
                        ticker=new_ticker,
                        target_price=target_p if target_p > 0 else None,
                        stop_loss=stop_l if stop_l > 0 else None,
                        note=f_note,
                        alert_enabled=f_alert,
                        tier=tier_code,
                    )
                    st.success(f"Đã lưu thành công mã {new_ticker} vào {tier_choice.split(':')[0]}!")
                    time.sleep(0.4)
                    st.rerun()
                else:
                    st.error("Vui lòng nhập mã cổ phiếu hợp lệ!")

    st.markdown("---")

    # Lấy dữ liệu giá thực tế cho toàn bộ danh mục
    wl_syms = tuple(item["ticker"] for item in watchlist_items)
    wl_quotes_map = get_cached_quotes_map(wl_syms)

    # Phân nhóm theo 3 Tier
    tier1_items = [it for it in watchlist_items if it.get("tier") == "TIER_1_FOCUS"]
    tier2_items = [it for it in watchlist_items if it.get("tier") == "TIER_2_RADAR"]
    tier3_items = [it for it in watchlist_items if it.get("tier") == "TIER_3_WARNING"]

    tab_t1, tab_t2, tab_t3, tab_map = st.tabs([
        f"🥇 Tier 1: Focus List ({len(tier1_items)} mã)",
        f"🥈 Tier 2: Radar List ({len(tier2_items)} mã)",
        f"⚠️ Tier 3: Warning List ({len(tier3_items)} mã)",
        "🗺️ Bản Đồ Nhiệt Ngành (Sector Heatmap)",
    ])

    def render_tier_items_list(items, tier_badge_label):
        if not items:
            st.info(f"Chưa có cổ phiếu nào trong danh mục {tier_badge_label}.")
            return

        for item in items:
            sym = item["ticker"]
            q = wl_quotes_map.get(sym) or stock_engine.get_realtime_quote(sym)
            tech = get_stock_technical_summary(sym)
            p_class = "price-up" if q["change"] > 0 else ("price-down" if q["change"] < 0 else "price-ref")

            with st.container():
                c1, c2, c3, c4, c5, c6 = st.columns([1.2, 1.8, 1.8, 2.3, 2.0, 1.6])

                # Cột 1: Mã & Phân loại
                c1.markdown(f"### **{sym}**")
                c1.caption(f"{tier_badge_label}")

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
                tp_str = f"{cur_tp:,.2f} ({cur_tp*1000:,.0f} đ)" if cur_tp > 0 else "Chưa đặt"
                sl_str = f"{cur_sl:,.2f} ({cur_sl*1000:,.0f} đ)" if cur_sl > 0 else "Chưa đặt"
                c4.markdown(f"🎯 **Target:** `{tp_str}`\n\n⚠️ **Stop:** `{sl_str}`")

                # Cột 5: Ghi chú
                c5.info(item.get("note") or "Không có ghi chú")

                # Cột 6: Chỉnh sửa & Chuyển Tier
                with c6.popover("⚙️ Tùy chỉnh", width="stretch"):
                    st.markdown(f"#### Chỉnh sửa mã **{sym}**")
                    with st.form(key=f"edit_tier_form_{sym}"):
                        cur_t = item.get("tier", "TIER_1_FOCUS")
                        idx_t = 0 if cur_t == "TIER_1_FOCUS" else (1 if cur_t == "TIER_2_RADAR" else 2)
                        edit_t = st.selectbox("Chuyển Tier:", ["Tier 1: Focus List", "Tier 2: Radar List", "Tier 3: Warning List"], index=idx_t)
                        edit_tp = st.number_input("Giá Chốt Lời (Điểm)", min_value=0.0, step=0.5, value=cur_tp)
                        edit_sl = st.number_input("Ngưỡng Cắt Lỗ (Điểm)", min_value=0.0, step=0.5, value=cur_sl)
                        edit_note = st.text_input("Ghi chú", value=item.get("note") or "")

                        if st.form_submit_button("Lưu Thay Đổi", width="stretch"):
                            new_t_code = "TIER_1_FOCUS" if "Tier 1" in edit_t else ("TIER_2_RADAR" if "Tier 2" in edit_t else "TIER_3_WARNING")
                            watchlist_db.add_or_update(
                                ticker=sym,
                                target_price=edit_tp if edit_tp > 0 else None,
                                stop_loss=edit_sl if edit_sl > 0 else None,
                                note=edit_note,
                                tier=new_t_code,
                            )
                            st.cache_data.clear()
                            st.success(f"Đã cập nhật mã {sym}!")
                            st.rerun()

                if c6.button("🗑️ Xóa", key=f"del_wl_{sym}", width="stretch"):
                    watchlist_db.remove(sym)
                    st.cache_data.clear()
                    st.rerun()

                st.markdown("<hr style='margin: 8px 0; border-color: #334155;'>", unsafe_allow_html=True)

    with tab_t1:
        st.markdown("##### 🥇 Tier 1 (Focus List) - Ưu Tiên Số 1")
        st.caption("Cổ phiếu đạt chuẩn FA xuất sắc, có câu chuyện tăng trưởng và đang vận động trong nền giá đẹp sẵn sàng điểm mua bứt phá.")
        render_tier_items_list(tier1_items, "🥇 Tier 1 (Focus)")

    with tab_t2:
        st.markdown("##### 🥈 Tier 2 (Radar List) - Theo Dõi Tiềm Năng")
        st.caption("Doanh nghiệp tốt nhưng giá đang trong nhịp điều chỉnh hoặc chưa hoàn thành mẫu hình tích lũy. Kiên nhẫn chờ thời cơ.")
        render_tier_items_list(tier2_items, "🥈 Tier 2 (Radar)")

    with tab_t3:
        st.markdown("##### ⚠️ Tier 3 (Warning / Review List) - Cảnh Báo Rủi Ro")
        st.caption("Cổ phiếu đang nắm giữ tiệm cận ngưỡng cắt lỗ hoặc đã chạm vùng giá mục tiêu chốt lời. Cần theo dõi sát để ra quyết định cơ cấu.")
        render_tier_items_list(tier3_items, "⚠️ Tier 3 (Warning)")

    with tab_map:
        st.subheader("🗺️ Ma Trận Tương Quan Ngành & Dòng Tiền (Sector Treemap)")
        st.caption("Diện tích khối thể hiện quy mô thanh khoản, màu sắc thể hiện % tăng giảm giá giúp nhận diện ngay tâm điểm dòng tiền")

        # Chuẩn bị dữ liệu cho Treemap từ các cổ phiếu theo dõi và top thị trường
        sector_items = []
        # Mapping ngành cho các mã phổ biến
        sec_dict = {
            "HPG": "Thép & Vật Liệu", "HSG": "Thép & Vật Liệu", "NKG": "Thép & Vật Liệu",
            "SSI": "Chứng Khoán", "VND": "Chứng Khoán", "VCI": "Chứng Khoán",
            "TCB": "Ngân Hàng", "MBB": "Ngân Hàng", "ACB": "Ngân Hàng", "VCB": "Ngân Hàng",
            "VHM": "Bất Động Sản", "VIC": "Bất Động Sản", "DIG": "Bất Động Sản", "DXG": "Bất Động Sản",
            "FPT": "Công Nghệ & Viễn Thông", "CTR": "Công Nghệ & Viễn Thông",
            "MWG": "Bán Lẻ & Tiêu Dùng", "FRT": "Bán Lẻ & Tiêu Dùng", "VNM": "Bán Lẻ & Tiêu Dùng",
            "REE": "Năng Lượng & Tiện Ích", "POW": "Năng Lượng & Tiện Ích",
            "PVD": "Dầu Khí", "PVS": "Dầu Khí",
        }

        for item in watchlist_items:
            s_sym = item["ticker"]
            q_info = wl_quotes_map.get(s_sym) or stock_engine.get_realtime_quote(s_sym)
            sec_name = sec_dict.get(s_sym, "Khác")
            sector_items.append({
                "ticker": s_sym,
                "sector": sec_name,
                "price": q_info.get("price", 0.0),
                "change": q_info.get("pct_change", 0.0),
                "volume": q_info.get("volume", 1000000),
            })

        if sector_items:
            treemap_fig = create_sector_treemap_chart(sector_items)
            st.plotly_chart(treemap_fig, width="stretch", config=PLOTLY_CONFIG, on_select="ignore")
        else:
            st.info("Chưa đủ dữ liệu để vẽ bản đồ nhiệt ngành.")
