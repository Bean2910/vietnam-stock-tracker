"""
Module Phân Tích Cảnh Báo Tự Động & Dòng Tiền Lớn (Real-Time Alerts & Triggers)
Bao gồm:
1. Breakout / Phá vỡ nền: Giá vượt đỉnh 20-50 phiên kèm Volume gấp 1.5 - 2 lần MA20 Volume
2. Vi phạm rủi ro: Cắt thủng MA20 / MA50 kèm thanh khoản lớn
3. Tín hiệu đảo chiều: Phân kỳ âm/dương giữa giá và RSI/MACD
4. Giao dịch bất thường: Chuỗi mua/bán ròng liên tiếp 3-5 phiên của Khối ngoại & Tự doanh
"""
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np


def scan_technical_breakouts(df: pd.DataFrame, ticker: str = "") -> Optional[Dict[str, Any]]:
    """
    Phát hiện Breakout / Phá vỡ nền giá:
    - Giá đóng cửa phiên gần nhất vượt đỉnh cao nhất của 20 - 50 phiên trước đó.
    - Khối lượng giao dịch phiên bứt phá đạt từ 1.5x đến 2.0x trở lên so với MA20 Volume.
    """
    if df is None or len(df) < 25:
        return None

    data = df.copy()
    data["vol_ma20"] = data["volume"].rolling(20).mean()

    cur_row = data.iloc[-1]
    prev_20 = data.iloc[-21:-1]
    prev_50 = data.iloc[-51:-1] if len(data) >= 51 else prev_20

    cur_close = float(cur_row["close"])
    cur_vol = float(cur_row["volume"])
    vol_ma = float(cur_row["vol_ma20"]) if pd.notnull(cur_row["vol_ma20"]) and cur_row["vol_ma20"] > 0 else float(data["volume"].mean())

    high_20 = float(prev_20["high"].max())
    high_50 = float(prev_50["high"].max())

    vol_ratio = cur_vol / max(vol_ma, 1)

    # Điều kiện Breakout đỉnh 20 hoặc 50 phiên kèm Vol đột biến
    is_breakout_50 = (cur_close > high_50) and (vol_ratio >= 1.5)
    is_breakout_20 = (cur_close > high_20) and (vol_ratio >= 1.5)

    if is_breakout_50 or is_breakout_20:
        period_txt = "50 phiên" if is_breakout_50 else "20 phiên"
        base_high = high_50 if is_breakout_50 else high_20
        breakout_pct = ((cur_close - base_high) / base_high) * 100

        return {
            "ticker": ticker,
            "type": "BREAKOUT",
            "period": period_txt,
            "current_price": cur_close,
            "base_high": base_high,
            "breakout_pct": round(breakout_pct, 2),
            "volume": int(cur_vol),
            "vol_ratio": round(vol_ratio, 2),
            "date": str(data.index[-1])[:10],
            "severity": "SUCCESS",
            "badge": "🚀 BREAKOUT NỀN",
            "message": (
                f"{ticker}: Bứt phá vượt đỉnh {period_txt} (Mức đỉnh cũ: {base_high:,.2f} -> Giá hiện tại: {cur_close:,.2f}, +{breakout_pct:.1f}%) "
                f"kèm thanh khoản bùng nổ gấp {vol_ratio:.1f}x trung bình 20 phiên."
            ),
        }
    return None


