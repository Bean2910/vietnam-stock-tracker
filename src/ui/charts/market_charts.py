"""
Module Biểu Đồ Thị Trường & Định Giá (Market Breadth, Sector Treemap & Valuation Bands):
1. create_market_breadth_card: Thẻ đo độ rộng thị trường & cảnh báo bẫy Xanh vỏ đỏ lòng
2. create_sector_treemap_chart: Ma trận tương quan ngành (Sector Heatmap dạng Treemap)
3. create_valuation_bands_chart: Dải định giá lịch sử P/E Bands (+-1SD, +-2SD)
"""
from typing import Dict, Any, List
import numpy as np
import pandas as pd
import plotly.graph_objects as go


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


def create_sector_treemap_chart(
    sector_stocks: List[Dict[str, Any]],
    size_by: str = "turnover",
) -> go.Figure:
    """
    Tạo Bản Đồ Nhiệt Thị Trường (Market Heatmap dạng Treemap):
    - Kích thước khối: Tùy chọn theo Giá trị giao dịch (Tỷ VNĐ) hoặc Khối lượng (CP)
    - Màu sắc: % Tăng giảm giá theo quy ước TTCK Việt Nam (Sàn -7% Xanh lơ, Đỏ, Tham chiếu 0%, Xanh lục, Trần +7% Tím)
    """
    if not sector_stocks:
        fig = go.Figure()
        fig.update_layout(title="Chưa có dữ liệu thị trường để hiển thị Heatmap")
        return fig

    # Tiêu đề & đơn vị đo lường kích thước khối
    is_turnover = (size_by == "turnover")
    size_label = "Giá trị GD (Tỷ VNĐ)" if is_turnover else "Khối lượng (CP)"

    def _calc_stock_val(s: Dict[str, Any]) -> float:
        vol = float(s.get("volume", 0) or 0)
        p = float(s.get("price", 0.0) or 0.0)
        if is_turnover:
            turnover_bil = (p * 1000.0 * vol) / 1_000_000_000.0
            return max(round(turnover_bil, 2), 0.5)
        return max(vol, 1000.0)

    total_val = sum([_calc_stock_val(s) for s in sector_stocks])

    ids = ["root"]
    labels = ["Toàn Thị Trường"]
    parents = [""]
    values = [total_val]
    colors = ["#e2e8f0"]
    text_colors = ["#0f172a"]
    hover_texts = [f"<b>Toàn Thị Trường</b><br>Tổng quy mô: {total_val:,.1f} {'Tỷ VNĐ' if is_turnover else 'CP'}"]

    # Nhóm theo ngành
    sectors_map: Dict[str, List[Dict[str, Any]]] = {}
    for s in sector_stocks:
        sec = s.get("sector", "Khác")
        if sec not in sectors_map:
            sectors_map[sec] = []
        sectors_map[sec].append(s)

    for sec, stocks in sectors_map.items():
        sec_id = f"sec_{sec}"
        sec_total_val = sum([_calc_stock_val(s) for s in stocks])
        sec_avg_chg = float(np.mean([s.get("change", 0.0) for s in stocks]))
        
        ids.append(sec_id)
        labels.append(f"<b>{sec}</b>")
        parents.append("root")
        values.append(sec_total_val)
        colors.append("#f1f5f9")
        text_colors.append("#0f172a")
        hover_texts.append(
            f"<b>Ngành: {sec}</b><br>"
            f"Số mã: {len(stocks)} CP<br>"
            f"Biến động TB: <b>{sec_avg_chg:+.2f}%</b><br>"
            f"Tổng thanh khoản: {sec_total_val:,.1f} {'Tỷ VNĐ' if is_turnover else 'CP'}"
        )

        for s in stocks:
            sym = s.get("ticker", "")
            p_chg = s.get("change", 0.0)
            vol = s.get("volume", 0)
            price = s.get("price", 0.0)
            val = _calc_stock_val(s)
            t_bil = (price * 1000.0 * vol) / 1_000_000_000.0

            # Xác định màu sắc theo quy ước chuẩn sàn Vietstock
            if p_chg >= 6.8:
                tile_color = "#9333ea"  # Tím trần
                txt_color = "#ffffff"
            elif p_chg > 0.05:
                tile_color = "#16a34a"  # Xanh lá tăng
                txt_color = "#ffffff"
            elif -0.05 <= p_chg <= 0.05:
                tile_color = "#eab308"  # Vàng tham chiếu (Đứng giá)
                txt_color = "#0f172a"   # Chữ đen trên nền vàng
            elif p_chg <= -6.8:
                tile_color = "#0284c7"  # Xanh lơ sàn
                txt_color = "#ffffff"
            else:
                tile_color = "#dc2626"  # Đỏ giảm
                txt_color = "#ffffff"

            ids.append(f"stock_{sym}_{sec}")
            labels.append(f"<b>{sym}</b><br>{p_chg:+.2f}%")
            parents.append(sec_id)
            values.append(val)
            colors.append(tile_color)
            text_colors.append(txt_color)
            hover_texts.append(
                f"<b>{sym}</b> ({sec})<br>"
                f"Giá khớp: <b>{price:,.2f}</b> ({price * 1000:,.0f} đ)<br>"
                f"Biến động: <b>{p_chg:+.2f}%</b><br>"
                f"Khối lượng: <b>{vol:,} CP</b><br>"
                f"Thanh khoản: <b>{t_bil:,.1f} Tỷ VNĐ</b>"
            )

    fig = go.Figure(
        go.Treemap(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            marker=dict(
                colors=colors,
                line=dict(width=2, color="#ffffff"),
            ),
            hoverinfo="text",
            hovertext=hover_texts,
            branchvalues="total",
            textposition="middle center",
            textfont=dict(size=14, color=text_colors, family="Segoe UI, sans-serif"),
            pathbar=dict(visible=False),
            tiling=dict(packing="squarify", pad=3),
        )
    )

    fig.update_layout(
        height=580,
        margin=dict(l=5, r=5, t=10, b=10),
    )
    return fig


