"""
ỨNG DỤNG THEO DÕI, DỰ BÁO & BÁO CÁO CHỨNG KHOÁN VIỆT NAM (VN-STOCK TRACKER & FORECAST)
Giao diện Streamlit Dashboard hiện đại, kết nối dữ liệu tức thì, lưu trữ TinyDB NoSQL.
"""
import time
from datetime import datetime
import streamlit as st
import pandas as pd

# Import các module cốt lõi của dự án
from config.settings import DEFAULT_TICKERS, AUTO_REFRESH_INTERVAL
from src.database.tinydb_manager import watchlist_db
from src.data.stock_data import stock_engine
from src.data.market_data import market_engine
from src.analysis.indicators import calculate_indicators, generate_technical_signals
from src.analysis.forecasting import forecast_price_trend
from src.analysis.ml_forecasting import train_and_forecast_ml
from src.reporting.report_builder import generate_ticker_report_html, generate_ticker_report_markdown
from src.ui.components import (
    create_candlestick_chart,
    create_forecast_chart,
    create_ml_forecast_chart,
    create_feature_importance_chart,
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

# Custom CSS giao diện hiện đại & các thẻ KPI
st.markdown("""
<style>
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

# -------------------------------------------------------------
# 2. SIDEBAR - THANH ĐIỀU HƯỚNG & CÀI ĐẶT
# -------------------------------------------------------------
st.sidebar.markdown("## 📈 **VN-Stock Analytics**")
st.sidebar.caption("Hệ thống theo dõi & dự báo chứng khoán tức thì")

navigation = st.sidebar.radio(
    "CHỌN CHỨC NĂNG",
    [
        "📊 Tổng quan Thị trường",
        "⭐ Danh mục Yêu thích (Watchlist)",
        "🔍 Phân tích Chi tiết & Dự báo",
        "📑 Xuất Báo cáo Phân tích",
    ],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Cấu hình Tự động Làm mới")
auto_refresh = st.sidebar.checkbox("Bật tự động làm mới", value=False)
refresh_rate = st.sidebar.slider("Tần suất (giây)", min_value=5, max_value=60, value=AUTO_REFRESH_INTERVAL, step=5)

if st.sidebar.button("🔄 Làm mới dữ liệu ngay", use_container_width=True):
    st.rerun()

# Kiểm tra & hiển thị cảnh báo giá tức thì từ Watchlist
all_watchlist = watchlist_db.get_all()
active_alerts = []
for item in all_watchlist:
    sym = item["ticker"]
    quote = stock_engine.get_realtime_quote(sym)
    alerts = watchlist_db.check_price_alerts(sym, quote["price"])
    active_alerts.extend(alerts)

if active_alerts:
    st.sidebar.markdown("---")
    st.sidebar.error("🔔 **CẢNH BÁO GIÁ KÍCH HOẠT!**")
    for alt in active_alerts:
        st.sidebar.warning(alt)

st.sidebar.markdown("---")
st.sidebar.caption(f"🕒 Lần cập nhật cuối: {datetime.now().strftime('%H:%M:%S')}")
st.sidebar.caption("💾 Lưu trữ NoSQL: `TinyDB (JSON)`")


# -------------------------------------------------------------
# 3. TRANG 1: TỔNG QUAN THỊ TRƯỜNG (MARKET OVERVIEW)
# -------------------------------------------------------------
if navigation == "📊 Tổng quan Thị trường":
    st.title("📊 Tổng Quan Thị Trường Chứng Khoán Việt Nam")
    st.caption("Cập nhật chỉ số VN-Index, VN30, độ rộng và thanh khoản toàn thị trường")

    mkt_data = market_engine.get_market_overview()
    indexes = mkt_data["indexes"]

    # Hiển thị 4 cột chỉ số chính
    cols = st.columns(4)
    for idx, col in enumerate(cols):
        item = indexes[idx]
        change_sign = "+" if item["change"] >= 0 else ""
        delta_str = f"{change_sign}{item['change']:,.2f} ({change_sign}{item['pct_change']}%)"
        col.metric(
            label=f"📌 {item['name']}",
            value=f"{item['value']:,.2f}",
            delta=delta_str,
        )

    st.markdown("---")

    # Độ rộng thị trường & Thanh khoản
    breadth = mkt_data["breadth"]
    b_col1, b_col2, b_col3, b_col4 = st.columns(4)
    b_col1.metric("🟢 Mã Tăng giá", f"{breadth['advances']} mã")
    b_col2.metric("🔴 Mã Giảm giá", f"{breadth['declines']} mã")
    b_col3.metric("🟡 Không đổi", f"{breadth['no_changes']} mã")
    b_col4.metric("💰 Thanh khoản ước tính", f"{breadth['liquidity_bil']:,.0f} Tỷ VND")

    st.markdown("---")
    st.subheader("🔥 Bảng Giá Trực Tuyến Các Cổ Phiếu Tâm Điểm")
    
    # Lấy bảng giá các mã trong Watchlist
    fav_tickers = watchlist_db.get_ticker_list()
    quotes = stock_engine.get_quotes_batch(fav_tickers)

    table_records = []
    for q in quotes:
        table_records.append({
            "Mã CK": q["ticker"],
            "Giá Khớp (k)": f"{q['price']:,.2f}",
            "Giá Thực Tế (VNĐ)": f"{q['price']*1000:,.0f} đ",
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

    st.dataframe(pd.DataFrame(table_records), use_container_width=True, hide_index=True)


# -------------------------------------------------------------
# 4. TRANG 2: DANH MỤC YÊU THÍCH (WATCHLIST - TINYDB)
# -------------------------------------------------------------
elif navigation == "⭐ Danh mục Yêu thích (Watchlist)":
    st.title("⭐ Quản Lý Danh Mục Cổ Phiếu Yêu Thích")
    st.caption("Lưu trữ NoSQL TinyDB chuẩn JSON - Cài đặt ngưỡng cảnh báo chốt lời / cắt lỗ tức thì")

    watchlist_items = watchlist_db.get_all()

    # Form thêm mã mới
    with st.expander("➕ **Thêm Mã Cổ Phiếu Mới Vào Danh Sách Theo Dõi**", expanded=False):
        with st.form("add_ticker_form"):
            f_col1, f_col2, f_col3 = st.columns(3)
            new_ticker = f_col1.text_input("Mã Cổ Phiếu (VD: HPG, FPT, VNM)*").strip().upper()
            target_p = f_col2.number_input("Giá Mục Tiêu Chốt Lời (VND)", min_value=0.0, step=1.0, value=0.0)
            stop_l = f_col3.number_input("Ngưỡng Cắt Lỗ (VND)", min_value=0.0, step=1.0, value=0.0)
            
            f_note = st.text_input("Ghi chú chiến lược đầu tư (Tùy chọn)", placeholder="Ví dụ: Mua gom vùng hỗ trợ, chờ báo cáo Q3")
            f_alert = st.checkbox("Bật cảnh báo tự động khi chạm ngưỡng", value=True)
            
            submitted = st.form_submit_button("Lưu Vào Watchlist", use_container_width=True)
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
        for item in watchlist_items:
            sym = item["ticker"]
            q = stock_engine.get_realtime_quote(sym)
            p_class = "price-up" if q["change"] > 0 else ("price-down" if q["change"] < 0 else "price-ref")

            with st.container():
                c1, c2, c3, c4, c5 = st.columns([1.5, 2, 2, 3, 1])
                
                # Cột 1: Mã & Trạng thái
                c1.markdown(f"### **{sym}**")
                c1.caption(f"Thêm lúc: {item.get('added_at', 'N/A')[:10]}")
                
                # Cột 2: Giá Realtime
                c2.markdown(f"<div class='{p_class}' style='font-size: 22px;'>{q['price']:,.2f} k <span style='font-size: 14px; color: #94a3b8;'>({q['price']*1000:,.0f} đ)</span></div>", unsafe_allow_html=True)
                c2.caption(f"{'+' if q['change'] >= 0 else ''}{q['change']:,.2f} ({'+' if q['pct_change'] >= 0 else ''}{q['pct_change']:.2f}%)")

                # Cột 3: Ngưỡng cảnh báo
                tp_str = f"{item['target_price']:,.1f}" if item.get("target_price") else "Chưa đặt"
                sl_str = f"{item['stop_loss']:,.1f}" if item.get("stop_loss") else "Chưa đặt"
                c3.markdown(f"🎯 **Target:** `{tp_str}`\n\n⚠️ **Stop:** `{sl_str}`")

                # Cột 4: Ghi chú
                c4.info(item.get("note") or "Không có ghi chú")

                # Cột 5: Nút Xóa
                if c5.button("🗑️ Xóa", key=f"del_{sym}"):
                    watchlist_db.remove(sym)
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

    t_col1, t_col2, t_col3 = st.columns([2, 1, 1])
    selected_ticker = t_col1.selectbox("Chọn mã từ Watchlist:", fav_list, index=0)
    manual_ticker = t_col2.text_input("Hoặc nhập mã bất kỳ:").strip().upper()
    active_sym = manual_ticker if manual_ticker else selected_ticker

    forecast_days = t_col3.slider("Số phiên dự báo:", min_value=3, max_value=15, value=7)

    if active_sym:
        # Lấy dữ liệu nến lịch sử và tính chỉ báo
        with st.spinner(f"Đang phân tích dữ liệu cho mã {active_sym}..."):
            df = stock_engine.get_historical_ohlcv(active_sym, days=180)
            df_indicators = calculate_indicators(df)
            signals = generate_technical_signals(df_indicators)
            forecast = forecast_price_trend(df_indicators, forecast_days=forecast_days)
            ml_result = train_and_forecast_ml(df_indicators, forecast_days=min(forecast_days, 5), target_ticker=active_sym)
            quote = stock_engine.get_realtime_quote(active_sym)

        # Header thông tin mã
        h1, h2, h3, h4 = st.columns(4)
        h1.metric("Mã Cổ Phiếu", active_sym, quote.get("status", "LIVE"))
        h2.metric("Giá Khớp Hiện Tại", f"{quote['price']:,.2f} k ({quote['price']*1000:,.0f} đ)", f"{'+' if quote['change'] >= 0 else ''}{quote['change']:,.2f} ({quote['pct_change']:+.2f}%)")
        h3.metric("Khối Lượng Khớp", f"{quote['volume']:,}")
        
        # Action badge
        action = signals.get("action", "TRUNG LẬP")
        h4.metric("Khuyến Nghị Kỹ Thuật", action, f"Điểm: {signals.get('score', 50)}/100")

        st.markdown("---")

        # Tab chia nhỏ giữa Biểu đồ kỹ thuật, Dự báo AI Machine Learning & Mô phỏng Monte Carlo
        tab_chart, tab_ml, tab_forecast = st.tabs([
            "📊 Biểu đồ Nến Kỹ thuật",
            "🤖 Dự Báo Máy Học (AI / Gradient Boosting)",
            "🎲 Mô Phỏng Xác Suất Monte Carlo",
        ])

        with tab_chart:
            # Tùy chọn hiển thị chỉ báo
            c_opt1, c_opt2, c_opt3 = st.columns(3)
            s_sma = c_opt1.checkbox("Hiển thị Đường Trung Bình (SMA 20, 50)", value=True)
            s_bb = c_opt2.checkbox("Hiển thị Dải Bollinger Bands", value=True)
            s_rsi = c_opt3.checkbox("Hiển thị Chỉ số RSI(14)", value=True)

            chart_fig = create_candlestick_chart(
                df_indicators,
                active_sym,
                show_sma=s_sma,
                show_bb=s_bb,
                show_rsi=s_rsi,
            )
            st.plotly_chart(chart_fig, use_container_width=True)

            # Khối lý do tín hiệu
            st.subheader("💡 Tín Hiệu Phân Tích Kỹ Thuật Tự Động")
            for r in signals.get("reasons", []):
                st.write(f"- {r}")

        with tab_ml:
            st.subheader("🌐 Đối Chiếu Đa Chiều Các Mô Hình Dự Báo Xu Hướng Giá")
            st.caption("Tổng hợp và so sánh độc lập giữa các thuật toán Machine Learning, Mô hình Định lượng và Xác suất Thống kê")

            if "error" in ml_result and ml_result.get("error"):
                st.warning(ml_result["error"])
            else:
                all_models_dict = ml_result.get("models", {})
                future_dates = ml_result.get("future_dates", [])

                # 1. BỘ CHỌN MÔ HÌNH TRỰC QUAN BẰNG CHECKBOX
                st.markdown("#### 🎯 Tùy Chọn Các Mô Hình Muốn Đối Chiếu:")
                
                c_btn1, c_btn2, _ = st.columns([1, 1, 4])
                select_all = c_btn1.button("✅ Chọn Tất Cả", key="sel_all_models")
                reset_btn = c_btn2.button("🔄 Mặc Định", key="reset_models")

                # Trạng thái mặc định hoặc lưu session
                if select_all:
                    st.session_state["cb_gb"] = True
                    st.session_state["cb_rf"] = True
                    st.session_state["cb_tech"] = True
                    st.session_state["cb_mc"] = True
                    st.session_state["cb_cs"] = True
                elif reset_btn:
                    st.session_state["cb_gb"] = True
                    st.session_state["cb_rf"] = True
                    st.session_state["cb_tech"] = True
                    st.session_state["cb_mc"] = True
                    st.session_state["cb_cs"] = True

                mc1, mc2, mc3, mc4, mc5 = st.columns(5)
                sel_gb = mc1.checkbox("🟣 Gradient Boosting (AI)", value=st.session_state.get("cb_gb", True), key="cb_gb")
                sel_rf = mc2.checkbox("🟢 Random Forest", value=st.session_state.get("cb_rf", True), key="cb_rf")
                sel_tech = mc3.checkbox("🟠 Quán Tính Kỹ Thuật", value=st.session_state.get("cb_tech", True), key="cb_tech")
                sel_mc = mc4.checkbox("🟡 Monte Carlo (Cơ Sở)", value=st.session_state.get("cb_mc", True), key="cb_mc")
                sel_cs = mc5.checkbox("🔵 Đồng Thuận Tổng Hợp", value=st.session_state.get("cb_cs", True), key="cb_cs")

                # Danh sách các mô hình được người dùng tích chọn
                selected_models = []
                if sel_gb and "Gradient Boosting (AI)" in all_models_dict:
                    selected_models.append("Gradient Boosting (AI)")
                if sel_rf and "Random Forest" in all_models_dict:
                    selected_models.append("Random Forest")
                if sel_tech and "Quán Tính Kỹ Thuật" in all_models_dict:
                    selected_models.append("Quán Tính Kỹ Thuật")
                if sel_mc and "Monte Carlo (Cơ Sở)" in all_models_dict:
                    selected_models.append("Monte Carlo (Cơ Sở)")
                if sel_cs and "Đồng Thuận Tổng Hợp (Consensus)" in all_models_dict:
                    selected_models.append("Đồng Thuận Tổng Hợp (Consensus)")

                # Nếu chưa chọn gì, hiển thị cảnh báo hướng dẫn và không tính max/min
                if not all_models_dict:
                    st.warning("⚠️ Chưa có dữ liệu mô hình dự báo cho mã cổ phiếu này.")
                elif not selected_models:
                    st.warning("⚠️ Bạn đang bỏ chọn tất cả các mô hình. Vui lòng tick chọn ít nhất 1 mô hình ở trên để xem phân tích xu hướng!")
                else:
                    st.markdown("---")

                    # 2. PHÂN TÍCH SỐ LIỆU ĐA CHIỀU DỰA TRÊN CÁC MÔ HÌNH ĐÃ CHỌN
                    selected_returns = [all_models_dict[m]["expected_return"] for m in selected_models if m in all_models_dict]
                    selected_prices = [all_models_dict[m]["final_price"] for m in selected_models if m in all_models_dict]

                    avg_return = float(np.mean(selected_returns)) if selected_returns else 0.0
                    avg_price = float(np.mean(selected_prices)) if selected_prices else quote["price"]
                    best_model = max(selected_models, key=lambda m: all_models_dict[m]["expected_return"])
                    worst_model = min(selected_models, key=lambda m: all_models_dict[m]["expected_return"])
                    spread = all_models_dict[best_model]["expected_return"] - all_models_dict[worst_model]["expected_return"]

                    # Hiển thị 4 thẻ KPI tổng hợp từ các mô hình đang chọn
                    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
                    c_sign_avg = "+" if avg_return >= 0 else ""
                    kpi_col1.metric("Giá Kỳ Vọng Trung Bình", f"{avg_price:,.2f} k", f"{c_sign_avg}{avg_return:.2f}%")
                    kpi_col2.metric("Số Mô Hình Đang Đối Chiếu", f"{len(selected_models)}/5 mô hình", "Góc nhìn đa chiều")
                    kpi_col3.metric(f"Lạc Quan Nhất ({best_model.split()[0]})", f"{all_models_dict[best_model]['final_price']:,.2f} k", f"{all_models_dict[best_model]['expected_return']:+.2f}%")
                    kpi_col4.metric(f"Thận Trọng Nhất ({worst_model.split()[0]})", f"{all_models_dict[worst_model]['final_price']:,.2f} k", f"{all_models_dict[worst_model]['expected_return']:+.2f}%")

                    # BẢN MÔ TẢ PHÂN TÍCH XU HƯỚNG TỔNG HỢP CHI TIẾT
                    st.markdown("#### 📝 Nhận Định Xu Hướng Tổng Hợp Từ Các Mô Hình Đã Chọn:")
                    
                    # Logic diễn giải xu hướng
                    if avg_return >= 3.0:
                        trend_headline = "🟢 XU HƯỚNG TĂNG GIÁ MẠNH (STRONG BULLISH)"
                        trend_color = "success"
                        action_advice = "Ưu tiên nắm giữ cổ phiếu, canh các nhịp điều chỉnh trong phiên để gia tăng tỷ trọng. Vùng giá chốt lời kỳ vọng hướng tới mốc " + f"**{avg_price:,.2f} k ({avg_price*1000:,.0f} VNĐ)**."
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
                    - **Mức giá dự phóng bình quân:** `{avg_price:,.2f} k` ({avg_price*1000:,.0f} đ), tương ứng biến động kỳ vọng `{c_sign_avg}{avg_return:.2f}%` sau 5 phiên tới.
                    - **Kịch bản cao nhất:** Mô hình **{best_model}** dự báo giá có thể chạm mốc **{all_models_dict[best_model]['final_price']:,.2f} k** ({all_models_dict[best_model]['expected_return']:+.2f}%).
                    - **Kịch bản bảo thủ:** Mô hình **{worst_model}** nhận định giá ở mức **{all_models_dict[worst_model]['final_price']:,.2f} k** ({all_models_dict[worst_model]['expected_return']:+.2f}%).
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

                    # 3. BIỂU ĐỒ ĐỐI CHIẾU ĐA CHIỀU
                    ml_fig = create_multi_model_comparison_chart(df_indicators, ml_result, selected_models, active_sym)
                    st.plotly_chart(ml_fig, use_container_width=True)

                    # 4. BẢNG SO SÁNH CHI TIẾT TỪNG PHIÊN THEO CÁC MÔ HÌNH ĐÃ CHỌN
                    st.markdown("#### 📋 Bảng So Sánh Dự Báo Chi Tiết Từng Phiên (Theo Các Mô Hình Đã Chọn)")
                    
                    dyn_table = []
                    for step_idx in range(len(future_dates)):
                        step_date = future_dates[step_idx]
                        row = {
                            "Phiên": f"T+{step_idx+1}",
                            "Ngày GD": step_date,
                        }
                        step_prices = []
                        for m_name in selected_models:
                            if m_name in all_models_dict:
                                p_val = all_models_dict[m_name]["prices"][step_idx]
                                row[m_name] = f"{p_val:,.2f} k"
                                step_prices.append(p_val)

                        if step_prices:
                            step_avg = float(np.mean(step_prices))
                            row["Trung Bình Đã Chọn"] = f"{step_avg:,.2f} k"
                            row["Giá VNĐ Bình Quân"] = f"{step_avg*1000:,.0f} đ"
                            row["% So Giá Hiện Tại"] = f"{((step_avg - quote['price']) / quote['price'] * 100):+.2f}%"

                        dyn_table.append(row)

                    st.dataframe(pd.DataFrame(dyn_table), use_container_width=True, hide_index=True)

                    # 5. BIỂU ĐỒ TRỌNG SỐ ĐÓNG GÓP (FEATURE IMPORTANCE)
                    st.markdown("---")
                    fi_fig = create_feature_importance_chart(ml_result.get("feature_importance", []))
                    st.plotly_chart(fi_fig, use_container_width=True)

        with tab_forecast:
            st.subheader(f"🎲 Mô Phỏng Kịch Bản Xác Suất Monte Carlo ({forecast_days} Phiên Tới)")
            
            f_col1, f_col2, f_col3 = st.columns(3)
            f_col1.metric("Xu Hướng Chủ Đạo", forecast.get("outlook", "N/A"))
            f_col2.metric("Xác Suất Tăng Giá", f"{forecast.get('upward_probability', 50)}%")
            f_col3.metric("Mục Tiêu Cơ Sở (Base)", f"{forecast.get('target_price_base', 0):,.1f}", f"{forecast.get('expected_return_pct', 0):+.2f}%")

            st.info(f"👉 **Khuyến nghị:** {forecast.get('recommendation', 'Quan sát')}")

            # Đồ thị dự báo Monte Carlo Fan Chart
            forecast_fig = create_forecast_chart(df_indicators, forecast, active_sym)
            st.plotly_chart(forecast_fig, use_container_width=True)

            # Bảng chi tiết từng phiên
            st.markdown("#### Bảng Kịch Bản Giá Chi Tiết Theo Phiên")
            st.dataframe(forecast.get("forecast_df"), use_container_width=True, hide_index=True)


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
            quote = stock_engine.get_realtime_quote(rep_ticker)
            df = stock_engine.get_historical_ohlcv(rep_ticker, days=180)
            df_ind = calculate_indicators(df)
            signals = generate_technical_signals(df_ind)
            forecast = forecast_price_trend(df_ind, forecast_days=7)
            wl_info = watchlist_db.get_by_ticker(rep_ticker)

            md_report = generate_ticker_report_markdown(rep_ticker, quote, signals, forecast, wl_info)
            html_report = generate_ticker_report_html(rep_ticker, quote, signals, forecast, wl_info)

        r_col1, r_col2 = st.columns([3, 1])
        r_col1.markdown(f"### Xem trước Báo Cáo: **{rep_ticker}**")
        
        # Nút tải file
        r_col2.download_button(
            label="📥 Tải Báo Cáo HTML",
            data=html_report,
            file_name=f"Bao_Cao_{rep_ticker}_{datetime.now().strftime('%Y%m%d')}.html",
            mime="text/html",
            use_container_width=True,
        )

        st.markdown(md_report)

# Tự động refresh nếu được bật
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