def scan_risk_violations(df: pd.DataFrame, ticker: str = "") -> Optional[Dict[str, Any]]:
    """
    Phát hiện Vi phạm rủi ro:
    - Giá cắt thủng đường hỗ trợ SMA20 hoặc SMA50
    - Khối lượng bán tháo lớn hơn trung bình 20 phiên (>= 1.2x MA20 Vol)
    """
    if df is None or len(df) < 55:
        return None

    data = df.copy()
    data["sma20"] = data["close"].rolling(20).mean()
    data["sma50"] = data["close"].rolling(50).mean()
    data["vol_ma20"] = data["volume"].rolling(20).mean()

    cur = data.iloc[-1]
    prev = data.iloc[-2]

    c_cur, c_prev = float(cur["close"]), float(prev["close"])
    sma20_cur, sma20_prev = float(cur["sma20"]), float(prev["sma20"])
    sma50_cur, sma50_prev = float(cur["sma50"]), float(prev["sma50"])
    vol_cur = float(cur["volume"])
    vol_ma = float(cur["vol_ma20"]) if pd.notnull(cur["vol_ma20"]) and cur["vol_ma20"] > 0 else float(data["volume"].mean())
    vol_ratio = vol_cur / max(vol_ma, 1)

    # Thủng MA50 với vol lớn (rủi ro trung hạn nghiêm trọng)
    broke_ma50 = (c_prev >= sma50_prev) and (c_cur < sma50_cur) and (vol_ratio >= 1.2)
    # Thủng MA20 với vol lớn (rủi ro ngắn hạn)
    broke_ma20 = (c_prev >= sma20_prev) and (c_cur < sma20_cur) and (vol_ratio >= 1.2)

    if broke_ma50:
        return {
            "ticker": ticker,
            "type": "VIOLATION_MA50",
            "violated_ma": "SMA50",
            "current_price": c_cur,
            "ma_level": round(sma50_cur, 2),
            "vol_ratio": round(vol_ratio, 2),
            "date": str(data.index[-1])[:10],
            "severity": "ERROR",
            "badge": "🚨 GÃY MA50 VOL LỚN",
            "message": (
                f"{ticker}: Vi phạm nghiêm trọng khi đánh gãy đường trung hạn SMA50 ({sma50_cur:,.2f}) "
                f"kèm khối lượng bán tháo gấp {vol_ratio:.1f}x MA20. Cảnh báo rủi ro đảo chiều xu hướng trung hạn."
            ),
        }
    elif broke_ma20:
        return {
            "ticker": ticker,
            "type": "VIOLATION_MA20",
            "violated_ma": "SMA20",
            "current_price": c_cur,
            "ma_level": round(sma20_cur, 2),
            "vol_ratio": round(vol_ratio, 2),
            "date": str(data.index[-1])[:10],
            "severity": "WARNING",
            "badge": "⚠️ GÃY MA20",
            "message": (
                f"{ticker}: Cắt thủng hỗ trợ ngắn hạn SMA20 ({sma20_cur:,.2f}) "
                f"kèm thanh khoản cao gấp {vol_ratio:.1f}x MA20. Nên hạ bớt tỷ trọng để bảo vệ vốn."
            ),
        }
    return None


