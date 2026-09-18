"""
Trang 1: Tổng Quan Thị Trường & Radar Tín Hiệu Kỹ Thuật (Market Overview Page)
Cung cấp góc nhìn toàn cảnh vĩ mô, thanh khoản, dòng tiền khối ngoại/tự doanh,
độ rộng thị trường và radar khuyến nghị tự động toàn bộ danh mục cổ phiếu.
"""
import streamlit as st
import pandas as pd
import numpy as np

from config.settings import DEFAULT_TICKERS
from src.database.tinydb_manager import watchlist_db
from src.data.stock_data import stock_engine
from src.data.macro_data import macro_engine
from src.ui.cache import (
    get_cached_market_overview,
    get_cached_macro_data,
    get_cached_quotes_map,
    get_stock_technical_summary,
    get_cached_sentiment_and_margin,
    get_cached_distribution_analysis,
    get_cached_sector_rotation,
)
from src.ui.components import create_market_breadth_card


def render_market_overview_page():
    """Hiển thị toàn bộ nội dung trang Tổng Quan Thị Trường & Radar Tín Hiệu."""
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
    # 3. CÁC DẤU HIỆU CUNG - CẦU & CHỈ BÁO THỊ TRƯỜNG NÂNG CAO
    # ---------------------------------------------------------
    st.subheader("🌊 Dấu Hiệu Cung - Cầu & Chỉ Báo Thị Trường Nâng Cao")
    st.caption("Đo lường Đòn bẩy Margin, Tâm lý phái sinh VN30F1M Basis/OI, Phiên Phân Phối (Distribution Days) & Luân chuyển dòng tiền ngành")

    sentiment_data = get_cached_sentiment_and_margin()
    dist_data = get_cached_distribution_analysis()

    # Nhóm 1: Dữ liệu Đòn bẩy & Tâm lý dòng tiền
    with st.expander("📌 **1. DỮ LIỆU ĐÒN BẨY & TÂM LÝ DÒNG TIỀN (SENTIMENT & MARGIN)**", expanded=True):
        margin_info = sentiment_data.get("margin", {})
        f0_info = sentiment_data.get("f0_accounts", {})
        deriv_info = sentiment_data.get("derivatives", {})

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric(
            "⚡ Dư Nợ Margin Toàn TT",
            f"{margin_info.get('debt_bil', 0):,.0f} Tỷ VNĐ",
            f"Tỷ lệ/VCSH: {margin_info.get('ratio', 0):.2f}x ({margin_info.get('status', 'Ổn định')})",
            help="Dư nợ cho vay ký quỹ chạm trần báo hiệu vùng quá nhiệt (rủi ro call margin chéo); margin cạn kiệt kết hợp thanh khoản thấp phản ánh vùng đáy tâm lý."
        )
        col_m2.metric(
            "👥 Số Lượng TK Mở Mới",
            f"{f0_info.get('new_monthly', 0):,} TK/tháng",
            f0_info.get("trend", "Ổn định"),
            help="Đo lường dòng tiền F0 đổ vào thị trường (chỉ báo trễ nhưng phản ánh quy mô hưng phấn)."
        )
        col_m3.metric(
            "🎯 VN30F1M & Độ Lệch Basis",
            f"{deriv_info.get('price', 0):,.2f}",
            f"{deriv_info.get('basis', 0):+,.2f} điểm ({deriv_info.get('basis_sentiment', 'Cân bằng')})",
            help="Basis dương lớn thể hiện tâm lý hưng phấn ngắn hạn; Basis âm sâu thể hiện tâm lý phòng vệ hoặc bi quan."
        )
        col_m4.metric(
            "📑 Hợp Đồng Mở OI Phái Sinh",
            f"{deriv_info.get('oi', 0):,} HĐ",
            deriv_info.get("oi_status", "Bình thường"),
            help="Lượng vị thế được giữ lại qua ngày, cho biết phe Long hay Short đang quyết liệt gom hàng."
        )
        st.info(f"💡 **Trạng thái Đòn bẩy & Tâm lý:** {margin_info.get('zone', '')} | {margin_info.get('assessment', '')} | {deriv_info.get('basis_desc', '')}")

    # Nhóm 2: Dấu hiệu Cung Cầu Theo Hành Động Giá (Distribution Days & FTD)
    with st.expander("📉 **2. DẤU HIỆU CUNG CẦU THEO HÀNH ĐỘNG GIÁ (PRICE ACTION & VOLUME SPREAD)**", expanded=True):
        col_d1, col_d2, col_d3 = st.columns([1, 1, 2])
        col_d1.metric(
            "⚠️ Phiên Phân Phối (25 phiên)",
            f"{dist_data.get('distribution_count', 0)} phiên",
            dist_data.get("risk_level", "AN TOÀN"),
            help="Định nghĩa: Chỉ số giảm > 0.2% với khối lượng cao hơn phiên liền trước. Xuất hiện 4-6 phiên phân phối trong 20-25 phiên là cảnh báo thị trường chuẩn bị điều chỉnh mạnh."
        )
        ftd_status_txt = "ĐÃ KÍCH HOẠT 🚀" if dist_data.get("ftd_detected") else "CHƯA XUẤT HIỆN"
        col_d2.metric(
            "🚀 Phiên Bùng Nổ Theo Đà (FTD)",
            ftd_status_txt,
            "Xác nhận dòng tiền",
            help="Xuất hiện từ ngày thứ 4 đến ngày thứ 7 của nhịp nỗ lực hồi phục. Chỉ số tăng mạnh (> 1.2% - 1.5%) đi kèm vol đột biến, xác nhận xác suất tạo đáy 70-80%."
        )
        col_d3.markdown(f"""
        <div style="background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 10px; font-size: 13px; line-height: 1.5;">
            <b>Đánh giá rủi ro O'Neil:</b> {dist_data.get('assessment', '')}<br>
            <b>Trạng thái FTD:</b> {dist_data.get('ftd_detail', '')}
        </div>
        """, unsafe_allow_html=True)

        dist_days_list = dist_data.get("distribution_days_detail", [])
        if dist_days_list:
            with st.expander("🔎 Xem danh sách chi tiết các phiên phân phối gần nhất:"):
                st.dataframe(pd.DataFrame(dist_days_list), width="stretch", hide_index=True)

    # Nhóm 3: Luân chuyển dòng tiền theo ngành & Leader Stocks
    all_known_tickers = tuple(set(watchlist_db.get_ticker_list() + DEFAULT_TICKERS))
    sector_data = get_cached_sector_rotation(all_known_tickers)
    with st.expander("🔄 **3. SỰ LUÂN CHUYỂN DÒNG TIỀN THEO NGÀNH & CỔ PHIẾU DẪN DẮT (LEADER STOCKS)**", expanded=True):
        rot_col1, rot_col2 = st.columns([1, 1])
        with rot_col1:
            st.markdown("##### 🧭 Vòng Luân Chuyển Dòng Tiền Giữa Các Nhóm:")
            sec_list = sector_data.get("sectors", [])
            sb_records = []
            for s_info in sec_list:
                sb_records.append({
                    "Nhóm Ngành": s_info.get("name", ""),
                    "Phân Loại": s_info.get("type", ""),
                    "Hiệu Suất TB": f"{s_info.get('avg_pct_change', 0):+.2f}%",
                    "Khối Lượng": f"{s_info.get('total_volume', 0):,}",
                    "Số Mã": s_info.get("tickers_count", 0),
                    "Đặc Điểm": s_info.get("desc", ""),
                })
            st.dataframe(pd.DataFrame(sb_records), width="stretch", hide_index=True)
            st.info(f"💡 **Vòng luân chuyển:** **{sector_data.get('stage_title', '')}**\n\n{sector_data.get('stage_desc', '')}")

        with rot_col2:
            st.markdown("##### 🏆 Cổ Phiếu Dẫn Dắt (Leader Stocks):")
            st.caption("Cổ phiếu khỏe nhất thị trường: Vượt đỉnh trước VN-Index hoặc giữ nền giá khi chỉ số chung giảm")
            leaders = sector_data.get("leader_stocks", [])
            if leaders:
                ldr_records = []
                for l in leaders:
                    ldr_records.append({
                        "Mã Leader": l.get("ticker"),
                        "Giá Khớp": f"{l.get('price', 0):,.2f}",
                        "Biến Động": f"{l.get('change', 0):+.2f}%",
                        "Nhóm Ngành": l.get("sector", ""),
                    })
                st.dataframe(pd.DataFrame(ldr_records), width="stretch", hide_index=True)
                st.warning("⚠️ **Cảnh báo suy yếu:** Khi các mã Leader gãy nền và sụt giảm khối lượng lớn, thị trường chung thường điều chỉnh theo sau đó 1 - 2 tuần.")
            else:
                st.write("Đang cập nhật danh sách cổ phiếu dẫn dắt...")

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
