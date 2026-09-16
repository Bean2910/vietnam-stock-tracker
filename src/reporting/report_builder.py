"""
Module Sinh Báo cáo Tóm tắt & Xuất File (HTML & Markdown Report Builder)
Tạo báo cáo chi tiết về tình hình cổ phiếu, phân tích kỹ thuật, dự báo và khuyến nghị.
"""
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd


def generate_ticker_report_markdown(
    ticker: str,
    quote_info: Dict[str, Any],
    signals: Dict[str, Any],
    forecast: Dict[str, Any],
    watchlist_info: Optional[Dict[str, Any]] = None,
) -> str:
    """Tạo báo cáo chi tiết dạng Markdown"""
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    current_price = quote_info.get("price", 0)
    change = quote_info.get("change", 0)
    pct_change = quote_info.get("pct_change", 0)
    volume = quote_info.get("volume", 0)

    color_emoji = "🟢" if change > 0 else ("🔴" if change < 0 else "🟡")

    target_price = watchlist_info.get("target_price") if watchlist_info else None
    stop_loss = watchlist_info.get("stop_loss") if watchlist_info else None
    note = watchlist_info.get("note", "Chưa có ghi chú") if watchlist_info else "Chưa theo dõi trong Watchlist"

    reasons_md = "\n".join([f"- {r}" for r in signals.get("reasons", [])])

    md = f"""# 📊 BÁO CÁO PHÂN TÍCH CỔ PHIẾU: **{ticker}**
*Thời gian xuất báo cáo: {now_str}*

---

## 1. TÌNH HÌNH THỊ TRƯỜNG HIỆN TẠI
- **Giá hiện tại**: `{current_price:,.2f}` ({current_price*1000:,.0f} VNĐ) ({color_emoji} {change:+,.2f} / {pct_change:+.2f}%)
- **Khối lượng giao dịch**: `{volume:,.0f}` cổ phiếu
- **Vùng dao động gần nhất (Hỗ trợ - Kháng cự)**: `{signals.get('support', 0):,.2f}` — `{signals.get('resistance', 0):,.2f}`

---

## 2. ĐÁNH GIÁ PHÂN TÍCH KỸ THUẬT & TÍN HIỆU
- **Khuyến nghị kỹ thuật**: **{signals.get('action', 'TRUNG LẬP')}** (Điểm số kỹ thuật: `{signals.get('score', 50)}/100`)
- **Tín hiệu chi tiết**:
{reasons_md}

---

## 3. DỰ BÁO XU HƯỚNG & KỊCH BẢN GIÁ ({forecast.get('forecast_days', 7)} PHIÊN TỚI)
- **Định hướng xu hướng**: **{forecast.get('outlook', 'N/A')}**
- **Xác suất tăng giá**: `{forecast.get('upward_probability', 50)}%`
- **Giá mục tiêu cơ sở (Base Case)**: `{forecast.get('target_price_base', current_price):,.1f}` ({forecast.get('expected_return_pct', 0):+.2f}%)
- **Kịch bản lạc quan (Bull Case 80%)**: `{forecast.get('target_price_bull', current_price):,.1f}`
- **Kịch bản thận trọng (Bear Case 20%)**: `{forecast.get('target_price_bear', current_price):,.1f}`
- **Khuyến nghị hành động**: *{forecast.get('recommendation', 'N/A')}*

---

## 4. THÔNG TIN DANH MỤC THEO DÕI (WATCHLIST)
- **Giá mục tiêu cá nhân**: `{f'{target_price:,.1f}' if target_price else 'Chưa cài đặt'}`
- **Ngưỡng cắt lỗ**: `{f'{stop_loss:,.1f}' if stop_loss else 'Chưa cài đặt'}`
- **Ghi chú chiến lược**: {note}

---
*Báo cáo được tổng hợp tự động bởi Vietnam Stock Tracker & Forecast Engine.*
"""
    return md


