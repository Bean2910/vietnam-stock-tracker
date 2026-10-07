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
    # 1. Price Overlays (Vẽ trực tiếp trên khung nến giá)
    show_sma: Optional[bool] = None,
    show_sma_short: bool = True,
    show_sma_med: bool = True,
    show_sma200: bool = True,
    show_ema: bool = False,
    show_bb: bool = True,
    show_ichimoku: bool = False,
    show_sar: bool = False,
    show_vwap: bool = False,
    show_ref_line: bool = True,
    ref_price: Optional[float] = None,
    # 2. Sub-panels (Chỉ báo dao động ở các hàng bên dưới)
    show_volume: bool = True,
    show_rsi: bool = True,
    show_macd: bool = True,
    show_stoch: bool = False,
    show_mfi: bool = False,
    show_atr: bool = False,
    show_obv: bool = False,
    # Khung phiên hiển thị
    n_sessions: Optional[int] = None,
) -> go.Figure:
    """
    Tạo biểu đồ kỹ thuật chuyên nghiệp TradingView bằng Plotly với khả năng bật/tắt động
    hàng loạt chỉ báo kỹ thuật theo lựa chọn của người dùng:
    - Overlays trên nến: SMA (10, 20, 50, 100, 200), EMA (9, 21, 50, 200), Bollinger Bands,
      Mây Ichimoku Kinko Hyo, Parabolic SAR, VWAP, Giá tham chiếu.
    - Sub-panels dao động: Volume, RSI (14), MACD (12, 26, 9), Stochastic (14, 3, 3),
      MFI (14), ATR (14), OBV.
    """
    if show_sma is not None:
        if not show_sma:
            show_sma_short = False
            show_sma_med = False

    plot_df = df.tail(n_sessions).copy() if (n_sessions and n_sessions > 0) else df.copy()

    # Danh sách các Sub-panel được người dùng bật
    subpanels = []
    if show_volume and "volume" in plot_df.columns:
        subpanels.append(("Khối lượng (Volume)", "volume"))
    if show_rsi and "RSI14" in plot_df.columns:
        subpanels.append(("Chỉ số RSI (14)", "rsi"))
    if show_macd and "MACD" in plot_df.columns:
        subpanels.append(("Chỉ báo MACD (12, 26, 9)", "macd"))
    if show_stoch and "STOCH_K" in plot_df.columns:
        subpanels.append(("Dao động Stochastic (14, 3, 3)", "stoch"))
    if show_mfi and "MFI14" in plot_df.columns:
        subpanels.append(("Dòng tiền MFI (14)", "mfi"))
    if show_atr and "ATR14" in plot_df.columns:
        subpanels.append(("Biến động ATR (14)", "atr"))
    if show_obv and "OBV" in plot_df.columns:
        subpanels.append(("Khối lượng Cân bằng OBV", "obv"))

    num_subs = len(subpanels)
    total_rows = 1 + num_subs

    # Phân bổ tỷ lệ độ cao màn hình
    if num_subs == 0:
        row_heights = [1.0]
        total_height = 540
    elif num_subs == 1:
        row_heights = [0.72, 0.28]
        total_height = 620
    elif num_subs == 2:
        row_heights = [0.60, 0.20, 0.20]
        total_height = 720
    elif num_subs == 3:
        row_heights = [0.49, 0.17, 0.17, 0.17]
        total_height = 840
    elif num_subs == 4:
        row_heights = [0.40, 0.15, 0.15, 0.15, 0.15]
        total_height = 960
    else:
        main_h = 0.35
        sub_h = (1.0 - main_h) / num_subs
        row_heights = [main_h] + [sub_h] * num_subs
        total_height = 500 + num_subs * 120

    title_main = (
        f"Biểu đồ Kỹ thuật {ticker} ({n_sessions} phiên gần nhất)"
        if (n_sessions and n_sessions > 0 and n_sessions < len(df))
        else f"Biểu đồ Kỹ thuật {ticker}"
    )
    sub_titles = [title_main] + [p[0] for p in subpanels]

    fig = make_subplots(
        rows=total_rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.025,
        row_heights=row_heights,
        subplot_titles=sub_titles,
    )

    # ==================== HÀNG 1: NẾN NHẬT & OVERLAYS ====================
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

    # 2. Các đường SMA Ngắn & Trung hạn
    if show_sma_short:
        if "SMA10" in plot_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["SMA10"],
                    mode="lines",
                    name="SMA 10",
                    line=dict(color="#eab308", width=1.5),
                    hovertemplate="SMA10: %{y:,.2f}<extra></extra>",
                ),
                row=1, col=1,
            )
        if "SMA20" in plot_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["SMA20"],
                    mode="lines",
                    name="SMA 20",
                    line=dict(color="#f59e0b", width=1.8),
                    hovertemplate="SMA20: %{y:,.2f}<extra></extra>",
                ),
                row=1, col=1,
            )

    if show_sma_med:
        if "SMA50" in plot_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["SMA50"],
                    mode="lines",
                    name="SMA 50",
                    line=dict(color="#3b82f6", width=1.8),
                    hovertemplate="SMA50: %{y:,.2f}<extra></extra>",
                ),
                row=1, col=1,
            )
        if "SMA100" in plot_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["SMA100"],
                    mode="lines",
                    name="SMA 100",
                    line=dict(color="#8b5cf6", width=1.6),
                    hovertemplate="SMA100: %{y:,.2f}<extra></extra>",
                ),
                row=1, col=1,
            )

    # 3. SMA 200 (Dài hạn)
    if show_sma200 and "SMA200" in plot_df.columns:
        fig.add_trace(
            go.Scatter(
                x=plot_df.index,
                y=plot_df["SMA200"],
                mode="lines",
                name="SMA 200 (Dài)",
                line=dict(color="#ec4899", width=2.0, dash="solid"),
                hovertemplate="SMA200: %{y:,.2f}<extra></extra>",
            ),
            row=1, col=1,
        )

    # 4. Các đường EMA (Lũy thừa)
    if show_ema:
        if "EMA9" in plot_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["EMA9"],
                    mode="lines",
                    name="EMA 9",
                    line=dict(color="#06b6d4", width=1.5),
                    hovertemplate="EMA9: %{y:,.2f}<extra></extra>",
                ),
                row=1, col=1,
            )
        if "EMA21" in plot_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["EMA21"],
                    mode="lines",
                    name="EMA 21",
                    line=dict(color="#14b8a6", width=1.6),
                    hovertemplate="EMA21: %{y:,.2f}<extra></extra>",
                ),
                row=1, col=1,
            )
        if "EMA50" in plot_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["EMA50"],
                    mode="lines",
                    name="EMA 50",
                    line=dict(color="#6366f1", width=1.8),
                    hovertemplate="EMA50: %{y:,.2f}<extra></extra>",
                ),
                row=1, col=1,
            )

    # 5. Dải Bollinger Bands
    if show_bb and "BB_Upper" in plot_df.columns and "BB_Lower" in plot_df.columns:
        fig.add_trace(
            go.Scatter(
                x=plot_df.index,
                y=plot_df["BB_Upper"],
                mode="lines",
                name="BB Upper",
                line=dict(color="rgba(156, 163, 175, 0.6)", width=1, dash="dot"),
                hoverinfo="skip",
            ),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=plot_df.index,
                y=plot_df["BB_Lower"],
                mode="lines",
                name="BB Lower",
                line=dict(color="rgba(156, 163, 175, 0.6)", width=1, dash="dot"),
                fill="tonexty",
                fillcolor="rgba(156, 163, 175, 0.08)",
                hoverinfo="skip",
            ),
            row=1, col=1,
        )

    # 6. Mây Ichimoku Kinko Hyo
    if show_ichimoku and "ICH_Tenkan" in plot_df.columns:
        fig.add_trace(
            go.Scatter(
                x=plot_df.index,
                y=plot_df["ICH_Tenkan"],
                mode="lines",
                name="Tenkan (Chuyển đổi)",
                line=dict(color="#ef4444", width=1.3),
                hovertemplate="Tenkan: %{y:,.2f}<extra></extra>",
            ),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=plot_df.index,
                y=plot_df["ICH_Kijun"],
                mode="lines",
                name="Kijun (Tiêu chuẩn)",
                line=dict(color="#2563eb", width=1.5),
                hovertemplate="Kijun: %{y:,.2f}<extra></extra>",
            ),
            row=1, col=1,
        )
        if "ICH_SpanA" in plot_df.columns and "ICH_SpanB" in plot_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["ICH_SpanA"],
                    mode="lines",
                    name="Span A",
                    line=dict(color="rgba(16, 185, 129, 0.6)", width=1, dash="dot"),
                    hoverinfo="skip",
                ),
                row=1, col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["ICH_SpanB"],
                    mode="lines",
                    name="Mây Kumo (Span B)",
                    line=dict(color="rgba(239, 68, 68, 0.6)", width=1, dash="dot"),
                    fill="tonexty",
                    fillcolor="rgba(16, 185, 129, 0.07)",
                    hoverinfo="skip",
                ),
                row=1, col=1,
            )

    # 7. Parabolic SAR
    if show_sar and "SAR" in plot_df.columns:
        fig.add_trace(
            go.Scatter(
                x=plot_df.index,
                y=plot_df["SAR"],
                mode="markers",
                name="Parabolic SAR",
                marker=dict(symbol="circle", size=4, color="#a855f7"),
                hovertemplate="SAR: %{y:,.2f}<extra></extra>",
            ),
            row=1, col=1,
        )

    # 8. VWAP
    if show_vwap and "VWAP" in plot_df.columns:
        fig.add_trace(
            go.Scatter(
                x=plot_df.index,
                y=plot_df["VWAP"],
                mode="lines",
                name="VWAP",
                line=dict(color="#10b981", width=1.6, dash="dashdot"),
                hovertemplate="VWAP: %{y:,.2f}<extra></extra>",
            ),
            row=1, col=1,
        )

    # 9. Đường giá tham chiếu ngang
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

    # ==================== CÁC SUB-PANEL DAO ĐỘNG DƯỚI ====================
    bar_width_ms = 51840000 if isinstance(plot_df.index, pd.DatetimeIndex) else None

    for idx, (p_title, p_id) in enumerate(subpanels, start=2):
        if p_id == "volume":
            colors = ["#10b981" if c >= o else "#ef4444" for c, o in zip(plot_df["close"], plot_df["open"])]
            fig.add_trace(
                go.Bar(
                    x=plot_df.index,
                    y=plot_df["volume"],
                    name="Volume",
                    marker_color=colors,
                    width=bar_width_ms,
                    showlegend=False,
                ),
                row=idx, col=1,
            )
            if "VOL_SMA20" in plot_df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=plot_df.index,
                        y=plot_df["VOL_SMA20"],
                        mode="lines",
                        name="Vol SMA20",
                        line=dict(color="#6366f1", width=1.4),
                        hoverinfo="skip",
                    ),
                    row=idx, col=1,
                )
            # Tự động tính thang đo Y cho Volume ôm sát khối lượng thực tế trong phiên (Auto-Fit Y)
            vol_max = float(plot_df["volume"].max()) if "volume" in plot_df.columns and len(plot_df) > 0 else 1000
            vol_range = [0, vol_max * 1.15] if vol_max > 0 else None
            fig.update_yaxes(range=vol_range, fixedrange=False, automargin=False, row=idx, col=1)

        elif p_id == "rsi":
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["RSI14"],
                    mode="lines",
                    name="RSI (14)",
                    line=dict(color="#8b5cf6", width=1.8),
                    hovertemplate="RSI: %{y:,.1f}<extra></extra>",
                ),
                row=idx, col=1,
            )
            fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", line_width=1, row=idx, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="#10b981", line_width=1, row=idx, col=1)
            fig.add_hline(y=50, line_dash="dot", line_color="rgba(148, 163, 184, 0.4)", line_width=1, row=idx, col=1)
            fig.update_yaxes(range=[0, 100], fixedrange=True, automargin=False, tickvals=[30, 50, 70], row=idx, col=1)

        elif p_id == "macd":
            hist_colors = ["#10b981" if float(v) >= 0 else "#ef4444" for v in plot_df.get("MACD_Hist", [])]
            fig.add_trace(
                go.Bar(
                    x=plot_df.index,
                    y=plot_df["MACD_Hist"],
                    name="Histogram",
                    marker_color=hist_colors,
                    width=bar_width_ms,
                    showlegend=False,
                ),
                row=idx, col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["MACD"],
                    mode="lines",
                    name="MACD",
                    line=dict(color="#38bdf8", width=1.6),
                    hovertemplate="MACD: %{y:,.2f}<extra></extra>",
                ),
                row=idx, col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["MACD_Signal"],
                    mode="lines",
                    name="Signal",
                    line=dict(color="#f59e0b", width=1.4, dash="dot"),
                    hovertemplate="Signal: %{y:,.2f}<extra></extra>",
                ),
                row=idx, col=1,
            )
            fig.add_hline(y=0, line_color="rgba(148, 163, 184, 0.4)", line_width=1, row=idx, col=1)

            # Tự động tính thang đo MACD ôm sát giá trị thực tế của các phiên hiển thị (Auto-Fit Y)
            m_vals = []
            if "MACD" in plot_df.columns:
                m_vals.extend([plot_df["MACD"].min(), plot_df["MACD"].max()])
            if "MACD_Signal" in plot_df.columns:
                m_vals.extend([plot_df["MACD_Signal"].min(), plot_df["MACD_Signal"].max()])
            if "MACD_Hist" in plot_df.columns:
                m_vals.extend([plot_df["MACD_Hist"].min(), plot_df["MACD_Hist"].max()])
            m_valid = [float(v) for v in m_vals if pd.notnull(v) and np.isfinite(v)]
            if m_valid:
                m_min = min(m_valid)
                m_max = max(m_valid)
                m_pad = max((m_max - m_min) * 0.12, 0.05)
                fig.update_yaxes(range=[m_min - m_pad, m_max + m_pad], fixedrange=False, automargin=False, row=idx, col=1)
            else:
                fig.update_yaxes(fixedrange=False, automargin=False, row=idx, col=1)

        elif p_id == "stoch":
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["STOCH_K"],
                    mode="lines",
                    name="Stoch %K (14)",
                    line=dict(color="#06b6d4", width=1.6),
                    hovertemplate="%%K: %{y:,.1f}<extra></extra>",
                ),
                row=idx, col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["STOCH_D"],
                    mode="lines",
                    name="Stoch %D (3)",
                    line=dict(color="#f59e0b", width=1.4, dash="dot"),
                    hovertemplate="%%D: %{y:,.1f}<extra></extra>",
                ),
                row=idx, col=1,
            )
            fig.add_hline(y=80, line_dash="dash", line_color="#ef4444", line_width=1, row=idx, col=1)
            fig.add_hline(y=20, line_dash="dash", line_color="#10b981", line_width=1, row=idx, col=1)
            fig.update_yaxes(range=[0, 100], fixedrange=True, automargin=False, tickvals=[20, 50, 80], row=idx, col=1)

        elif p_id == "mfi":
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["MFI14"],
                    mode="lines",
                    name="MFI (14)",
                    line=dict(color="#10b981", width=1.8),
                    hovertemplate="MFI: %{y:,.1f}<extra></extra>",
                ),
                row=idx, col=1,
            )
            fig.add_hline(y=80, line_dash="dash", line_color="#ef4444", line_width=1, row=idx, col=1)
            fig.add_hline(y=20, line_dash="dash", line_color="#10b981", line_width=1, row=idx, col=1)
            fig.add_hline(y=50, line_dash="dot", line_color="rgba(148, 163, 184, 0.4)", line_width=1, row=idx, col=1)
            fig.update_yaxes(range=[0, 100], fixedrange=True, automargin=False, tickvals=[20, 50, 80], row=idx, col=1)

        elif p_id == "atr":
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["ATR14"],
                    mode="lines",
                    name="ATR (14)",
                    line=dict(color="#ec4899", width=1.6),
                    hovertemplate="ATR: %{y:,.2f}<extra></extra>",
                ),
                row=idx, col=1,
            )
            fig.update_yaxes(fixedrange=True, automargin=False, row=idx, col=1)

        elif p_id == "obv":
            fig.add_trace(
                go.Scatter(
                    x=plot_df.index,
                    y=plot_df["OBV"],
                    mode="lines",
                    name="OBV",
                    line=dict(color="#38bdf8", width=1.6),
                    hovertemplate="OBV: %{y:,.0f}<extra></extra>",
                ),
                row=idx, col=1,
            )
            fig.update_yaxes(fixedrange=True, automargin=False, row=idx, col=1)

    # Tính toán dải giá tối ưu (Auto-Fit Y) ôm sát các cây nến và đường MA ngắn/trung hạn
    low_min = float(plot_df["low"].min()) if "low" in plot_df.columns and len(plot_df) > 0 else 0.0
    high_max = float(plot_df["high"].max()) if "high" in plot_df.columns and len(plot_df) > 0 else 100.0

    active_overlay_values = [low_min, high_max]
    if show_sma_short and "SMA20" in plot_df.columns:
        active_overlay_values.extend([plot_df["SMA20"].min(), plot_df["SMA20"].max()])
    if show_sma_med and "SMA50" in plot_df.columns:
        active_overlay_values.extend([plot_df["SMA50"].min(), plot_df["SMA50"].max()])
    if show_bb and "BB_Upper" in plot_df.columns and "BB_Lower" in plot_df.columns:
        active_overlay_values.extend([plot_df["BB_Upper"].max(), plot_df["BB_Lower"].min()])

    valid_vals = [float(v) for v in active_overlay_values if pd.notnull(v) and np.isfinite(v) and v > 0]
    if valid_vals:
        calc_min = min(valid_vals)
        calc_max = max(valid_vals)
        pad = max((calc_max - calc_min) * 0.06, 0.15)
        price_range = [calc_min - pad, calc_max + pad]
    else:
        price_range = None

    # Layout tổng thể
    fig.update_layout(
        height=total_height,
        margin=dict(l=65, r=20, t=30, b=35),
        xaxis_rangeslider_visible=False,
        hovermode="x",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        dragmode="pan",
        uirevision=ticker,
        bargap=0.25,
        transition=dict(duration=0),
    )
    # Tự động co giãn trục Y hàng 1 ôm sát nến (Auto-Fit Y) và mở khóa fixedrange để kéo dãn chiều cao
    if price_range:
        fig.update_yaxes(range=price_range, fixedrange=False, automargin=False, row=1, col=1)
    else:
        fig.update_yaxes(fixedrange=False, automargin=False, row=1, col=1)

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


