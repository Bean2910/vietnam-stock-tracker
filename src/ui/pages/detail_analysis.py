"""
Trang 3: Phân Tích Kỹ Thuật Chi Tiết, Định Giá & Dự Báo (Detail Analysis Page)
Bao gồm 4 tabs chuyên sâu:
1. Biểu đồ Kỹ thuật TradingView Plotly, SMA, BB, RSI, MACD & Hệ số Beta
2. Phân tích cơ bản (FA), Định giá (P/E, P/B, PEG) & Checklist đầu tư
3. Đối chiếu đa chiều 4 thuật toán Machine Learning (AI, Random Forest, Quán tính, Đồng thuận)
4. Mô phỏng kịch bản xác suất Monte Carlo Cone & Fan Chart
"""
import streamlit as st
import pandas as pd
import numpy as np

from config.settings import DEFAULT_TICKERS
from src.database.tinydb_manager import watchlist_db
from src.data.stock_data import stock_engine
from src.data.fundamental_data import fundamental_engine
from src.ui.cache import (
    get_cached_ticker_analysis,
    get_cached_volume_profile,
    get_cached_vsa_patterns,
    get_cached_valuation_bands,
)
from src.ui.styles import PLOTLY_CONFIG
from src.ui.components import (
    create_candlestick_chart,
    create_forecast_chart,
    create_multi_model_comparison_chart,
    create_feature_importance_chart,
    create_volume_profile_chart,
    create_valuation_bands_chart,
)


def render_detail_analysis_page():
    """Hiển thị toàn bộ nội dung trang Phân Tích Chi Tiết & Dự Báo."""
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

        # Tab chia nhỏ giữa Biểu đồ kỹ thuật, Phân tích cơ bản FA, Dự báo AI Machine Learning, Mô phỏng Monte Carlo & Volume Profile / VSA
        tab_chart, tab_fa, tab_ml, tab_forecast, tab_vp = st.tabs([
            "📊 Biểu Đồ Kỹ Thuật & Beta",
            "🏢 Phân Tích Cơ Bản (FA) & Định Giá",
            "🤖 Dự Báo Máy Học (AI / Gradient Boosting)",
            "🎲 Mô Phỏng Xác Suất Monte Carlo",
            "📦 Khối Lượng Theo Mức Giá (Volume Profile) & VSA",
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

            # Dải Định Giá Lịch Sử Historical Valuation Bands (P/E Bands +-1SD, +-2SD)
            val_bands = get_cached_valuation_bands(active_sym)
            st.info(f"💡 **Trạng thái P/E Bands:** **{val_bands.get('pe_status', '')}** — {val_bands.get('pe_recommendation', '')}")
            vb_fig = create_valuation_bands_chart(df, active_sym, val_bands)
            st.plotly_chart(vb_fig, width="stretch", config=PLOTLY_CONFIG, on_select="ignore")

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

        with tab_vp:
            st.subheader(f"📦 Khối Lượng Theo Mức Giá (Volume Profile) & Mẫu Hình VSA - {active_sym}")
            st.caption("Xác định vùng kiểm soát Point of Control (POC), Vùng giá trị Value Area (VAH/VAL) và Mẫu hình hành động giá VSA")

            vp_info = get_cached_volume_profile(active_sym)
            vsa_patterns = get_cached_vsa_patterns(active_sym)

            # Metric Cards
            vp_col1, vp_col2, vp_col3, vp_col4 = st.columns(4)
            poc_val = vp_info.get("poc_price", 0)
            vah_val = vp_info.get("vah", 0)
            val_val = vp_info.get("val", 0)

            vp_col1.metric(
                "🎯 Point of Control (POC)",
                f"{poc_val:,.2f}",
                f"{poc_val * 1000:,.0f} VNĐ",
                help="Vùng giá có khối lượng tích lũy lớn nhất trong giai đoạn. Đóng vai trò nam châm hút giá hoặc hỗ trợ/kháng cự cứng nhất."
            )
            vp_col2.metric(
                "🔺 Value Area High (VAH)",
                f"{vah_val:,.2f}",
                "Biên trên 70% KL",
                help="Mức giá cao nhất trong vùng giá trị (Value Area), nơi tập trung 70% tổng khối lượng trao tay."
            )
            vp_col3.metric(
                "🔻 Value Area Low (VAL)",
                f"{val_val:,.2f}",
                "Biên dưới 70% KL",
                help="Mức giá thấp nhất trong vùng giá trị (Value Area)."
            )
            curr_pos_desc = vp_info.get("position", "N/A")
            vp_col4.metric(
                "📍 Vị Thế Giá So Với POC",
                curr_pos_desc.split(" (")[0] if " (" in curr_pos_desc else curr_pos_desc,
                f"Giá hiện tại: {quote['price']:,.2f}",
                help=curr_pos_desc
            )

            st.info(f"💡 **Ý nghĩa Volume Profile:** {vp_info.get('assessment', '')}")

            # Biểu đồ Volume Profile kết hợp nến và POC
            st.markdown("#### 📊 Biểu Đồ Volume Profile & Vùng Khối Lượng Tích Lũy:")
            vp_fig = create_volume_profile_chart(df, active_sym, vp_info)
            st.plotly_chart(vp_fig, width="stretch", config=PLOTLY_CONFIG, on_select="ignore")

            st.markdown("---")

            # Phần VSA Price Action & Volume Spread
            st.subheader("🔍 Dấu Hiệu Cung Cầu Theo Mẫu Hình VSA (Price Action & Volume Spread)")
            st.caption("Nhận diện No Supply Bar / Test Cung (cạn kiệt cung) và Bẫy giá (Bull Trap / Bear Trap)")

            if vsa_patterns:
                st.markdown(f"Đã phát hiện **{len(vsa_patterns)}** tín hiệu nến VSA đặc trưng trong các phiên gần nhất:")
                for pat in vsa_patterns:
                    p_name = pat.get("pattern", "")
                    p_date = pat.get("date", "")
                    p_desc = pat.get("desc", "")
                    p_type = pat.get("type", "")
                    p_badge = pat.get("badge", "")

                    if p_type == "BULLISH":
                        st.success(f"**{p_name}** ({p_badge}) | Ngày: `{p_date}`\n\n- {p_desc}")
                    elif p_type == "BEARISH":
                        st.error(f"**{p_name}** ({p_badge}) | Ngày: `{p_date}`\n\n- {p_desc}")
                    else:
                        st.info(f"**{p_name}** ({p_badge}) | Ngày: `{p_date}`\n\n- {p_desc}")
            else:
                st.write("Chưa ghi nhận tín hiệu cạn cung (No Supply) hoặc bẫy giá (Upthrust/Spring) đột biến trong 10 phiên gần đây. Cổ phiếu đang vận động giá bình thường.")