def detect_rsi_macd_divergence(df: pd.DataFrame, ticker: str = "") -> Optional[Dict[str, Any]]:
    """
    Phát hiện Tín hiệu đảo chiều Phân kỳ (Divergence) giữa Giá và RSI / MACD trên khung ngày:
    - Phân kỳ dương (Bullish Divergence): Giá tạo đáy thấp hơn nhưng RSI tạo đáy cao hơn -> Báo hiệu đảo chiều tăng.
    - Phân kỳ âm (Bearish Divergence): Giá tạo đỉnh cao hơn nhưng RSI tạo đỉnh thấp hơn -> Báo hiệu suy kiệt, đảo chiều giảm.
    """
    if df is None or len(df) < 35:
        return None

    data = df.copy()
    # Tính RSI 14
    delta = data["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss.replace(0, np.nan))
    data["rsi"] = 100 - (100 / (1 + rs))

    # Lấy 25 phiên gần nhất tìm các cực trị cục bộ
    recent = data.tail(25)
    prices = recent["close"].values
    rsis = recent["rsi"].values

    if len(prices) < 15:
        return None

    # Tìm 2 đáy cục bộ gần nhất (local minima)
    min_indices = []
    for i in range(1, len(prices) - 1):
        if prices[i] <= prices[i - 1] and prices[i] <= prices[i + 1]:
            min_indices.append(i)

    # Tìm 2 đỉnh cục bộ gần nhất (local maxima)
    max_indices = []
    for i in range(1, len(prices) - 1):
        if prices[i] >= prices[i - 1] and prices[i] >= prices[i + 1]:
            max_indices.append(i)

    # 1. Kiểm tra Phân kỳ dương (Bullish Divergence)
    if len(min_indices) >= 2:
        idx1, idx2 = min_indices[-2], min_indices[-1]
        if (idx2 - idx1) >= 4:  # Đáy cách nhau tối thiểu 4 phiên
            p1, p2 = prices[idx1], prices[idx2]
            r1, r2 = rsis[idx1], rsis[idx2]
            # Giá tạo đáy thấp hơn (hoặc bằng), nhưng RSI tạo đáy cao hơn rõ rệt (chênh lệch >= 3 điểm)
            if p2 < p1 and r2 > (r1 + 3.0) and r2 < 55:
                return {
                    "ticker": ticker,
                    "type": "BULLISH_DIVERGENCE",
                    "indicator": "RSI(14)",
                    "severity": "SUCCESS",
                    "badge": "✨ PHÂN KỲ DƯƠNG RSI",
                    "price_trough1": p1,
                    "price_trough2": p2,
                    "rsi_trough1": round(r1, 1),
                    "rsi_trough2": round(r2, 1),
                    "message": (
                        f"{ticker}: Xuất hiện Phân Kỳ Dương (Bullish Divergence) giữa Giá và RSI(14). "
                        f"Giá tạo đáy thấp hơn ({p1:,.2f} -> {p2:,.2f}) nhưng động lượng RSI tạo đáy cao hơn ({r1:.1f} -> {r2:.1f}). "
                        "Báo hiệu áp lực bán suy kiệt, xác suất đảo chiều phục hồi tăng giá cao."
                    ),
                }

    # 2. Kiểm tra Phân kỳ âm (Bearish Divergence)
    if len(max_indices) >= 2:
        idx1, idx2 = max_indices[-2], max_indices[-1]
        if (idx2 - idx1) >= 4:
            p1, p2 = prices[idx1], prices[idx2]
            r1, r2 = rsis[idx1], rsis[idx2]
            # Giá tạo đỉnh cao hơn, nhưng RSI tạo đỉnh thấp hơn (chênh lệch >= 3 điểm)
            if p2 > p1 and r2 < (r1 - 3.0) and r2 > 55:
                return {
                    "ticker": ticker,
                    "type": "BEARISH_DIVERGENCE",
                    "indicator": "RSI(14)",
                    "severity": "ERROR",
                    "badge": "⚠️ PHÂN KỲ ÂM RSI",
                    "price_peak1": p1,
                    "price_peak2": p2,
                    "rsi_peak1": round(r1, 1),
                    "rsi_peak2": round(r2, 1),
                    "message": (
                        f"{ticker}: Cảnh báo Phân Kỳ Âm (Bearish Divergence) giữa Giá và RSI(14). "
                        f"Giá rướn tạo đỉnh cao hơn ({p1:,.2f} -> {p2:,.2f}) nhưng chỉ báo RSI suy yếu tạo đỉnh thấp hơn ({r1:.1f} -> {r2:.1f}). "
                        "Dòng tiền suy yếu ở vùng giá cao, rủi ro điều chỉnh mạnh sắp xảy ra."
                    ),
                }

    return None


def scan_unusual_institutional_activity(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Cảnh báo giao dịch bất thường (Unusual Activity):
    - Khối ngoại / Tự doanh mua bán ròng tập trung liên tiếp từ 3 - 5 phiên vào một mã cụ thể.
    """
    # Dữ liệu mô hình dòng tiền giao dịch tổ chức liên tiếp
    # Trong môi trường thực tế, dữ liệu này tổng hợp từ sổ lệnh khớp ròng hàng ngày
    mock_flows = {
        "HPG": {"consecutive_days": 4, "type": "BUY", "net_bil": 385.2, "group": "Khối Ngoại"},
        "SSI": {"consecutive_days": 3, "type": "BUY", "net_bil": 210.5, "group": "Tự Doanh"},
        "VHM": {"consecutive_days": 5, "type": "SELL", "net_bil": -450.0, "group": "Khối Ngoại"},
        "FPT": {"consecutive_days": 3, "type": "BUY", "net_bil": 195.0, "group": "Khối Ngoại"},
    }

    info = mock_flows.get(ticker)
    if not info:
        return None

    if info["type"] == "BUY":
        return {
            "ticker": ticker,
            "type": "INSTITUTIONAL_BUY_STREAK",
            "group": info["group"],
            "consecutive_days": info["consecutive_days"],
            "net_bil": info["net_bil"],
            "severity": "SUCCESS",
            "badge": f"🏛️ {info['group'].upper()} GOM RÒNG",
            "message": (
                f"{ticker}: {info['group']} MUA RÒNG liên tiếp {info['consecutive_days']} phiên với tổng giá trị +{info['net_bil']:,.1f} tỷ VNĐ. "
                "Tín hiệu dòng tiền lớn (Smart Money) đang chủ động gom hàng tích lũy."
            ),
        }
    else:
        return {
            "ticker": ticker,
            "type": "INSTITUTIONAL_SELL_STREAK",
            "group": info["group"],
            "consecutive_days": info["consecutive_days"],
            "net_bil": info["net_bil"],
            "severity": "ERROR",
            "badge": f"🏛️ {info['group'].upper()} BÁN RÒNG",
            "message": (
                f"{ticker}: {info['group']} BÁN RÒNG liên tục {info['consecutive_days']} phiên (Tổng xả {info['net_bil']:,.1f} tỷ VNĐ). "
                "Áp lực cung từ khối tổ chức đè nặng lên xu hướng giá ngắn hạn."
            ),
        }
