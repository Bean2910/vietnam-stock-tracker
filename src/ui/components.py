"""
Module Giao diện & Đồ thị Trực quan hóa (UI Components & Plotly Financial Charts)
Cung cấp các widget chuyên nghiệp: Biểu đồ nến kỹ thuật, Biểu đồ dự báo Monte Carlo, Bảng thẻ giá.
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_candlestick_chart(
    df: pd.DataFrame,
    ticker: str,
    show_sma: bool = True,
    show_sma200: bool = True,
    show_bb: bool = True,
    show_rsi: bool = True,
    show_macd: bool = True,
    n_sessions: Optional[int] = None,
    show_ref_line: bool = False,
    ref_price: Optional[float] = None,
) -> go.Figure:
    """
    Tạo biểu đồ kỹ thuật chuẩn TradingView bằng Plotly:
    - Hàng 1: Nến Nhật + SMA (20, 50, 200) + Bollinger Bands (+ Đường giá tham chiếu nếu bật)
    - Hàng 2: Khối lượng giao dịch (Volume Bar + Vol SMA20)
    - Hàng 3 (Tùy chọn): Chỉ số RSI (14) kèm ngưỡng 70/30
    - Hàng 4 (Tùy chọn): Chỉ báo MACD (Đường MACD, Signal line, Histogram xanh/đỏ)
    """
    plot_df = df.tail(n_sessions).copy() if (n_sessions and n_sessions > 0) else df.copy()

    # Tính toán số hàng và tỷ lệ độ cao linh hoạt
    sub_titles = [f"Biểu đồ Kỹ thuật {ticker}", "Khối lượng (Volume)"]
    row_heights = [0.55, 0.15]
    curr_row = 3

    has_rsi = show_rsi and "RSI14" in plot_df.columns
    has_macd = show_macd and "MACD" in plot_df.columns

    rsi_row = None
    macd_row = None

    if has_rsi:
        sub_titles.append("Chỉ số RSI (14)")
        rsi_row = curr_row
        curr_row += 1

    if has_macd:
        sub_titles.append("Chỉ báo MACD (12, 26, 9)")
        macd_row = curr_row
        curr_row += 1

    total_rows = curr_row - 1
    if total_rows == 4:
        row_heights = [0.46, 0.16, 0.19, 0.19]
        total_height = 840
    elif total_rows == 3:
        row_heights = [0.55, 0.22, 0.23]
        total_height = 740
    else:
        row_heights = [0.72, 0.28]
        total_height = 600

    title_main = f"Biểu đồ Kỹ thuật {ticker} ({n_sessions} phiên gần nhất)" if (n_sessions and n_sessions > 0 and n_sessions < len(df)) else f"Biểu đồ Kỹ thuật {ticker}"
    sub_titles[0] = title_main

    fig = make_subplots(
        rows=total_rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=sub_titles,
    )

    # 1. Nến Nhật (Candlestick)
    fig.add_trace(
        go.Candlestick(
            x=plot_df.index,
            open=plot_df["open"],
            high=plot_df["high"],
            low=plot_df["low"],
            close=plot_df["close"],
            name=ticker,
            increasing_line_color="#10b981",
            decreasing_line_color="#ef4444",
        ),
        row=1,
        col=1,
    )

    # 2. Các đường SMA
    if show_sma:
        if "SMA20" in plot_df.columns:
            fig.add_trace(
                go.Scatter(x=plot_df.index, y=plot_df["SMA20"], mode="lines", name="SMA 20 (Ngắn)", line=dict(color="#f59e0b", width=1.5)),
                row=1, col=1,
            )
        if "SMA50" in plot_df.columns:
            fig.add_trace(
                go.Scatter(x=plot_df.index, y=plot_df["SMA50"], mode="lines", name="SMA 50 (Trung)", line=dict(color="#3b82f6", width=1.5)),
                row=1, col=1,
            )

    if show_sma200 and "SMA200" in plot_df.columns:
        fig.add_trace(
            go.Scatter(x=plot_df.index, y=plot_df["SMA200"], mode="lines", name="SMA 200 (Dài)", line=dict(color="#ec4899", width=1.8, dash="solid")),
            row=1, col=1,
        )

    # 3. Dải Bollinger Bands
    if show_bb and "BB_Upper" in plot_df.columns and "BB_Lower" in plot_df.columns:
        fig.add_trace(
            go.Scatter(x=plot_df.index, y=plot_df["BB_Upper"], mode="lines", name="BB Upper", line=dict(color="rgba(156, 163, 175, 0.6)", width=1, dash="dot")),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=plot_df.index, y=plot_df["BB_Lower"], mode="lines", name="BB Lower",
                line=dict(color="rgba(156, 163, 175, 0.6)", width=1, dash="dot"),
                fill="tonexty", fillcolor="rgba(156, 163, 175, 0.08)",
            ),
            row=1, col=1,
        )

    # 3b. Đường giá tham chiếu ngang (Reference Price Line)
    if show_ref_line and ref_price is not None and ref_price > 0:
        fig.add_hline(
            y=ref_price,
            line_dash="dot",
            line_color="#eab308",
            line_width=1.5,
            annotation_text=f"Tham chiếu: {ref_price:,.2f}",
            annotation_position="bottom right",
            annotation_font=dict(size=11, color="#eab308"),
            row=1, col=1,
        )

    # 4. Khối lượng Volume
    colors = ["#10b981" if c >= o else "#ef4444" for c, o in zip(plot_df["close"], plot_df["open"])]
    fig.add_trace(
        go.Bar(x=plot_df.index, y=plot_df["volume"], name="Volume", marker_color=colors, showlegend=False),
        row=2, col=1,
    )
    if "VOL_SMA20" in plot_df.columns:
        fig.add_trace(
            go.Scatter(x=plot_df.index, y=plot_df["VOL_SMA20"], mode="lines", name="Vol SMA20", line=dict(color="#6366f1", width=1.2)),
            row=2, col=1,
        )

    # 5. Chỉ báo RSI
    if has_rsi and rsi_row is not None:
        fig.add_trace(
            go.Scatter(x=plot_df.index, y=plot_df["RSI14"], mode="lines", name="RSI (14)", line=dict(color="#8b5cf6", width=1.8)),
            row=rsi_row, col=1,
        )
        # Đường ngưỡng 70 và 30
        fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", line_width=1, row=rsi_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#10b981", line_width=1, row=rsi_row, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="rgba(148, 163, 184, 0.4)", line_width=1, row=rsi_row, col=1)

    # 6. Chỉ báo MACD
    if has_macd and macd_row is not None:
        hist_colors = ["#10b981" if float(v) >= 0 else "#ef4444" for v in plot_df.get("MACD_Hist", [])]
        fig.add_trace(
            go.Bar(x=plot_df.index, y=plot_df["MACD_Hist"], name="Histogram", marker_color=hist_colors, showlegend=False),
            row=macd_row, col=1,
        )
        fig.add_trace(
            go.Scatter(x=plot_df.index, y=plot_df["MACD"], mode="lines", name="MACD", line=dict(color="#38bdf8", width=1.6)),
            row=macd_row, col=1,
        )
        fig.add_trace(
            go.Scatter(x=plot_df.index, y=plot_df["MACD_Signal"], mode="lines", name="Signal", line=dict(color="#f59e0b", width=1.4, dash="dot")),
            row=macd_row, col=1,
        )
        fig.add_hline(y=0, line_color="rgba(148, 163, 184, 0.4)", line_width=1, row=macd_row, col=1)

    fig.update_layout(
        height=total_height,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_forecast_chart(
    df: pd.DataFrame,
    forecast: Dict[str, Any],
    ticker: str,
) -> go.Figure:
    """
    Biểu đồ dự báo xu hướng giá và dải xác suất tin cậy (Monte Carlo Cone)
    """
    fig = go.Figure()
    forecast_df = forecast.get("forecast_df")
    if forecast_df is None or len(forecast_df) == 0:
        return fig

    # Lấy 30 phiên lịch sử gần nhất để nối vào dự báo
    hist_tail = df.tail(30).copy()
    fig.add_trace(
        go.Scatter(
            x=[d.strftime("%d/%m") if hasattr(d, "strftime") else str(d) for d in hist_tail.index],
            y=hist_tail["close"],
            mode="lines+markers",
            name="Giá Lịch Sử",
            line=dict(color="#38bdf8", width=2),
        )
    )

    last_date_str = hist_tail.index[-1].strftime("%d/%m") if hasattr(hist_tail.index[-1], "strftime") else "H.Tại"
    last_price = float(hist_tail["close"].iloc[-1])

    # Nối điểm hiện tại với chuỗi dự báo
    future_x = [last_date_str] + list(forecast_df["date"])
    base_y = [last_price] + list(forecast_df["base_price"])
    bull_y = [last_price] + list(forecast_df["bull_price"])
    bear_y = [last_price] + list(forecast_df["bear_price"])

    # Dải tin cậy Bull / Bear (Vùng xác suất mờ)
    fig.add_trace(
        go.Scatter(
            x=future_x,
            y=bull_y,
            mode="lines",
            name="Kịch bản Lạc quan (+80%)",
            line=dict(color="#10b981", width=1.5, dash="dash"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=future_x,
            y=bear_y,
            mode="lines",
            name="Kịch bản Thận trọng (-20%)",
            line=dict(color="#ef4444", width=1.5, dash="dash"),
            fill="tonexty",
            fillcolor="rgba(56, 189, 248, 0.15)",
        )
    )

    # Đường giá cơ sở kỳ vọng (Base Case)
    fig.add_trace(
        go.Scatter(
            x=future_x,
            y=base_y,
            mode="lines+markers",
            name="Dự báo Cơ sở (Base Case)",
            line=dict(color="#fbbf24", width=3),
            marker=dict(size=6),
        )
    )

    fig.update_layout(
        title=f"Dự Báo Xu Hướng Giá {ticker} ({forecast.get('forecast_days', 7)} Phiên Tới)",
        height=450,
        margin=dict(l=10, r=10, t=50, b=10),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_multi_model_comparison_chart(
    df: pd.DataFrame,
    ml_result: Dict[str, Any],
    selected_models: List[str],
    ticker: str,
    view_mode: str = "forecast_only",
    hist_len: int = 5,
) -> go.Figure:
    """
    Biểu đồ đối chiếu đa chiều nhiều mô hình dự báo trên cùng 1 đồ thị tương tác Plotly:
    - Chế độ "forecast_only" (Mặc định): Toàn bộ chiều ngang 100% của biểu đồ được dành trọn vẹn
      cho các mô hình dự phóng từ điểm xuất phát Hiện tại (T0) đến T+N. Không bị dồn vào một góc nhỏ.
    - Chế độ "with_history": Hiển thị thêm n phiên lịch sử tham chiếu gần nhất (mặc định 5 phiên).
    - Trục Y tự động co giãn (Auto-scale) ôm sát biên độ giá dự báo để phóng to các biến động.
    """
    fig = go.Figure()
    all_models = ml_result.get("models", {})
    future_dates = ml_result.get("future_dates", [])
    if not all_models:
        return fig

    last_y = float(df["close"].iloc[-1])

    if view_mode == "with_history":
        # Kèm n phiên lịch sử gần nhất để làm mốc so sánh
        actual_hist_len = min(max(2, hist_len), len(df))
        hist = df.tail(actual_hist_len).copy()
        hist_x = [f"T-{actual_hist_len - 1 - i} ({d.strftime('%d/%m') if hasattr(d, 'strftime') else str(d)[:5]})" for i, d in enumerate(hist.index)]
        last_x = hist_x[-1]

        fig.add_trace(
            go.Scatter(
                x=hist_x,
                y=hist["close"],
                mode="lines+markers",
                name="Lịch Sử Gần Nhất",
                line=dict(color="#cbd5e1", width=2.5),
                marker=dict(size=6, color="#f8fafc"),
            )
        )
        pred_x = [last_x] + [f"T+{i+1} ({d[:5]})" for i, d in enumerate(future_dates)]
        all_displayed_prices = list(hist["close"].dropna())
    else:
        # MẶC ĐỊNH: Tràn 100% khung màn hình dành riêng cho các mô hình dự báo
        start_x = f"Hiện Tại (T0)"
        pred_x = [start_x] + [f"T+{i+1} ({d[:5]})" for i, d in enumerate(future_dates)]
        all_displayed_prices = [last_y]

        # Điểm mốc giá hiện tại T0
        fig.add_trace(
            go.Scatter(
                x=[start_x],
                y=[last_y],
                mode="markers+text",
                name="Giá Khớp Hiện Tại (T0)",
                text=[f"T0: {last_y:,.2f}"],
                textposition="top center",
                marker=dict(size=12, color="#38bdf8", symbol="diamond"),
                showlegend=True,
            )
        )

    # Vẽ từng mô hình được chọn
    for m_name in selected_models:
        if m_name in all_models:
            m_info = all_models[m_name]
            pred_y = [last_y] + list(m_info["prices"])
            all_displayed_prices.extend(m_info["prices"])
            line_width = 3.5 if "Đồng Thuận" in m_name else 2.5

            custom_vnd = [p * 1000 for p in pred_y]
            fig.add_trace(
                go.Scatter(
                    x=pred_x,
                    y=pred_y,
                    mode="lines+markers",
                    name=f"{m_name} ({m_info['expected_return']:+.2f}%)",
                    customdata=custom_vnd,
                    hovertemplate="<b>" + m_name + "</b><br>Phiên: %{x}<br>Điểm giá: %{y:,.2f} (%{customdata:,.0f} VNĐ)<extra></extra>",
                    line=dict(
                        color=m_info.get("color", "#c084fc"),
                        width=line_width,
                        dash=m_info.get("dash", "solid"),
                    ),
                    marker=dict(size=7),
                )
            )

    # Đường tham chiếu ngang tại mức giá hiện tại T0
    fig.add_hline(
        y=last_y,
        line_dash="dot",
        line_color="#475569",
        line_width=1.5,
        annotation_text=f"Mức Giá Khớp Tham Chiếu (T0): {last_y:,.2f} ({last_y*1000:,.0f} VNĐ)",
        annotation_position="bottom right",
        annotation_font=dict(size=11, color="#334155"),
    )

    # Tính toán Auto-scale trục Y ôm sát biên độ dự báo
    if all_displayed_prices:
        p_min = float(min(all_displayed_prices))
        p_max = float(max(all_displayed_prices))
        span = p_max - p_min
        pad = max(span * 0.18, p_max * 0.015)
        y_range = [round(p_min - pad, 2), round(p_max + pad, 2)]
    else:
        y_range = None

    layout_kwargs = dict(
        title=dict(
            text=f"🌐 Đối Chiếu Đa Chiều Các Mô Hình Dự Báo Xu Hướng Giá ({ticker}) - {len(future_dates)} Phiên Tới",
            x=0.01,
            y=0.98,
        ),
        height=580,
        margin=dict(l=20, r=20, t=65, b=30),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0, 0, 0, 0)",
        ),
        xaxis=dict(
            title="Các Phiên Giao Dịch Dự Báo",
            showgrid=True,
            tickangle=0,
            zeroline=False,
        ),
        yaxis=dict(
            title="Mức Giá Dự Báo (nghìn VNĐ)",
            showgrid=True,
            zeroline=False,
            tickformat=",.2f",
        ),
    )

    if y_range is not None:
        layout_kwargs["yaxis"]["range"] = y_range
        layout_kwargs["yaxis"]["autorange"] = False

    fig.update_layout(**layout_kwargs)
    return fig


# Giữ tên cũ tương thích
create_ml_forecast_chart = create_multi_model_comparison_chart


def create_feature_importance_chart(feature_importance: List[Dict[str, Any]]) -> go.Figure:
    """
    Biểu đồ thanh thể hiện độ quan trọng của các yếu tố chi phối giá
    """
    fig = go.Figure()
    if not feature_importance:
        return fig

    feats = [item["feature"] for item in reversed(feature_importance)]
    weights = [item["importance"] for item in reversed(feature_importance)]

    fig.add_trace(
        go.Bar(
            y=feats,
            x=weights,
            orientation="h",
            marker=dict(
                color=weights,
                colorscale="Viridis",
            ),
            text=[f"{w}%" for w in weights],
            textposition="inside",
        )
    )

    fig.update_layout(
        title="Trọng Số Các Yếu Tố Chi Phối Quyết Định Dự Báo (Feature Importance)",
        height=320,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title="Tỷ lệ đóng góp (%)",
    )
    return fig


def create_market_breadth_card(breadth: Dict[str, Any], vnindex_change: float = 0.0) -> str:
    """
    Hiển thị thanh đo độ rộng thị trường (Tăng / Giảm / Không đổi) và phát hiện bẫy 'Xanh vỏ đỏ lòng'
    """
    adv = int(breadth.get("advances", 0))
    dec = int(breadth.get("declines", 0))
    no_chg = int(breadth.get("no_changes", 0))
    total = max(adv + dec + no_chg, 1)

    pct_adv = (adv / total) * 100
    pct_dec = (dec / total) * 100
    pct_no = (no_chg / total) * 100

    # Kiểm tra bẫy "Xanh vỏ đỏ lòng"
    is_trap = (vnindex_change > 0) and (dec >= adv * 1.25)
    is_healthy_bull = (vnindex_change > 0) and (adv >= dec * 1.2)

    if is_trap:
        status_alert = (
            '<div style="background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; border-radius: 6px; padding: 8px 12px; margin-top: 10px; color: #f87171; font-size: 13px;">'
            '⚠️ <b>CẢNH BÁO: BẪY \'XANH VỎ ĐỎ LÒNG\'!</b> Chỉ số VN-Index tăng điểm chủ yếu do kéo một vài cổ phiếu trụ lớn, trong khi số mã giảm chiếm đa số áp đảo trên toàn thị trường. Nhà đầu tư mới nên thận trọng, không vội đua lệnh mua giá cao!'
            '</div>'
        )
    elif is_healthy_bull:
        status_alert = (
            '<div style="background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; border-radius: 6px; padding: 8px 12px; margin-top: 10px; color: #34d399; font-size: 13px;">'
            '🟢 <b>ĐỘ RỘNG TÍCH CỰC: DÒNG TIỀN LAN TỎA ĐỀU!</b> Số lượng mã tăng giá chiếm ưu thế áp đảo, thị trường tăng điểm trên diện rộng lành mạnh.'
            '</div>'
        )
    else:
        status_alert = (
            '<div style="background: rgba(148, 163, 184, 0.1); border: 1px solid #475569; border-radius: 6px; padding: 8px 12px; margin-top: 10px; color: #cbd5e1; font-size: 13px;">'
            '⚖️ <b>ĐỘ RỘNG CÂN BẰNG:</b> Dòng tiền phân hóa giữa các nhóm ngành, thị trường tìm điểm cân bằng tích lũy.'
            '</div>'
        )

    html = (
        '<div style="background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 16px; margin: 10px 0;">'
        '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">'
        '<span style="font-size: 14px; font-weight: 700; color: #f8fafc;">⚖️ Độ Rộng Thị Trường (Tỷ Lệ Tăng / Giảm)</span>'
        f'<span style="font-size: 12px; color: #94a3b8;">Tổng số: <b>{total} mã</b></span>'
        '</div>'
        '<div style="height: 14px; width: 100%; display: flex; border-radius: 7px; overflow: hidden; background: #334155;">'
        f'<div style="width: {pct_adv:.1f}%; background: #10b981;" title="Tăng: {adv} mã ({pct_adv:.1f}%)"></div>'
        f'<div style="width: {pct_no:.1f}%; background: #f59e0b;" title="Không đổi: {no_chg} mã ({pct_no:.1f}%)"></div>'
        f'<div style="width: {pct_dec:.1f}%; background: #ef4444;" title="Giảm: {dec} mã ({pct_dec:.1f}%)"></div>'
        '</div>'
        '<div style="display: flex; justify-content: space-between; font-size: 12px; margin-top: 6px;">'
        f'<span style="color: #10b981; font-weight: 700;">🟢 Tăng: {adv} ({pct_adv:.1f}%)</span>'
        f'<span style="color: #f59e0b; font-weight: 700;">🟡 Không đổi: {no_chg} ({pct_no:.1f}%)</span>'
        f'<span style="color: #ef4444; font-weight: 700;">🔴 Giảm: {dec} ({pct_dec:.1f}%)</span>'
        '</div>'
        f'{status_alert}'
        '</div>'
    )
    return html


