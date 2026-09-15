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
    show_bb: bool = True,
    show_rsi: bool = True,
) -> go.Figure:
    """
    Tạo biểu đồ kỹ thuật chuẩn TradingView bằng Plotly:
    - Hàng 1: Nến Nhật + SMA + Bollinger Bands
    - Hàng 2: Khối lượng giao dịch (Volume Bar)
    - Hàng 3: Chỉ báo RSI(14)
    """
    rows = 3 if show_rsi else 2
    row_heights = [0.6, 0.2, 0.2] if show_rsi else [0.75, 0.25]

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=(f"Biểu đồ Kỹ thuật {ticker}", "Khối lượng (Volume)", "Chỉ số RSI (14)") if show_rsi else (f"Biểu đồ Kỹ thuật {ticker}", "Khối lượng"),
    )

    # 1. Nến Nhật (Candlestick)
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=ticker,
            increasing_line_color="#10b981",
            decreasing_line_color="#ef4444",
        ),
        row=1,
        col=1,
    )

    # 2. Các đường SMA
    if show_sma:
        if "SMA20" in df.columns:
            fig.add_trace(
                go.Scatter(x=df.index, y=df["SMA20"], mode="lines", name="SMA 20", line=dict(color="#f59e0b", width=1.5)),
                row=1, col=1,
            )
        if "SMA50" in df.columns:
            fig.add_trace(
                go.Scatter(x=df.index, y=df["SMA50"], mode="lines", name="SMA 50", line=dict(color="#3b82f6", width=1.5)),
                row=1, col=1,
            )

    # 3. Dải Bollinger Bands
    if show_bb and "BB_Upper" in df.columns and "BB_Lower" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["BB_Upper"], mode="lines", name="BB Upper", line=dict(color="rgba(156, 163, 175, 0.6)", width=1, dash="dot")),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df["BB_Lower"], mode="lines", name="BB Lower",
                line=dict(color="rgba(156, 163, 175, 0.6)", width=1, dash="dot"),
                fill="tonexty", fillcolor="rgba(156, 163, 175, 0.08)",
            ),
            row=1, col=1,
        )

    # 4. Khối lượng Volume
    colors = ["#10b981" if c >= o else "#ef4444" for c, o in zip(df["close"], df["open"])]
    fig.add_trace(
        go.Bar(x=df.index, y=df["volume"], name="Volume", marker_color=colors, showlegend=False),
        row=2, col=1,
    )
    if "VOL_SMA20" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["VOL_SMA20"], mode="lines", name="Vol SMA20", line=dict(color="#6366f1", width=1.2)),
            row=2, col=1,
        )

    # 5. Chỉ báo RSI
    if show_rsi and "RSI14" in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df["RSI14"], mode="lines", name="RSI (14)", line=dict(color="#8b5cf6", width=1.8)),
            row=3, col=1,
        )
        # Đường ngưỡng 70 và 30
        fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", line_width=1, row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#10b981", line_width=1, row=3, col=1)

    fig.update_layout(
        height=750,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        template="plotly_dark",
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
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_multi_model_comparison_chart(
    df: pd.DataFrame,
    ml_result: Dict[str, Any],
    selected_models: List[str],
    ticker: str,
) -> go.Figure:
    """
    Biểu đồ đối chiếu đa chiều nhiều mô hình dự báo trên cùng 1 đồ thị tương tác Plotly
    """
    fig = go.Figure()
    all_models = ml_result.get("models", {})
    future_dates = ml_result.get("future_dates", [])
    if not all_models:
        return fig

    # 25 phiên nến lịch sử thực tế gần nhất
    hist = df.tail(25).copy()
    hist_x = [d.strftime("%d/%m") if hasattr(d, "strftime") else str(d) for d in hist.index]
    last_x = hist_x[-1]
    last_y = float(hist["close"].iloc[-1])

    # Đường giá thực tế
    fig.add_trace(
        go.Scatter(
            x=hist_x,
            y=hist["close"],
            mode="lines+markers",
            name="Giá Thực Tế (HOSE)",
            line=dict(color="#f8fafc", width=2.5),
            marker=dict(size=4),
        )
    )

    pred_x = [last_x] + [d[:5] + f" (T+{i+1})" for i, d in enumerate(future_dates)]

    # Vẽ từng mô hình mà người dùng chọn
    for m_name in selected_models:
        if m_name in all_models:
            m_info = all_models[m_name]
            pred_y = [last_y] + list(m_info["prices"])
            line_width = 3.5 if "Đồng Thuận" in m_name else 2.0

            fig.add_trace(
                go.Scatter(
                    x=pred_x,
                    y=pred_y,
                    mode="lines+markers",
                    name=f"{m_name} ({m_info['expected_return']:+.2f}%)",
                    line=dict(
                        color=m_info.get("color", "#c084fc"),
                        width=line_width,
                        dash=m_info.get("dash", "solid"),
                    ),
                    marker=dict(size=6),
                )
            )

    fig.update_layout(
        title=f"🌐 Đối Chiếu Đa Chiều Các Mô Hình Dự Báo Xu Hướng Giá ({ticker})",
        height=480,
        margin=dict(l=10, r=10, t=50, b=10),
        hovermode="x unified",
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title="Thời Gian",
        yaxis_title="Mức Giá (nghìn VNĐ)",
    )
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
        template="plotly_dark",
    )
    return fig