def create_valuation_bands_chart(
    df: pd.DataFrame,
    ticker: str,
    valuation_info: Dict[str, Any],
) -> go.Figure:
    """
    Biểu đồ Dải Định Giá Lịch Sử (Historical Valuation Bands) P/E:
    Quy đổi các mốc P/E (+2SD, +1SD, Mean, -1SD, -2SD) thành các dải giá mục tiêu tương ứng.
    """
    fig = go.Figure()
    if df is None or len(df) < 20:
        return fig

    dates = df.index
    closes = df["close"].values

    cur_p = valuation_info.get("current_price", float(closes[-1]))
    cur_pe = max(valuation_info.get("current_pe", 15.0), 1.0)
    pe_bands = valuation_info.get("pe_bands", {})

    eps = cur_p / cur_pe

    p_plus_2sd = eps * pe_bands.get("plus_2sd", cur_pe * 1.3)
    p_plus_1sd = eps * pe_bands.get("plus_1sd", cur_pe * 1.15)
    p_mean = eps * pe_bands.get("mean", cur_pe)
    p_minus_1sd = eps * pe_bands.get("minus_1sd", cur_pe * 0.85)
    p_minus_2sd = eps * pe_bands.get("minus_2sd", cur_pe * 0.7)

    # 1. Đường giá thực tế
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=closes,
            mode="lines",
            name=f"Giá {ticker}",
            line=dict(color="#38bdf8", width=2.5),
        )
    )

    # 2. Dải +2SD (Quá đắt / Bong bóng)
    fig.add_hline(
        y=p_plus_2sd,
        line_dash="dot",
        line_color="#ef4444",
        line_width=1.5,
        annotation_text=f"🔴 +2SD ({pe_bands.get('plus_2sd', 0)}x): {p_plus_2sd:,.2f}",
        annotation_position="top right",
        annotation_font=dict(size=11, color="#ef4444"),
    )

    # 3. Dải +1SD (Hơi đắt)
    fig.add_hline(
        y=p_plus_1sd,
        line_dash="dash",
        line_color="#f59e0b",
        line_width=1.2,
        annotation_text=f"🟡 +1SD ({pe_bands.get('plus_1sd', 0)}x): {p_plus_1sd:,.2f}",
        annotation_position="top right",
        annotation_font=dict(size=11, color="#f59e0b"),
    )

    # 4. Đường Mean P/E (Giá trị hợp lý bình quân)
    fig.add_hline(
        y=p_mean,
        line_dash="solid",
        line_color="#94a3b8",
        line_width=1.8,
        annotation_text=f"⚪ Mean P/E ({pe_bands.get('mean', 0)}x): {p_mean:,.2f}",
        annotation_position="top left",
        annotation_font=dict(size=11, color="#94a3b8"),
    )

    # 5. Dải -1SD (Định giá hấp dẫn)
    fig.add_hline(
        y=p_minus_1sd,
        line_dash="dash",
        line_color="#3b82f6",
        line_width=1.2,
        annotation_text=f"🔵 -1SD ({pe_bands.get('minus_1sd', 0)}x): {p_minus_1sd:,.2f}",
        annotation_position="bottom right",
        annotation_font=dict(size=11, color="#3b82f6"),
    )

    # 6. Dải -2SD (Món hời / Vùng đáy)
    fig.add_hline(
        y=p_minus_2sd,
        line_dash="dot",
        line_color="#10b981",
        line_width=1.5,
        annotation_text=f"🟢 -2SD ({pe_bands.get('minus_2sd', 0)}x): {p_minus_2sd:,.2f}",
        annotation_position="bottom right",
        annotation_font=dict(size=11, color="#10b981"),
    )

    fig.update_layout(
        title=dict(
            text=f"📈 Biểu Đồ Dải Định Giá Lịch Sử (Historical P/E Valuation Bands) - {ticker}",
            x=0.01,
            y=0.98,
        ),
        height=480,
        margin=dict(l=55, r=50, t=55, b=40),
        xaxis=dict(showgrid=True),
        yaxis=dict(
            title="Mức Giá Quy Đổi Theo P/E (nghìn VNĐ)",
            showgrid=True,
            tickformat=",.2f",
            fixedrange=True,
            automargin=False,
        ),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        dragmode="pan",
        uirevision=ticker,
        transition=dict(duration=0),
    )
    return fig
