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
            st.subheader("🤖 Dự Báo Xu Hướng Giá Bằng Máy Học (Gradient Boosting / LightGBM)")
            st.caption("Mô hình học máy huấn luyện trực tiếp trên chuỗi nến lịch sử thật và các đặc trưng động lượng (RSI, MA, MACD, Volume)")

            if "error" in ml_result and ml_result.get("error"):
                st.warning(ml_result["error"])
            else:
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                m_col1.metric("Tín Hiệu AI", ml_result.get("ml_signal", "TRUNG LẬP"))
                m_col2.metric("Giá Kỳ Vọng T+5", f"{ml_result.get('final_predicted_price', 0):,.2f} k", f"{ml_result.get('final_expected_return', 0):+.2f}%")
                m_col3.metric("Độ Chính Xác Hướng Đi", f"{ml_result.get('directional_accuracy', 0)}%")
                m_col4.metric("Sai Số Huấn Luyện (MAE)", f"{ml_result.get('mae', 0):,.2f} k ({ml_result.get('error_pct', 0)}%)")

                st.info(f"💡 **Nhận định từ Mô hình Máy học:** {ml_result.get('comment')}")

                # Biểu đồ dự báo nến thực tế + đường AI
                ml_fig = create_ml_forecast_chart(df_indicators, ml_result, active_sym)
                st.plotly_chart(ml_fig, use_container_width=True)

                # Bảng chi tiết từng phiên T+
                sub_col1, sub_col2 = st.columns([1, 1])
                with sub_col1:
                    st.markdown("#### Bảng Giá Dự Báo 5 Phiên Tới (T+1 đến T+5)")
                    pred_table = []
                    for p in ml_result.get("predictions", []):
                        pred_table.append({
                            "Phiên": p["step"],
                            "Ngày": p["date"],
                            "Giá Dự Báo (k)": f"{p['predicted_price']:,.2f}",
                            "Giá VNĐ": f"{p['predicted_price']*1000:,.0f} đ",
                            "Biến Động Dự Kiến": f"{p['expected_return_pct']:+.2f}%",
                        })
                    st.dataframe(pd.DataFrame(pred_table), use_container_width=True, hide_index=True)

                with sub_col2:
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
