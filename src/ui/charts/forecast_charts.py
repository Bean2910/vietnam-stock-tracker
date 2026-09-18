"""
Module Biểu Đồ Dự Báo Giá & Trí Tuệ Nhân Tạo (AI / ML Forecasting Charts):
1. create_forecast_chart: Biểu đồ nón xác suất Monte Carlo Fan Chart
2. create_multi_model_comparison_chart: Biểu đồ đối chiếu đa chiều 4 mô hình Machine Learning
3. create_feature_importance_chart: Biểu đồ trọng số đóng góp các nhân tố chi phối giá
"""
from typing import Dict, Any, List
import pandas as pd
import plotly.graph_objects as go


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

    fig.update_yaxes(fixedrange=True)
    fig.update_layout(
        title=f"Dự Báo Xu Hướng Giá {ticker} ({forecast.get('forecast_days', 7)} Phiên Tới)",
        height=450,
        margin=dict(l=10, r=10, t=50, b=10),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        dragmode="pan",
        uirevision=ticker,
        transition=dict(duration=0),
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
        start_x = "Hiện Tại (T0)"
        pred_x = [start_x] + [f"T+{i+1} ({d[:5]})" for i, d in enumerate(future_dates)]
        all_displayed_prices = [last_y]

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

    fig.add_hline(
        y=last_y,
        line_dash="dot",
        line_color="#475569",
        line_width=1.5,
        annotation_text=f"Mức Giá Khớp Tham Chiếu (T0): {last_y:,.2f} ({last_y*1000:,.0f} VNĐ)",
        annotation_position="bottom right",
        annotation_font=dict(size=11, color="#334155"),
    )

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

    layout_kwargs["dragmode"] = "pan"
    layout_kwargs["uirevision"] = ticker
    layout_kwargs["transition"] = dict(duration=0)

    fig.update_layout(**layout_kwargs)
    fig.update_yaxes(fixedrange=True)
    return fig


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