def generate_ticker_report_html(
    ticker: str,
    quote_info: Dict[str, Any],
    signals: Dict[str, Any],
    forecast: Dict[str, Any],
    watchlist_info: Optional[Dict[str, Any]] = None,
) -> str:
    """Tạo báo cáo giao diện HTML đẹp mắt, chuyên nghiệp, hỗ trợ in ấn hoặc lưu trữ"""
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    current_price = quote_info.get("price", 0)
    change = quote_info.get("change", 0)
    pct_change = quote_info.get("pct_change", 0)
    volume = quote_info.get("volume", 0)

    price_color = "#10b981" if change > 0 else ("#ef4444" if change < 0 else "#f59e0b")
    action = signals.get("action", "TRUNG LẬP")
    action_badge_color = "#10b981" if "MUA" in action else ("#ef4444" if "BÁN" in action else "#6b7280")

    target_price = watchlist_info.get("target_price") if watchlist_info else None
    stop_loss = watchlist_info.get("stop_loss") if watchlist_info else None
    note = watchlist_info.get("note", "Chưa có ghi chú") if watchlist_info else "Chưa nằm trong Watchlist"

    reasons_li = "".join([f"<li style='margin-bottom: 6px;'>{r}</li>" for r in signals.get("reasons", [])])

    forecast_table_rows = ""
    forecast_df = forecast.get("forecast_df")
    if forecast_df is not None and isinstance(forecast_df, pd.DataFrame):
        for _, row in forecast_df.iterrows():
            pct = row.get("expected_pct", 0)
            c = "#10b981" if pct > 0 else ("#ef4444" if pct < 0 else "#6b7280")
            forecast_table_rows += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{row.get('date', '')} ({row.get('day_step', '')})</td>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; font-weight: bold;">{row.get('base_price', 0):,.1f}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; color: #10b981;">{row.get('bull_price', 0):,.1f}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; color: #ef4444;">{row.get('bear_price', 0):,.1f}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; color: {c}; font-weight: 600;">{pct:+.2f}%</td>
            </tr>
            """

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Báo cáo Phân tích Cổ phiếu {ticker}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f8fafc;
            color: #1e293b;
            margin: 0;
            padding: 30px;
        }}
        .report-card {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            padding: 40px;
            border: 1px solid #e2e8f0;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #0284c7;
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .title {{
            font-size: 28px;
            font-weight: 800;
            color: #0f172a;
            margin: 0;
        }}
        .meta {{
            color: #64748b;
            font-size: 14px;
        }}
        .badge {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            color: white;
            font-weight: 700;
            font-size: 14px;
            background-color: {action_badge_color};
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat-box {{
            background: #f1f5f9;
            padding: 16px;
            border-radius: 8px;
            border-left: 4px solid #0284c7;
        }}
        .stat-label {{
            font-size: 13px;
            color: #64748b;
            margin-bottom: 4px;
        }}
        .stat-value {{
            font-size: 22px;
            font-weight: 800;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            color: #0369a1;
            margin-top: 24px;
            margin-bottom: 12px;
            border-left: 4px solid #0369a1;
            padding-left: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 14px;
        }}
        th {{
            background: #f8fafc;
            padding: 10px;
            text-align: left;
            border-bottom: 2px solid #cbd5e1;
            color: #475569;
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            font-size: 12px;
            color: #94a3b8;
            border-top: 1px solid #e2e8f0;
            padding-top: 16px;
        }}
    </style>
</head>
<body>
    <div class="report-card">
        <div class="header">
            <div>
                <h1 class="title">BÁO CÁO PHÂN TÍCH: {ticker}</h1>
                <div class="meta">Thời gian xuất: {now_str} | Thị trường Chứng khoán Việt Nam</div>
            </div>
            <div>
                <span class="badge">{action}</span>
            </div>
        </div>

        <div class="grid">
            <div class="stat-box" style="border-left-color: {price_color};">
                <div class="stat-label">Giá Thị Trường Hiện Tại</div>
                <div class="stat-value" style="color: {price_color};">{current_price:,.2f} <span style="font-size: 14px; font-weight: 500; color: #64748b;">({current_price*1000:,.0f} VNĐ)</span></div>
                <div style="font-size: 13px; color: {price_color}; font-weight: 600;">{change:+,.2f} ({pct_change:+.2f}%)</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Khối Lượng Khớp Lệnh</div>
                <div class="stat-value">{volume:,.0f}</div>
                <div style="font-size: 13px; color: #64748b;">Cổ phiếu trong phiên</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Kháng Cự / Hỗ Trợ Gần Nhất</div>
                <div class="stat-value" style="font-size: 18px; line-height: 28px;">{signals.get('support', 0):,.2f} - {signals.get('resistance', 0):,.2f}</div>
                <div style="font-size: 13px; color: #64748b;">Khung 20 phiên</div>
            </div>
        </div>

        <div class="section-title">1. Nhận Định & Tín Hiệu Kỹ Thuật</div>
        <ul style="background: #f8fafc; padding: 16px 20px 16px 36px; border-radius: 8px; border: 1px solid #e2e8f0; font-size: 14px;">
            {reasons_li}
        </ul>

        <div class="section-title">2. Dự Báo Xu Hướng & Kịch Bản Giá ({forecast.get('forecast_days', 7)} Phiên Tới)</div>
        <div style="background: #eff6ff; padding: 16px; border-radius: 8px; margin-bottom: 12px; border: 1px solid #bfdbfe;">
            <div><strong>Xu hướng chủ đạo:</strong> {forecast.get('outlook', 'N/A')}</div>
            <div><strong>Xác suất tăng giá:</strong> <span style="font-weight: bold; color: #0284c7;">{forecast.get('upward_probability', 50)}%</span></div>
            <div><strong>Chiến lược khuyến nghị:</strong> {forecast.get('recommendation', 'N/A')}</div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Phiên / Ngày</th>
                    <th>Giá Cơ Sở (Base)</th>
                    <th>Lạc Quan (+80%)</th>
                    <th>Thận Trọng (-20%)</th>
                    <th>Biến Động Kỳ Vọng</th>
                </tr>
            </thead>
            <tbody>
                {forecast_table_rows}
            </tbody>
        </table>

        <div class="section-title">3. Quản Lý Danh Mục Theo Dõi (Watchlist)</div>
        <div style="background: #f8fafc; padding: 16px; border-radius: 8px; border: 1px solid #e2e8f0; font-size: 14px;">
            <p style="margin: 4px 0;"><strong>Giá mục tiêu chốt lời:</strong> {f'{target_price:,.1f} VND' if target_price else 'Chưa thiết lập'}</p>
            <p style="margin: 4px 0;"><strong>Ngưỡng cắt lỗ:</strong> {f'{stop_loss:,.1f} VND' if stop_loss else 'Chưa thiết lập'}</p>
            <p style="margin: 4px 0;"><strong>Ghi chú chiến lược:</strong> {note}</p>
        </div>

        <div class="footer">
            Báo cáo được tổng hợp tự động từ hệ thống Vietnam Stock Tracker & Forecast Engine. Khuyến nghị chỉ mang tính chất tham khảo.
        </div>
    </div>
</body>
</html>
"""
    return html