def render_tradingview_widget(ticker: str, height: int = 620):
    """
    Nhúng trực tiếp biểu đồ TradingView chuẩn quốc tế (chuẩn 100% như trên ứng dụng điện thoại VPS / TCBS).
    Tự động hỗ trợ:
    - Auto-Scale Y ([A] tự động co giãn chiều cao nến ôm trọn khung nhìn khi phóng to / thu nhỏ)
    - Đầy đủ công cụ vẽ, chỉ báo, thước đo kỹ thuật
    - Chế độ nến to cao rõ nét chuẩn xác theo thời gian thực
    """
    import json
    import streamlit as st
    from src.ui.cache import HNX_TICKERS, UPCOM_TICKERS
    sym = ticker.strip().upper()

    # Nhận diện sàn giao dịch (HOSE, HNX, UPCOM) để TradingView tìm đúng mã cổ phiếu Việt Nam
    if sym in HNX_TICKERS:
        exchange_sym = f"HNX:{sym}"
    elif sym in UPCOM_TICKERS:
        exchange_sym = f"UPCOM:{sym}"
    else:
        exchange_sym = f"HOSE:{sym}"

    tv_config = {
        "width": "100%",
        "height": "100%",
        "symbol": exchange_sym,
        "interval": "D",
        "timezone": "Asia/Ho_Chi_Minh",
        "colorTheme": "dark",
        "style": "1",
        "locale": "vi",
        "enable_publishing": False,
        "allow_symbol_change": True,
        "calendar": False,
        "support_host": "https://www.tradingview.com",
    }
    cfg_json = json.dumps(tv_config, ensure_ascii=False)

    tv_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      background-color: #0f172a;
      overflow: hidden;
    }}
    .tradingview-widget-container {{
      width: 100%;
      height: 100%;
      min-height: {height}px;
    }}
    .tradingview-widget-container__widget {{
      width: 100%;
      height: 100%;
      min-height: {height}px;
    }}
  </style>
