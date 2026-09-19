"""
Trang: Quản Trị Rủi Ro NAV, Nhật Ký Giao Dịch & Lịch Sự Kiện
Triển khai:
1. Máy tính quy mô vị thế (Position Sizing Calculator)
2. Theo dõi cơ cấu Tiền mặt / Cổ phiếu / Margin
3. Nhật ký giao dịch Trading Journal (Win Rate, R:R Ratio)
4. Lịch sự kiện doanh nghiệp, GDKHQ, Đáo hạn phái sinh & ETF
"""
import re
from typing import Any
import streamlit as st
import pandas as pd

from src.database.tinydb_manager import journal_db
from src.analysis.risk_management import (
    calculate_position_size,
    calculate_portfolio_allocation,
    analyze_trading_journal,
)


def parse_vietnamese_currency(val_str: Any, default: int = 0) -> int:
    """Chuyển đổi chuỗi định dạng tiền tệ (vd: '500,000,000', '500 tr', '1.5 tỷ', '500.000.000') thành số nguyên VNĐ."""
    if val_str is None:
        return default
    s = str(val_str).strip().lower().replace("vnđ", "").replace("vnd", "").replace("đ", "").strip()
    if not s:
        return default
    if s == "0":
        return 0
    # Xử lý đơn vị Tỷ
    if "tỷ" in s or "ty" in s:
        cleaned = re.sub(r"[^0-9,\.]", "", s).replace(",", ".")
        try:
            return max(0, int(float(cleaned) * 1_000_000_000))
        except Exception:
            return default
    # Xử lý đơn vị Triệu / Tr
    if "triệu" in s or "trieu" in s or "tr" in s:
        cleaned = re.sub(r"[^0-9,\.]", "", s).replace(",", ".")
        try:
            return max(0, int(float(cleaned) * 1_000_000))
        except Exception:
            return default
    # Xử lý số có dấu phân cách hàng nghìn (phẩy hoặc chấm)
    cleaned = re.sub(r"[^0-9]", "", s)
    if cleaned:
        try:
            return max(0, int(cleaned))
        except Exception:
            return default
    return default


def format_vnd_readable(amount: float) -> str:
    """Định dạng số tiền sang chuẩn đọc tiếng Việt (vd: 500,000,000 VNĐ (500 triệu đồng))."""
    amt = int(amount)
    if amt == 0:
        return "0 VNĐ"
    if amt >= 1_000_000_000:
        ty = amt / 1_000_000_000
        ty_str = f"{int(ty):,}" if ty == int(ty) else f"{ty:.2f}"
        return f"{amt:,} VNĐ ({ty_str} tỷ đồng)"
    elif amt >= 1_000_000:
        tr = amt / 1_000_000
        tr_str = f"{int(tr):,}" if tr == int(tr) else f"{tr:.1f}"
        return f"{amt:,} VNĐ ({tr_str} triệu đồng)"
    else:
        return f"{amt:,} VNĐ"


def render_currency_input(
    label: str,
    default_val: int,
    key: str,
    help_text: str = "",
    min_val: int = 0,
    max_val: int = 100_000_000_000,
) -> int:
    """Widget nhập số tiền chuẩn định dạng phân cách hàng nghìn và tự động hiển thị số tiền chữ."""
    if key not in st.session_state:
        st.session_state[key] = f"{default_val:,}"

    def _sync_callback():
        raw_input = st.session_state.get(key, "")
        parsed = parse_vietnamese_currency(raw_input, default=default_val)
        parsed = max(min_val, min(max_val, parsed))
        st.session_state[key] = f"{parsed:,}"

    val_str = st.text_input(
        label,
        key=key,
        on_change=_sync_callback,
        help=help_text or "Bạn có thể gõ trực tiếp: 500,000,000 hoặc 500tr hoặc 1.5 tỷ",
    )
    current_amt = parse_vietnamese_currency(val_str, default=default_val)
    current_amt = max(min_val, min(max_val, current_amt))
    st.caption(f"💵 Quy đổi: **{format_vnd_readable(current_amt)}**")
    return current_amt


