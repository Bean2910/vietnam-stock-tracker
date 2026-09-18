"""
Module Biểu Đồ Kỹ Thuật (Technical Analysis Charts):
1. create_candlestick_chart: Biểu đồ nến TradingView chuẩn Plotly (Candles + MA + BB + RSI + MACD)
2. create_volume_profile_chart: Biểu đồ phân bổ thanh khoản theo mức giá (Volume Profile & POC)
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
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
            go.Scatter(x=plot_df.index, y=plot_df["BB_Upper"], mode="lines", name="BB Upper", line=dict(color="rgba(156, 163, 175, 0.6)", width=1, dash="dot"), hoverinfo="skip"),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=plot_df.index, y=plot_df["BB_Lower"], mode="lines", name="BB Lower",
                line=dict(color="rgba(156, 163, 175, 0.6)", width=1, dash="dot"),
                fill="tonexty", fillcolor="rgba(156, 163, 175, 0.08)",
                hoverinfo="skip",
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
            go.Scatter(x=plot_df.index, y=plot_df["VOL_SMA20"], mode="lines", name="Vol SMA20", line=dict(color="#6366f1", width=1.2), hoverinfo="skip"),
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
        fig.update_yaxes(range=[0, 100], fixedrange=True, tickvals=[30, 50, 70], row=rsi_row, col=1)

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
        margin=dict(l=65, r=20, t=30, b=35),
        xaxis_rangeslider_visible=False,
        hovermode="x",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        dragmode="pan",
        uirevision=ticker,
        transition=dict(duration=0),
    )
    # Khóa cố định trục Y khi zoom để chỉ zoom trục thời gian X, tắt automargin để cố định lề tuyệt đối (chống lắc)
    fig.update_yaxes(fixedrange=True, automargin=False)
    # Cố định lề X và định dạng ngày đồng nhất chống co giật nhãn trục
    fig.update_xaxes(
        automargin=False,
        tickformat="%d/%m",
        hoverformat="%d/%m/%Y",
        rangebreaks=[dict(bounds=["sat", "mon"])],
    )
    return fig


def create_volume_profile_chart(
    df: pd.DataFrame,
    ticker: str,
    vp_info: Dict[str, Any],
) -> go.Figure:
    """
    Biểu đồ phân bổ thanh khoản theo mức giá (Volume Profile & Point of Control - POC):
    - Cột ngang thể hiện khối lượng giao dịch tích lũy tại từng vùng giá
    - Cột màu Vàng Hổ Phách: Điểm kiểm soát POC (khối lượng trao tay lớn nhất)
    - Vùng màu Xanh Dương: Value Area (70% tổng khối lượng giao dịch)
    - Đường chỉ báo POC, VAH (Value Area High), VAL (Value Area Low) và Mức giá hiện tại
    """
    fig = go.Figure()
    bins_data = vp_info.get("bins_data", [])
    if not bins_data:
        return fig

    prices = [b["price_level"] for b in bins_data]
    volumes = [b["volume"] for b in bins_data]
    colors = []
    hover_texts = []

    poc_p = vp_info.get("poc_price", 0.0)
    vah = vp_info.get("vah", 0.0)
    val = vp_info.get("val", 0.0)
    cur_p = vp_info.get("current_close", 0.0)

    for b in bins_data:
        p = b["price_level"]
        v = b["volume"]
        if b["is_poc"]:
            colors.append("#f59e0b")  # Gold for POC
            tag = "⭐ Point of Control (POC) - Nam châm hút giá"
        elif b["in_value_area"]:
            colors.append("#3b82f6")  # Blue for Value Area
            tag = "Value Area (Vùng thanh khoản 70%)"
        else:
            colors.append("rgba(148, 163, 184, 0.45)")  # Gray outside Value Area
            tag = "Vùng thanh khoản thấp"

        hover_texts.append(
            f"<b>Mức giá:</b> {p:,.2f} ({p*1000:,.0f} VNĐ)<br>"
            f"<b>Khối lượng:</b> {v:,} CP<br>"
            f"<b>Phân loại:</b> {tag}"
        )

    # 1. Cột Volume Profile ngang
    fig.add_trace(
        go.Bar(
            y=prices,
            x=volumes,
            orientation="h",
            marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.1)", width=1)),
            hoverinfo="text",
            hovertext=hover_texts,
            name="Khối lượng tích lũy",
            showlegend=False,
        )
    )

    # 2. Đường kẻ ngang POC
    fig.add_hline(
        y=poc_p,
        line_dash="solid",
        line_color="#f59e0b",
        line_width=2.5,
        annotation_text=f"⭐ POC: {poc_p:,.2f}",
        annotation_position="top right",
        annotation_font=dict(size=12, color="#f59e0b", family="sans-serif"),
    )

    # 3. Đường Value Area High (VAH)
    fig.add_hline(
        y=vah,
        line_dash="dash",
        line_color="#38bdf8",
        line_width=1.5,
        annotation_text=f"VAH: {vah:,.2f}",
        annotation_position="bottom right",
        annotation_font=dict(size=11, color="#38bdf8"),
    )

    # 4. Đường Value Area Low (VAL)
    fig.add_hline(
        y=val,
        line_dash="dash",
        line_color="#ef4444",
        line_width=1.5,
        annotation_text=f"VAL: {val:,.2f}",
        annotation_position="top right",
        annotation_font=dict(size=11, color="#ef4444"),
    )

    # 5. Đường Giá Khớp Hiện Tại
    fig.add_hline(
        y=cur_p,
        line_dash="dash",
        line_color="#38bdf8",
        line_width=2,
        annotation_text=f"Giá hiện tại: {cur_p:,.2f}",
        annotation_position="bottom left",
        annotation_font=dict(size=11, color="#38bdf8"),
    )

    fig.update_layout(
        title=dict(
            text=f"📦 Biểu Đồ Volume Profile & Vùng Giá Kiểm Soát POC - {ticker} (60 Phiên)",
            x=0.01,
            y=0.98,
        ),
        height=520,
        margin=dict(l=65, r=50, t=60, b=40),
        xaxis=dict(
            title="Khối lượng giao dịch tích lũy (Cổ phiếu)",
            showgrid=True,
            tickformat="~s",
        ),
        yaxis=dict(
            title="Mức Giá (nghìn VNĐ)",
            showgrid=True,
            tickformat=",.2f",
            fixedrange=True,
            automargin=False,
        ),
        dragmode="pan",
        uirevision=ticker,
        transition=dict(duration=0),
    )
    return fig