</head>
<body>
  <div class="tradingview-widget-container">
    <div class="tradingview-widget-container__widget"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
    {cfg_json}
    </script>
  </div>
</body>
</html>"""
    if hasattr(st, "iframe"):
        st.iframe(tv_html, height=height + 20, width="stretch")
    else:
        import streamlit.components.v1 as components
        components.html(tv_html, height=height + 20)


def render_lightweight_tv_chart(
    df: pd.DataFrame,
    ticker: str,
    # 1. Overlays trên nến
    show_sma: bool = None,
    show_sma_short: bool = True,
    show_sma_med: bool = True,
    show_sma200: bool = True,
    show_ema: bool = False,
    show_bb: bool = True,
    show_ichi: bool = False,
    show_sar: bool = False,
    show_vwap: bool = False,
    show_ref_line: bool = True,
    ref_price: float = None,
    # 2. Sub-panels dao động bên dưới
    show_vol: bool = True,
    show_rsi: bool = True,
    show_macd: bool = True,
    show_stoch: bool = False,
    show_mfi: bool = False,
    show_atr: bool = False,
    show_obv: bool = False,
    height: int = 500,
):
    """
    Biểu đồ kỹ thuật chạy trực tiếp 100% trên máy nội bộ sử dụng TradingView Lightweight Charts:
    - Sử dụng công nghệ đồ họa Canvas của chính TradingView (Open-Source).
    - Dùng 100% dữ liệu nến thật từ VPS trên máy người dùng, KHÔNG bị HOSE chặn bản quyền.
    - Hỗ trợ đầy đủ bộ chỉ báo kỹ thuật chuyên nghiệp:
      * Overlays: SMA (10, 20, 50, 100, 200), EMA (9, 21, 50, 200), Bollinger Bands, Ichimoku (Tenkan/Kijun/Span A/B), Parabolic SAR, VWAP, Giá Tham Chiếu.
      * Sub-panels đồng bộ 100%: Volume (kèm Vol SMA20), RSI (14) kèm mốc 70/30/50, MACD (12, 26, 9) kèm Histogram & Signal,
        Stochastic (14, 3) kèm 80/20, Dòng tiền MFI (14), Độ biến động ATR (14), Khối lượng cân bằng OBV.
      * Tự động co giãn trục giá Y (Auto-Scale Y), kéo thả trục giá Y tùy thích, lăn chuột zoom 60 FPS.
    """
    import json
    import streamlit as st
    from pathlib import Path

    if show_sma is not None:
        show_sma_short = show_sma
        show_sma_med = show_sma
        show_sma200 = show_sma

    # 1. Trích xuất nến, volume và toàn bộ các chỉ báo kỹ thuật
    candles = []
    volumes = []
    vol_ma20 = []
    sma10, sma20, sma50, sma100, sma200 = [], [], [], [], []
    ema9, ema21, ema50, ema200 = [], [], [], []
    bb_up, bb_mid, bb_low = [], [], []
    ichi_tenkan, ichi_kijun, ichi_spana, ichi_spanb = [], [], [], []
    sar_pts = []
    vwap_pts = []
    rsi_pts = []
    macd_pts, signal_pts, hist_pts = [], [], []
    stoch_k, stoch_d = [], []
    mfi_pts = []
    atr_pts = []
    obv_pts = []

    sorted_df = df.sort_index().copy()
    for idx, row in sorted_df.iterrows():
        t_str = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)[:10]
        c_open = float(row.get('open', 0))
        c_high = float(row.get('high', 0))
        c_low = float(row.get('low', 0))
        c_close = float(row.get('close', 0))
        c_vol = float(row.get('volume', 0))

        if c_open > 0 and c_close > 0 and c_high >= c_low:
            candles.append({
                'time': t_str,
                'open': round(c_open, 2),
                'high': round(c_high, 2),
                'low': round(c_low, 2),
                'close': round(c_close, 2)
            })
            if show_vol:
                v_color = 'rgba(34, 197, 94, 0.55)' if c_close >= c_open else 'rgba(239, 68, 68, 0.55)'
                volumes.append({'time': t_str, 'value': c_vol, 'color': v_color})
                if pd.notnull(row.get('VOL_SMA20')):
                    vol_ma20.append({'time': t_str, 'value': round(float(row['VOL_SMA20']), 0)})

            # Overlays: SMA
            if show_sma_short:
                if pd.notnull(row.get('SMA10')):
                    sma10.append({'time': t_str, 'value': round(float(row['SMA10']), 2)})
                if pd.notnull(row.get('SMA20')):
                    sma20.append({'time': t_str, 'value': round(float(row['SMA20']), 2)})
            if show_sma_med:
                if pd.notnull(row.get('SMA50')):
                    sma50.append({'time': t_str, 'value': round(float(row['SMA50']), 2)})
                if pd.notnull(row.get('SMA100')):
                    sma100.append({'time': t_str, 'value': round(float(row['SMA100']), 2)})
            if show_sma200 and pd.notnull(row.get('SMA200')):
                sma200.append({'time': t_str, 'value': round(float(row['SMA200']), 2)})

            # Overlays: EMA
            if show_ema:
                if pd.notnull(row.get('EMA9')):
                    ema9.append({'time': t_str, 'value': round(float(row['EMA9']), 2)})
                if pd.notnull(row.get('EMA21')):
                    ema21.append({'time': t_str, 'value': round(float(row['EMA21']), 2)})
                if pd.notnull(row.get('EMA50')):
                    ema50.append({'time': t_str, 'value': round(float(row['EMA50']), 2)})
                if pd.notnull(row.get('EMA200')):
                    ema200.append({'time': t_str, 'value': round(float(row['EMA200']), 2)})

            # Overlays: Bollinger Bands
            if show_bb:
                if pd.notnull(row.get('BB_Upper')):
                    bb_up.append({'time': t_str, 'value': round(float(row['BB_Upper']), 2)})
                if pd.notnull(row.get('BB_Middle')):
                    bb_mid.append({'time': t_str, 'value': round(float(row['BB_Middle']), 2)})
                if pd.notnull(row.get('BB_Lower')):
                    bb_low.append({'time': t_str, 'value': round(float(row['BB_Lower']), 2)})

            # Overlays: Ichimoku
            if show_ichi:
                if pd.notnull(row.get('ICH_Tenkan')):
                    ichi_tenkan.append({'time': t_str, 'value': round(float(row['ICH_Tenkan']), 2)})
                if pd.notnull(row.get('ICH_Kijun')):
                    ichi_kijun.append({'time': t_str, 'value': round(float(row['ICH_Kijun']), 2)})
                if pd.notnull(row.get('ICH_SpanA')):
                    ichi_spana.append({'time': t_str, 'value': round(float(row['ICH_SpanA']), 2)})
                if pd.notnull(row.get('ICH_SpanB')):
                    ichi_spanb.append({'time': t_str, 'value': round(float(row['ICH_SpanB']), 2)})

            # Overlays: Parabolic SAR
            if show_sar and pd.notnull(row.get('SAR')):
                sar_pts.append({'time': t_str, 'value': round(float(row['SAR']), 2)})

            # Overlays: VWAP
            if show_vwap and pd.notnull(row.get('VWAP')):
                vwap_pts.append({'time': t_str, 'value': round(float(row['VWAP']), 2)})

            # Sub-panel: RSI
            if show_rsi and pd.notnull(row.get('RSI14')):
                rsi_pts.append({'time': t_str, 'value': round(float(row['RSI14']), 2)})

            # Sub-panel: MACD
            if show_macd:
                if pd.notnull(row.get('MACD')):
                    macd_pts.append({'time': t_str, 'value': round(float(row['MACD']), 2)})
                if pd.notnull(row.get('MACD_Signal')):
                    signal_pts.append({'time': t_str, 'value': round(float(row['MACD_Signal']), 2)})
                if pd.notnull(row.get('MACD_Hist')):
                    h_val = round(float(row['MACD_Hist']), 2)
                    h_col = 'rgba(34, 197, 94, 0.7)' if h_val >= 0 else 'rgba(239, 68, 68, 0.7)'
                    hist_pts.append({'time': t_str, 'value': h_val, 'color': h_col})

            # Sub-panel: Stochastic
            if show_stoch:
                if pd.notnull(row.get('STOCH_K')):
                    stoch_k.append({'time': t_str, 'value': round(float(row['STOCH_K']), 2)})
                if pd.notnull(row.get('STOCH_D')):
                    stoch_d.append({'time': t_str, 'value': round(float(row['STOCH_D']), 2)})

            # Sub-panel: MFI
            if show_mfi and pd.notnull(row.get('MFI14')):
                mfi_pts.append({'time': t_str, 'value': round(float(row['MFI14']), 2)})

            # Sub-panel: ATR
            if show_atr and pd.notnull(row.get('ATR14')):
                atr_pts.append({'time': t_str, 'value': round(float(row['ATR14']), 2)})

            # Sub-panel: OBV
            if show_obv and pd.notnull(row.get('OBV')):
                obv_pts.append({'time': t_str, 'value': round(float(row['OBV']), 0)})

    # Tính toán chiều cao các pane
    main_h = height
    rsi_h = 130 if show_rsi else 0
    macd_h = 130 if show_macd else 0
    stoch_h = 130 if show_stoch else 0
    mfi_h = 130 if show_mfi else 0
    atr_h = 120 if show_atr else 0
    obv_h = 120 if show_obv else 0
    total_h = main_h + rsi_h + macd_h + stoch_h + mfi_h + atr_h + obv_h

    # Đọc thư viện JS cục bộ đã lưu đệm hoặc dùng CDN
    js_lib_path = Path(__file__).parent.parent / "assets" / "lightweight-charts.js"
    if js_lib_path.exists():
        try:
            lib_js = js_lib_path.read_text(encoding="utf-8")
            script_tag = f"<script>{lib_js}</script>"
        except Exception:
            script_tag = '<script src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>'
    else:
        script_tag = '<script src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>'

    # Xây dựng các thẻ nhãn chú thích
    legend_badges = [
        f'<div class="legend-item" style="color: #f8fafc; font-weight: 700; font-size: 14px;">{ticker} · 1D</div>'
    ]
    if show_sma_short:
        legend_badges.append('<div class="legend-item" style="color: #eab308;"><span class="badge" style="background:#eab308;"></span> SMA10</div>')
        legend_badges.append('<div class="legend-item" style="color: #f97316;"><span class="badge" style="background:#f97316;"></span> SMA20</div>')
    if show_sma_med:
        legend_badges.append('<div class="legend-item" style="color: #38bdf8;"><span class="badge" style="background:#38bdf8;"></span> SMA50</div>')
        legend_badges.append('<div class="legend-item" style="color: #a855f7;"><span class="badge" style="background:#a855f7;"></span> SMA100</div>')
    if show_sma200:
        legend_badges.append('<div class="legend-item" style="color: #ec4899;"><span class="badge" style="background:#ec4899;"></span> SMA200</div>')
    if show_ema:
        legend_badges.append('<div class="legend-item" style="color: #10b981;"><span class="badge" style="background:#10b981;"></span> EMA9</div>')
        legend_badges.append('<div class="legend-item" style="color: #fbbf24;"><span class="badge" style="background:#fbbf24;"></span> EMA21</div>')
        legend_badges.append('<div class="legend-item" style="color: #818cf8;"><span class="badge" style="background:#818cf8;"></span> EMA50</div>')
        legend_badges.append('<div class="legend-item" style="color: #f43f5e;"><span class="badge" style="background:#f43f5e;"></span> EMA200</div>')
    if show_bb:
        legend_badges.append('<div class="legend-item" style="color: #06b6d4;"><span class="badge" style="background:#06b6d4;"></span> Bollinger Bands</div>')
    if show_ichi:
        legend_badges.append('<div class="legend-item" style="color: #ef4444;"><span class="badge" style="background:#ef4444;"></span> Tenkan</div>')
        legend_badges.append('<div class="legend-item" style="color: #3b82f6;"><span class="badge" style="background:#3b82f6;"></span> Kijun</div>')
        legend_badges.append('<div class="legend-item" style="color: #10b981;"><span class="badge" style="background:#10b981;"></span> Span A/B</div>')
    if show_sar:
        legend_badges.append('<div class="legend-item" style="color: #a855f7;"><span class="badge" style="background:#a855f7;"></span> SAR</div>')
    if show_vwap:
        legend_badges.append('<div class="legend-item" style="color: #eab308;"><span class="badge" style="background:#eab308;"></span> VWAP</div>')
    if show_ref_line and ref_price and ref_price > 0:
        legend_badges.append(f'<div class="legend-item" style="color: #facc15;"><span class="badge" style="background:#facc15;"></span> TC: {ref_price:,.2f}</div>')

    legend_html = "".join(legend_badges)

    rsi_pane_html = f'<div id="tv_rsi_container" style="width:100%;height:{rsi_h}px;border-top:1px solid #334155;position:relative;"><div style="position:absolute;top:6px;left:14px;color:#8b5cf6;font-size:12px;font-weight:600;z-index:10;">RSI (14) · Quá mua 70 / Quá bán 30</div></div>' if show_rsi else ""
    macd_pane_html = f'<div id="tv_macd_container" style="width:100%;height:{macd_h}px;border-top:1px solid #334155;position:relative;"><div style="position:absolute;top:6px;left:14px;color:#38bdf8;font-size:12px;font-weight:600;z-index:10;">MACD (12, 26, 9) · Histogram & Signal</div></div>' if show_macd else ""
    stoch_pane_html = f'<div id="tv_stoch_container" style="width:100%;height:{stoch_h}px;border-top:1px solid #334155;position:relative;"><div style="position:absolute;top:6px;left:14px;color:#06b6d4;font-size:12px;font-weight:600;z-index:10;">Stochastic (14, 3) · %K / %D · [20 - 80]</div></div>' if show_stoch else ""
    mfi_pane_html = f'<div id="tv_mfi_container" style="width:100%;height:{mfi_h}px;border-top:1px solid #334155;position:relative;"><div style="position:absolute;top:6px;left:14px;color:#10b981;font-size:12px;font-weight:600;z-index:10;">Dòng Tiền MFI (14) · [20 - 80]</div></div>' if show_mfi else ""
    atr_pane_html = f'<div id="tv_atr_container" style="width:100%;height:{atr_h}px;border-top:1px solid #334155;position:relative;"><div style="position:absolute;top:6px;left:14px;color:#ec4899;font-size:12px;font-weight:600;z-index:10;">Độ Biến Động ATR (14)</div></div>' if show_atr else ""
    obv_pane_html = f'<div id="tv_obv_container" style="width:100%;height:{obv_h}px;border-top:1px solid #334155;position:relative;"><div style="position:absolute;top:6px;left:14px;color:#38bdf8;font-size:12px;font-weight:600;z-index:10;">Khối Lượng Cân Bằng OBV</div></div>' if show_obv else ""

    lw_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    * {{ box-sizing: border-box; }}
    html, body {{
      margin: 0; padding: 0; width: 100%; height: 100%;
      background-color: #0f172a; overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    #chart_wrapper {{
      position: relative;
      width: 100%;
      height: {total_h}px;
      background: #0f172a;
      display: flex;
      flex-direction: column;
    }}
    #tv_main_container {{
      width: 100%;
      height: {main_h}px;
      position: relative;
    }}
    .legend-overlay {{
      position: absolute;
      top: 10px;
      left: 14px;
      z-index: 20;
      pointer-events: none;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
      font-size: 12px;
      font-weight: 500;
      background: rgba(15, 23, 42, 0.75);
      padding: 4px 8px;
      border-radius: 4px;
      border: 1px solid rgba(51, 65, 85, 0.5);
      max-width: 90%;
    }}
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 4px;
      white-space: nowrap;
    }}
    .badge {{
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }}
    .hint-overlay {{
      position: absolute;
      bottom: 24px;
      left: 14px;
      z-index: 20;
      pointer-events: none;
      font-size: 11px;
      color: #64748b;
    }}
  </style>
  {script_tag}
</head>
<body>
  <div id="chart_wrapper">
    <div id="tv_main_container">
      <div class="legend-overlay">
        {legend_html}
      </div>
      <div class="hint-overlay">
        💡 Lăn chuột phóng to | Kéo trục giá Y bên phải để dãn chiều cao nến | Nhấp đúp trục giá để Reset
      </div>
      <div id="tv_main_chart" style="width:100%;height:100%;"></div>
    </div>
    {rsi_pane_html}
    {macd_pane_html}
    {stoch_pane_html}
    {mfi_pane_html}
    {atr_pane_html}
    {obv_pane_html}
  </div>

  <script>
    const candleData = {json.dumps(candles)};
    const commonLayout = {{
      background: {{ type: 'solid', color: '#0f172a' }},
      textColor: '#94a3b8',
      fontSize: 12,
    }};
    const commonGrid = {{
      vertLines: {{ color: 'rgba(51, 65, 85, 0.4)' }},
      horzLines: {{ color: 'rgba(51, 65, 85, 0.4)' }},
    }};

    // ================= 1. BIỂU ĐỒ CHÍNH (NẾN & OVERLAYS) =================
    const mainContainer = document.getElementById('tv_main_chart');
    const mainChart = LightweightCharts.createChart(mainContainer, {{
      width: mainContainer.clientWidth,
      height: {main_h},
      layout: commonLayout,
      grid: commonGrid,
      crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
      rightPriceScale: {{
        borderColor: '#334155',
        autoScale: true,
        scaleMargins: {{ top: 0.10, bottom: {'0.22' if show_vol else '0.10'} }},
      }},
      timeScale: {{
        borderColor: '#334155',
        timeVisible: true,
        secondsVisible: false,
        barSpacing: 14,
        minBarSpacing: 4,
        visible: false,
      }},
      watermark: {{
        visible: true,
        fontSize: 60,
        horzAlign: 'center',
        vertAlign: 'center',
        color: 'rgba(51, 65, 85, 0.20)',
        text: '{ticker}',
      }},
    }});

    // Nến Nhật
    const candleSeries = mainChart.addCandlestickSeries({{
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderDownColor: '#ef4444',
      borderUpColor: '#22c55e',
      wickDownColor: '#ef4444',
      wickUpColor: '#22c55e',
    }});
    candleSeries.setData(candleData);

    // Đường giá tham chiếu
    {'candleSeries.createPriceLine({ price: ' + str(round(ref_price, 2)) + ', color: "#facc15", lineWidth: 1.5, lineStyle: 2, title: "TC: ' + str(round(ref_price, 2)) + '" });' if (show_ref_line and ref_price and ref_price > 0) else ''}

    // Cột Khối lượng Volume & Đường Vol SMA20
    {'const volSeries = mainChart.addHistogramSeries({ priceFormat: { type: "volume" }, priceScaleId: "", scaleMargins: { top: 0.80, bottom: 0 } }); volSeries.setData(' + json.dumps(volumes) + ');' if show_vol and volumes else ''}
    {'const volMaSeries = mainChart.addLineSeries({ color: "rgba(245, 158, 11, 0.8)", lineWidth: 1.2, lineStyle: 2, priceFormat: { type: "volume" }, priceScaleId: "", scaleMargins: { top: 0.80, bottom: 0 } }); volMaSeries.setData(' + json.dumps(vol_ma20) + ');' if show_vol and vol_ma20 else ''}

    // Overlays: SMA
    {'const s10 = mainChart.addLineSeries({ color: "#eab308", lineWidth: 1.5, priceLineVisible: false }); s10.setData(' + json.dumps(sma10) + ');' if show_sma_short and sma10 else ''}
    {'const s20 = mainChart.addLineSeries({ color: "#f97316", lineWidth: 2, priceLineVisible: false }); s20.setData(' + json.dumps(sma20) + ');' if show_sma_short and sma20 else ''}
    {'const s50 = mainChart.addLineSeries({ color: "#38bdf8", lineWidth: 2, priceLineVisible: false }); s50.setData(' + json.dumps(sma50) + ');' if show_sma_med and sma50 else ''}
    {'const s100 = mainChart.addLineSeries({ color: "#a855f7", lineWidth: 1.5, priceLineVisible: false }); s100.setData(' + json.dumps(sma100) + ');' if show_sma_med and sma100 else ''}
    {'const s200 = mainChart.addLineSeries({ color: "#ec4899", lineWidth: 2.5, priceLineVisible: false }); s200.setData(' + json.dumps(sma200) + ');' if show_sma200 and sma200 else ''}

    // Overlays: EMA
    {'const e9 = mainChart.addLineSeries({ color: "#10b981", lineWidth: 1.5, priceLineVisible: false }); e9.setData(' + json.dumps(ema9) + ');' if show_ema and ema9 else ''}
    {'const e21 = mainChart.addLineSeries({ color: "#fbbf24", lineWidth: 1.8, priceLineVisible: false }); e21.setData(' + json.dumps(ema21) + ');' if show_ema and ema21 else ''}
    {'const e50 = mainChart.addLineSeries({ color: "#818cf8", lineWidth: 2, priceLineVisible: false }); e50.setData(' + json.dumps(ema50) + ');' if show_ema and ema50 else ''}
    {'const e200 = mainChart.addLineSeries({ color: "#f43f5e", lineWidth: 2.5, priceLineVisible: false }); e200.setData(' + json.dumps(ema200) + ');' if show_ema and ema200 else ''}

    // Overlays: Bollinger Bands
    {'const bbU = mainChart.addLineSeries({ color: "#06b6d4", lineWidth: 1.5, lineStyle: 2, priceLineVisible: false }); bbU.setData(' + json.dumps(bb_up) + ');' if show_bb and bb_up else ''}
    {'const bbM = mainChart.addLineSeries({ color: "rgba(148, 163, 184, 0.7)", lineWidth: 1, lineStyle: 3, priceLineVisible: false }); bbM.setData(' + json.dumps(bb_mid) + ');' if show_bb and bb_mid else ''}
    {'const bbL = mainChart.addLineSeries({ color: "#06b6d4", lineWidth: 1.5, lineStyle: 2, priceLineVisible: false }); bbL.setData(' + json.dumps(bb_low) + ');' if show_bb and bb_low else ''}

    // Overlays: Ichimoku
    {'const iTenkan = mainChart.addLineSeries({ color: "#ef4444", lineWidth: 1.8, priceLineVisible: false }); iTenkan.setData(' + json.dumps(ichi_tenkan) + ');' if show_ichi and ichi_tenkan else ''}
    {'const iKijun = mainChart.addLineSeries({ color: "#3b82f6", lineWidth: 2, priceLineVisible: false }); iKijun.setData(' + json.dumps(ichi_kijun) + ');' if show_ichi and ichi_kijun else ''}
    {'const iSpanA = mainChart.addLineSeries({ color: "#10b981", lineWidth: 1.2, lineStyle: 2, priceLineVisible: false }); iSpanA.setData(' + json.dumps(ichi_spana) + ');' if show_ichi and ichi_spana else ''}
    {'const iSpanB = mainChart.addLineSeries({ color: "#f43f5e", lineWidth: 1.2, lineStyle: 2, priceLineVisible: false }); iSpanB.setData(' + json.dumps(ichi_spanb) + ');' if show_ichi and ichi_spanb else ''}

    // Overlays: Parabolic SAR
    {'const sarS = mainChart.addLineSeries({ color: "#a855f7", lineWidth: 2, lineStyle: 1, priceLineVisible: false }); sarS.setData(' + json.dumps(sar_pts) + ');' if show_sar and sar_pts else ''}

    // Overlays: VWAP
    {'const vwapS = mainChart.addLineSeries({ color: "#eab308", lineWidth: 2, priceLineVisible: false }); vwapS.setData(' + json.dumps(vwap_pts) + ');' if show_vwap and vwap_pts else ''}

    const allCharts = [mainChart];

    // ================= 2. KHUNG PHỤ: RSI (14) =================
    {'const rsiCont = document.getElementById("tv_rsi_container"); const rsiChart = LightweightCharts.createChart(rsiCont, { width: rsiCont.clientWidth, height: ' + str(rsi_h) + ', layout: commonLayout, grid: commonGrid, rightPriceScale: { borderColor: "#334155", autoScale: true, scaleMargins: { top: 0.15, bottom: 0.15 } }, timeScale: { borderColor: "#334155", visible: false } }); const rsiLine = rsiChart.addLineSeries({ color: "#8b5cf6", lineWidth: 2, priceLineVisible: false }); rsiLine.setData(' + json.dumps(rsi_pts) + '); rsiLine.createPriceLine({ price: 70, color: "rgba(239, 68, 68, 0.7)", lineStyle: 2, title: "70 Quá mua" }); rsiLine.createPriceLine({ price: 30, color: "rgba(16, 185, 129, 0.7)", lineStyle: 2, title: "30 Quá bán" }); rsiLine.createPriceLine({ price: 50, color: "rgba(148, 163, 184, 0.4)", lineStyle: 3, title: "50" }); allCharts.push(rsiChart);' if show_rsi else ''}

    // ================= 3. KHUNG PHỤ: MACD (12, 26, 9) =================
    {'const macdCont = document.getElementById("tv_macd_container"); const macdChart = LightweightCharts.createChart(macdCont, { width: macdCont.clientWidth, height: ' + str(macd_h) + ', layout: commonLayout, grid: commonGrid, rightPriceScale: { borderColor: "#334155", autoScale: true, scaleMargins: { top: 0.15, bottom: 0.15 } }, timeScale: { borderColor: "#334155", visible: false } }); const mHist = macdChart.addHistogramSeries({ priceLineVisible: false }); mHist.setData(' + json.dumps(hist_pts) + '); const mLine = macdChart.addLineSeries({ color: "#38bdf8", lineWidth: 1.8, priceLineVisible: false }); mLine.setData(' + json.dumps(macd_pts) + '); const mSig = macdChart.addLineSeries({ color: "#f59e0b", lineWidth: 1.5, lineStyle: 2, priceLineVisible: false }); mSig.setData(' + json.dumps(signal_pts) + '); mLine.createPriceLine({ price: 0, color: "rgba(148, 163, 184, 0.4)", lineStyle: 3, title: "0" }); allCharts.push(macdChart);' if show_macd else ''}

    // ================= 4. KHUNG PHỤ: STOCHASTIC (14, 3) =================
    {'const stochCont = document.getElementById("tv_stoch_container"); const stochChart = LightweightCharts.createChart(stochCont, { width: stochCont.clientWidth, height: ' + str(stoch_h) + ', layout: commonLayout, grid: commonGrid, rightPriceScale: { borderColor: "#334155", autoScale: true, scaleMargins: { top: 0.15, bottom: 0.15 } }, timeScale: { borderColor: "#334155", visible: false } }); const sK = stochChart.addLineSeries({ color: "#06b6d4", lineWidth: 1.6, priceLineVisible: false }); sK.setData(' + json.dumps(stoch_k) + '); const sD = stochChart.addLineSeries({ color: "#f59e0b", lineWidth: 1.4, lineStyle: 2, priceLineVisible: false }); sD.setData(' + json.dumps(stoch_d) + '); sK.createPriceLine({ price: 80, color: "rgba(239, 68, 68, 0.7)", lineStyle: 2, title: "80 Quá mua" }); sK.createPriceLine({ price: 20, color: "rgba(16, 185, 129, 0.7)", lineStyle: 2, title: "20 Quá bán" }); allCharts.push(stochChart);' if show_stoch else ''}

    // ================= 5. KHUNG PHỤ: DÒNG TIỀN MFI (14) =================
    {'const mfiCont = document.getElementById("tv_mfi_container"); const mfiChart = LightweightCharts.createChart(mfiCont, { width: mfiCont.clientWidth, height: ' + str(mfi_h) + ', layout: commonLayout, grid: commonGrid, rightPriceScale: { borderColor: "#334155", autoScale: true, scaleMargins: { top: 0.15, bottom: 0.15 } }, timeScale: { borderColor: "#334155", visible: false } }); const mfiLine = mfiChart.addLineSeries({ color: "#10b981", lineWidth: 1.8, priceLineVisible: false }); mfiLine.setData(' + json.dumps(mfi_pts) + '); mfiLine.createPriceLine({ price: 80, color: "rgba(239, 68, 68, 0.7)", lineStyle: 2, title: "80" }); mfiLine.createPriceLine({ price: 20, color: "rgba(16, 185, 129, 0.7)", lineStyle: 2, title: "20" }); mfiLine.createPriceLine({ price: 50, color: "rgba(148, 163, 184, 0.4)", lineStyle: 3, title: "50" }); allCharts.push(mfiChart);' if show_mfi else ''}

    // ================= 6. KHUNG PHỤ: BIẾN ĐỘNG ATR (14) =================
    {'const atrCont = document.getElementById("tv_atr_container"); const atrChart = LightweightCharts.createChart(atrCont, { width: atrCont.clientWidth, height: ' + str(atr_h) + ', layout: commonLayout, grid: commonGrid, rightPriceScale: { borderColor: "#334155", autoScale: true, scaleMargins: { top: 0.15, bottom: 0.15 } }, timeScale: { borderColor: "#334155", visible: false } }); const atrLine = atrChart.addLineSeries({ color: "#ec4899", lineWidth: 1.6, priceLineVisible: false }); atrLine.setData(' + json.dumps(atr_pts) + '); allCharts.push(atrChart);' if show_atr else ''}

    // ================= 7. KHUNG PHỤ: KHỐI LƯỢNG CÂN BẰNG OBV =================
    {'const obvCont = document.getElementById("tv_obv_container"); const obvChart = LightweightCharts.createChart(obvCont, { width: obvCont.clientWidth, height: ' + str(obv_h) + ', layout: commonLayout, grid: commonGrid, rightPriceScale: { borderColor: "#334155", autoScale: true, scaleMargins: { top: 0.15, bottom: 0.15 } }, timeScale: { borderColor: "#334155", visible: false } }); const obvLine = obvChart.addLineSeries({ color: "#38bdf8", lineWidth: 1.8, priceLineVisible: false }); obvLine.setData(' + json.dumps(obv_pts) + '); allCharts.push(obvChart);' if show_obv else ''}

    // ================= 8. CẤP PHÁT TIMESCALE & ĐỒNG BỘ 100% =================
    // Chỉ chart cuối cùng ở dưới đáy mới hiển thị nhãn thời gian:
    if (allCharts.length > 0) {{
      allCharts.forEach((c, idx) => {{
        const isBottom = (idx === allCharts.length - 1);
        c.applyOptions({{
          timeScale: {{
            visible: isBottom,
            borderColor: '#334155',
            timeVisible: true,
            secondsVisible: false,
            barSpacing: 14,
            minBarSpacing: 4,
          }}
        }});
      }});
    }}

    // Đồng bộ cuộn / zoom / dời trục giữa tất cả các chart
    let isSyncing = false;
    allCharts.forEach(sourceChart => {{
      sourceChart.timeScale().subscribeVisibleLogicalRangeChange(range => {{
        if (isSyncing || !range) return;
        isSyncing = true;
        allCharts.forEach(targetChart => {{
          if (targetChart !== sourceChart) {{
            targetChart.timeScale().setVisibleLogicalRange(range);
          }}
        }});
        isSyncing = false;
      }});
    }});

    // Zoom mặc định 30 phiên gần nhất
    if (candleData.length > 0) {{
      const fromIdx = Math.max(0, candleData.length - 30);
      mainChart.timeScale().setVisibleLogicalRange({{
        from: fromIdx,
        to: candleData.length + 2,
      }});
    }}

    // Tự động co giãn theo chiều rộng cửa sổ
    window.addEventListener('resize', () => {{
      const w = mainContainer.clientWidth;
      allCharts.forEach(c => c.applyOptions({{ width: w }}));
    }});
  </script>
</body>
</html>"""

    if hasattr(st, "iframe"):
        st.iframe(lw_html, height=total_h + 20, width="stretch")
    else:
        import streamlit.components.v1 as components
        components.html(lw_html, height=total_h + 20)