def render_portfolio_risk_page():
    """Hiển thị toàn bộ nội dung Quản Trị Rủi Ro NAV & Nhật Ký Giao Dịch."""
    from src.ui.cache import get_cached_corporate_events
    st.title("💼 Quản Trị Rủi Ro NAV, Nhật Ký & Sự Kiện Doanh Nghiệp")
    st.caption("Công cụ quản trị quy mô vị thế (Position Sizing), đo lường hiệu suất giao dịch và theo dõi lịch sự kiện thị trường")

    tab_pos, tab_journal, tab_events = st.tabs([
        "📐 Máy Tính Vị Thế (Position Sizing)",
        "📖 Nhật Ký Giao Dịch & Win Rate",
        "📅 Lịch Sự Kiện & Đáo Hạn Phái Sinh",
    ])

    # ---------------------------------------------------------
    # TAB 1: MÁY TÍNH VỊ THẾ POSITION SIZING
    # ---------------------------------------------------------
    with tab_pos:
        st.subheader("📐 Tối Ưu Hóa Quy Mô Vị Thế Theo Nguyên Tắc Quản Trị Vốn")
        st.caption("Nguyên lý bất biến của các Trader huyền thoại: Không bao giờ để rủi ro trên 1 lệnh vượt quá 1% - 2% tổng NAV tài sản")

        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("##### ⚙️ Thiết Lập Thông Số Lệnh:")
            total_nav = render_currency_input(
                "Tổng giá trị tài sản ròng (NAV) - VNĐ:",
                default_val=500_000_000,
                key="nav_currency_input",
                help_text="Nhập tổng NAV tài khoản (vd: 500,000,000 hoặc 500 triệu hoặc 1 tỷ)",
                min_val=10_000_000,
            )

            # Phím chọn nhanh NAV phổ biến
            p_cols = st.columns(5)
            nav_presets = [
                ("100 tr", 100_000_000),
                ("200 tr", 200_000_000),
                ("500 tr", 500_000_000),
                ("1 tỷ", 1_000_000_000),
                ("2 tỷ", 2_000_000_000),
            ]
            def _set_nav_preset(val):
                st.session_state["nav_currency_input"] = f"{val:,}"

            for pcol, (plabel, pval) in zip(p_cols, nav_presets):
                pcol.button(
                    f"⚡ {plabel}",
                    key=f"quick_nav_{pval}",
                    on_click=_set_nav_preset,
                    args=(pval,),
                    width="stretch",
                )

            risk_pct = st.slider("Mức rủi ro tối đa cho phép trên lệnh này (% NAV):", min_value=0.5, max_value=3.0, value=1.5, step=0.1, help="Chuẩn mực quản trị vốn an toàn là từ 1% đến 2% NAV")
            
            p_c1, p_c2, p_c3 = st.columns(3)
            entry_p = p_c1.number_input("Giá mua dự kiến (nghìn đ):", min_value=1.0, max_value=500.0, value=30.0, step=0.5)
            p_c1.caption(f"🪙 Quy đổi: **{entry_p * 1000:,.0f} đ**")
            
            stop_p = p_c2.number_input("Giá cắt lỗ (nghìn đ):", min_value=0.5, max_value=499.0, value=28.0, step=0.5)
            p_c2.caption(f"🪙 Quy đổi: **{stop_p * 1000:,.0f} đ**")
            
            target_p = p_c3.number_input("Giá mục tiêu (nghìn đ):", min_value=1.5, max_value=1000.0, value=35.0, step=0.5)
            p_c3.caption(f"🪙 Quy đổi: **{target_p * 1000:,.0f} đ**")

            calc_btn = st.button("🚀 Tính Toán Quy Mô Vị Thế Tối Ưu", width="stretch")

        with c2:
            st.markdown("##### 🎯 Kết Quả Tính Toán & Khuyến Nghị:")
            res = calculate_position_size(total_nav, risk_pct, entry_p, stop_p, target_p)
            if "error" in res:
                st.error(res["error"])
            else:
                m_c1, m_c2 = st.columns(2)
                m_c1.metric("📦 Số Lượng Nên Mua", f"{res['recommended_shares']:,} CP", f"Chuẩn lô {res['recommended_shares']//100} lô")
                m_c2.metric("💰 Tổng Vốn Giải Ngân", f"{res['total_position_value']:,.0f} đ", f"{res['position_nav_weight']:.1f}% NAV")

                m_c3, m_c4 = st.columns(2)
                m_c3.metric("🛡️ Rủi Ro Nếu Chạm Cắt Lỗ", f"-{res['actual_max_loss']:,.0f} đ", f"-{res['actual_risk_pct']:.2f}% NAV")
                m_c4.metric("⚖️ Tỷ Lệ Lợi Nhuận/Rủi Ro (R:R)", f"{res['reward_risk_ratio']:.2f}x", f"Lãi tiềm năng: +{res['potential_profit']:,.0f} đ")

                st.success(f"💡 **Hướng dẫn giải ngân:** {res['advice']}")

        st.markdown("---")
        st.markdown("##### 🏦 Kiểm Tra Tỷ Lệ Đòn Bẩy & Phân Bổ Tài Sản Danh Mục:")
        a_col1, a_col2, a_col3 = st.columns(3)
        with a_col1:
            cash_val = render_currency_input(
                "Tiền mặt hiện có (VNĐ):",
                default_val=200_000_000,
                key="cash_currency_input",
                min_val=0,
            )
        with a_col2:
            stock_val = render_currency_input(
                "Giá trị danh mục cổ phiếu (VNĐ):",
                default_val=300_000_000,
                key="stock_currency_input",
                min_val=0,
            )
        with a_col3:
            margin_val = render_currency_input(
                "Dư nợ Margin đang vay (VNĐ):",
                default_val=0,
                key="margin_currency_input",
                min_val=0,
            )

        alloc = calculate_portfolio_allocation(cash_val, stock_val, margin_val)
        alloc_col1, alloc_col2, alloc_col3 = st.columns(3)
        alloc_col1.metric("💵 Tỷ Lệ Tiền Mặt", f"{alloc['cash_pct']:.1f}%", f"{cash_val:,.0f} đ")
        alloc_col2.metric("📊 Tỷ Lệ Cổ Phiếu", f"{alloc['stock_pct']:.1f}%", f"{stock_val:,.0f} đ")
        alloc_col3.metric("⚡ Hệ Số Đòn Bẩy", f"{alloc['leverage_ratio']:.2f}x", alloc["status"])
        st.info(f"💡 **Đánh giá sức khỏe danh mục:** {alloc['description']}")

    # ---------------------------------------------------------
    # TAB 2: NHẬT KÝ GIAO DỊCH & WIN RATE
    # ---------------------------------------------------------
    with tab_journal:
        st.subheader("📖 Nhật Ký Giao Dịch & Phân Tích Hiệu Suất Đầu Tư")
        st.caption("Theo dõi tỷ lệ thắng (Win Rate), tỷ lệ Lãi/Lỗ (Reward/Risk) và hiệu quả sinh lời của từng chiến lược")

        all_trades = journal_db.get_all_trades()
        journal_stats = analyze_trading_journal(all_trades)

        # 4 Thẻ hiệu suất chính
        j1, j2, j3, j4 = st.columns(4)
        j1.metric("🏆 Tỷ Lệ Thắng (Win Rate)", f"{journal_stats['win_rate']:.1f}%", f"{journal_stats['win_count']} Thắng / {journal_stats['loss_count']} Thua")
        j2.metric("⚖️ Tỷ Lệ Lãi/Lỗ TB (R:R)", f"{journal_stats['reward_risk_ratio']:.2f}x", f"Lãi TB +{journal_stats['avg_win_pct']:.1f}% / Lỗ TB -{journal_stats['avg_loss_pct']:.1f}%")
        j3.metric("📈 Profit Factor", f"{journal_stats['profit_factor']:.2f}", "Hệ số sinh lời tổng thể")
        j4.metric("📋 Tổng Số Lệnh Đã Chốt", f"{journal_stats['total_trades']} lệnh", "Dữ liệu lịch sử")

        # Thanh công cụ quản lý dữ liệu mẫu & dữ liệu thật
        with st.expander("⚙️ **Quản Lý Dữ Liệu Nhật Ký (Xóa Dữ Liệu Test / Reset / Sao Lưu)**", expanded=False):
            st.caption("💾 *Dữ liệu thật của bạn được lưu trữ an toàn & cố định tại file CSDL cục bộ:* `data_store/watchlist.json` *(Bảng: `trading_journal`)*")
            t_col1, t_col2, t_col3 = st.columns(3)
            with t_col1:
                if st.button("🗑️ Xóa 5 Lệnh Test Mẫu", width="stretch", help="Chỉ xóa các lệnh mẫu ban đầu (FPT, HPG, SSI, MWG, VHM), giữ lại toàn bộ lệnh thật bạn đã nhập"):
                    deleted_cnt = journal_db.clear_mock_trades()
                    st.toast(f"Đã xóa {deleted_cnt} lệnh test mẫu!", icon="✅")
                    st.rerun()
            with t_col2:
                if st.button("⚠️ Xóa Toàn Bộ Nhật Ký", width="stretch", help="Xóa sạch toàn bộ dữ liệu nhật ký để làm mới từ đầu"):
                    deleted_cnt = journal_db.clear_all_trades()
                    st.toast("Đã làm sạch toàn bộ nhật ký giao dịch!", icon="🧹")
                    st.rerun()
            with t_col3:
                if st.button("🔄 Nạp Lại Dữ Liệu Mẫu", width="stretch", help="Khôi phục lại 5 lệnh mẫu bất cứ khi nào muốn kiểm thử tính năng"):
                    journal_db.reset_to_default_mock()
                    st.toast("Đã nạp lại 5 lệnh test mẫu!", icon="🔄")
                    st.rerun()

        st.markdown("---")

        j_col1, j_col2 = st.columns([1, 1])
        with j_col1:
            st.markdown("##### 🧭 Hiệu Suất Theo Chiến Lược Giao Dịch:")
            if journal_stats["strategy_summary"]:
                st.dataframe(pd.DataFrame(journal_stats["strategy_summary"]), width="stretch", hide_index=True)
            else:
                st.info("Chưa có giao dịch nào được ghi nhận để thống kê theo chiến lược.")

        with j_col2:
            st.markdown("##### ➕ Ghi Thêm Lệnh Mới Vào Nhật Ký:")
            with st.form("new_trade_form", clear_on_submit=True):
                f_c1, f_c2 = st.columns(2)
                t_sym = f_c1.text_input("Mã cổ phiếu:").strip().upper()
                t_strat = f_c2.selectbox("Chiến lược áp dụng:", ["Breakout Nền Giá", "Bắt Đáy Hỗ Trợ", "Đầu Tư Giá Trị", "Lướt Sóng T+"])
                
                f_c3, f_c4, f_c5 = st.columns(3)
                t_buy = f_c3.number_input("Giá Mua (nghìn đ):", min_value=1.0, value=25.0, step=0.5)
                f_c3.caption(f"≈ {t_buy * 1000:,.0f} đ/CP")
                t_sell = f_c4.number_input("Giá Bán (nghìn đ):", min_value=1.0, value=28.0, step=0.5)
                f_c4.caption(f"≈ {t_sell * 1000:,.0f} đ/CP")
                t_shares = f_c5.number_input("Khối lượng CP:", min_value=100, value=1000, step=100)
                f_c5.caption(f"Lô: {t_shares // 100} lô ({t_shares:,} CP)")
                t_note = st.text_input("Ghi chú kinh nghiệm / lý do giao dịch:")
                
                if st.form_submit_button("Lưu Giao Dịch Vào Nhật Ký", width="stretch"):
                    if t_sym:
                        journal_db.add_trade(t_sym, t_strat, t_buy, t_sell, t_shares, t_note)
                        st.toast(f"Đã lưu giao dịch thật của {t_sym} vào cơ sở dữ liệu!", icon="💾")
                        st.rerun()

        st.markdown("##### 📜 Lịch Sử Chi Tiết Các Lệnh Đã Thực Hiện:")
        if not all_trades:
            st.info("📝 Bạn chưa có giao dịch nào trong nhật ký. Hãy sử dụng form **'➕ Ghi Thêm Lệnh Mới Vào Nhật Ký'** ở trên để bắt đầu lưu các lệnh thực tế của bạn!")
        else:
            trade_rows = []
            for t in all_trades:
                pnl_val = t.get("pnl_pct", 0.0)
                b_p = t.get("buy_price", 0)
                s_p = t.get("sell_price", 0)
                shs = t.get("shares", 1000)
                pnl_money = (s_p - b_p) * 1000.0 * shs
                is_mock_item = t.get("is_mock", False) or t.get("ticker") in ["FPT", "HPG", "SSI", "MWG", "VHM"] and t.get("date") in ["10/09/2026", "05/09/2026", "28/08/2026", "15/08/2026", "02/08/2026"]
                trade_rows.append({
                    "Ngày": t.get("date", ""),
                    "Mã CK": t.get("ticker", ""),
                    "Loại": "🧪 Test" if is_mock_item else "💼 Thật",
                    "Chiến Lược": t.get("strategy", ""),
                    "Giá Mua": f"{b_p:,.2f} ({b_p * 1000:,.0f} đ)",
                    "Giá Bán": f"{s_p:,.2f} ({s_p * 1000:,.0f} đ)",
                    "Khối Lượng": f"{shs:,} CP",
                    "Tổng Vốn": f"{(b_p * 1000.0 * shs):,.0f} đ",
                    "% Lãi/Lỗ": f"{'+' if pnl_val >= 0 else ''}{pnl_val:.2f}%",
                    "Tiền Lãi/Lỗ": f"{'+' if pnl_money >= 0 else ''}{pnl_money:,.0f} đ",
                    "Kết Quả": "🟢 LÃI" if pnl_val > 0 else "🔴 LỖ",
                    "Ghi Chú": t.get("notes", ""),
                })
            st.dataframe(pd.DataFrame(trade_rows), width="stretch", hide_index=True)

            # Công cụ xóa từng lệnh cụ thể
            with st.expander("❌ Xóa một lệnh cụ thể trong danh sách"):
                del_options = {}
                for idx, t in enumerate(all_trades):
                    d_id = t.get("doc_id")
                    label = f"#{idx+1} | {t.get('date')} - {t.get('ticker')} ({t.get('strategy')}) - Lãi/Lỗ: {t.get('pnl_pct'):+.2f}%"
                    del_options[label] = d_id
                
                sel_label = st.selectbox("Chọn lệnh muốn xóa:", list(del_options.keys()))
                if st.button("Xác nhận xóa lệnh đã chọn", type="secondary"):
                    chosen_id = del_options[sel_label]
                    if chosen_id and journal_db.delete_trade_by_id(chosen_id):
                        st.toast(f"Đã xóa lệnh thành công!", icon="🗑️")
                        st.rerun()

    # ---------------------------------------------------------
    # TAB 3: LỊCH SỰ KIỆN DOANH NGHIỆP & ĐÁO HẠN PHÁI SINH
    # ---------------------------------------------------------
    with tab_events:
        st.subheader("📅 Lịch Kinh Tế, Sự Kiện Doanh Nghiệp & Đáo Hạn Phái Sinh")
        st.caption("Nắm bắt trước các mốc sự kiện quan trọng tránh bị bất ngờ trước những phiên biến động lớn")

        events_data = get_cached_corporate_events()
        deriv_info = events_data.get("derivative_expiry", {})

        ev_c1, ev_c2 = st.columns([1, 1])
        with ev_c1:
            st.markdown("##### 🎯 Đếm Ngược Ngày Đáo Hạn Phái Sinh Tháng Này:")
            st.metric(
                "Đáo Hạn HĐTL VN30F1M",
                f"Ngày {deriv_info.get('date', '')}",
                f"Còn {deriv_info.get('days_left', 0)} ngày nữa ({deriv_info.get('status', 'Bình thường')})",
                help="Thứ Năm tuần thứ 3 hàng tháng là ngày đáo hạn phái sinh, thường có biến động mạnh cuối phiên ATC."
            )
            st.info(f"💡 {deriv_info.get('warning', '')}")

            st.markdown("##### 🏦 Lịch Tái Cơ Cấu Danh Mục Các Quỹ ETF Lớn:")
            etf_list = events_data.get("etf_rebalancing", [])
            st.dataframe(pd.DataFrame(etf_list), width="stretch", hide_index=True)

        with ev_c2:
            st.markdown("##### 📑 Lịch Giao Dịch Không Hưởng Quyền & Chi Trả Cổ Tức:")
            corp_events = events_data.get("corporate_events", [])
            ce_rows = []
            for ce in corp_events:
                ce_rows.append({
                    "Mã CK": ce.get("ticker"),
                    "Sự Kiện": ce.get("event"),
                    "Ngày GDKHQ": ce.get("ex_date"),
                    "Ngày Thanh Toán": ce.get("payment_date"),
                })
            st.dataframe(pd.DataFrame(ce_rows), width="stretch", hide_index=True)
            st.warning("⚠️ **Lưu ý GDKHQ:** Mua cổ phiếu vào ngày Giao Dịch Không Hưởng Quyền sẽ KHÔNG được nhận cổ tức đợt này. Giá tham chiếu của cổ phiếu sẽ bị điều chỉnh giảm tương ứng vào sáng ngày GDKHQ.")
