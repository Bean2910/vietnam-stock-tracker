"""
Module Tính toán Chỉ báo Kỹ thuật (Technical Indicators)
Được tối ưu hóa bằng Pandas & NumPy, không phụ thuộc thư viện C bên ngoài,
đảm bảo chạy mượt mà 100% trên mọi nền tảng Windows/Linux.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tính toán bộ chỉ báo kỹ thuật toàn diện cho DataFrame nến (OHLCV).
    Yêu cầu các cột: 'open', 'high', 'low', 'close', 'volume'
    """
    if df is None or len(df) < 5:
        return df

    data = df.copy()
    close = data["close"]
    high = data["high"]
    low = data["low"]
    volume = data["volume"]

    # 1. Đường Trung bình Động (Moving Averages)
    data["SMA20"] = close.rolling(window=20, min_periods=1).mean()
    data["SMA50"] = close.rolling(window=50, min_periods=1).mean()
    data["SMA200"] = close.rolling(window=200, min_periods=1).mean()
    data["EMA12"] = close.ewm(span=12, adjust=False).mean()
    data["EMA26"] = close.ewm(span=26, adjust=False).mean()

    # 2. MACD (Moving Average Convergence Divergence)
    data["MACD"] = data["EMA12"] - data["EMA26"]
    data["MACD_Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()
    data["MACD_Hist"] = data["MACD"] - data["MACD_Signal"]

    # 3. RSI (Relative Strength Index - 14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
    rs = gain / (loss.replace(0, np.nan))
    data["RSI14"] = 100 - (100 / (1 + rs))
    data["RSI14"] = data["RSI14"].fillna(50)

    # 4. Dải Bollinger Bands (20 kỳ, độ lệch chuẩn 2)
    bb_mean = close.rolling(window=20, min_periods=1).mean()
    bb_std = close.rolling(window=20, min_periods=1).std().fillna(0)
    data["BB_Upper"] = bb_mean + (bb_std * 2)
    data["BB_Middle"] = bb_mean
    data["BB_Lower"] = bb_mean - (bb_std * 2)
    data["BB_Width"] = ((data["BB_Upper"] - data["BB_Lower"]) / bb_mean * 100).fillna(0)

    # 5. Khối lượng Trung bình (Volume SMA20)
    data["VOL_SMA20"] = volume.rolling(window=20, min_periods=1).mean()
    data["VOL_Ratio"] = (volume / data["VOL_SMA20"].replace(0, np.nan)).fillna(1.0)

    # 6. ATR (Average True Range - 14) - Đo lường độ biến động
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    data["ATR14"] = tr.rolling(window=14, min_periods=1).mean()

    return data


def generate_technical_signals(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Phân tích và tổng hợp tín hiệu MUA / BÁN / TRUNG LẬP dựa trên đa chỉ báo
    """
    if df is None or len(df) < 2:
        return {
            "action": "TRUNG LẬP",
            "score": 50,
            "reasons": ["Chưa đủ dữ liệu để phân tích tín hiệu"],
            "support": 0,
            "resistance": 0,
        }

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    reasons = []
    bullish_points = 0
    bearish_points = 0

    # Kiểm tra RSI
    rsi = latest.get("RSI14", 50)
    if rsi < 30:
        bullish_points += 2
        reasons.append(f"RSI({rsi:.1f}) đang ở vùng QUÁ BÁN (< 30) - Khả năng bật tăng hồi phục.")
    elif rsi > 70:
        bearish_points += 2
        reasons.append(f"RSI({rsi:.1f}) đang ở vùng QUÁ MUA (> 70) - Áp lực chốt lời gia tăng.")
    elif 45 <= rsi <= 55:
        reasons.append(f"RSI({rsi:.1f}) cân bằng quanh ngưỡng 50.")
    elif rsi > 50:
        bullish_points += 1
        reasons.append(f"RSI({rsi:.1f}) giữ vững trên ngưỡng 50 (xu hướng tăng tích cực).")
    else:
        bearish_points += 1
        reasons.append(f"RSI({rsi:.1f}) dưới ngưỡng 50 (áp lực bán chiếm ưu thế).")

    # Kiểm tra MACD
    macd = latest.get("MACD", 0)
    macd_signal = latest.get("MACD_Signal", 0)
    prev_macd = prev.get("MACD", 0)
    prev_signal = prev.get("MACD_Signal", 0)

    if prev_macd <= prev_signal and macd > macd_signal:
        bullish_points += 2
        reasons.append("MACD cắt lên đường Signal (Tín hiệu Vàng - Golden Cross).")
    elif prev_macd >= prev_signal and macd < macd_signal:
        bearish_points += 2
        reasons.append("MACD cắt xuống đường Signal (Tín hiệu Tiêu cực - Death Cross).")
    elif macd > macd_signal:
        bullish_points += 1
        reasons.append("MACD duy trì nằm trên đường Signal.")
    else:
        bearish_points += 1
        reasons.append("MACD duy trì nằm dưới đường Signal.")

    # Kiểm tra MA20
    sma20 = latest.get("SMA20", latest["close"])
    close = latest["close"]
    if close > sma20:
        bullish_points += 1
        reasons.append(f"Giá đóng cửa ({close:,.1f}) nằm TRÊN đường trung bình SMA20 ({sma20:,.1f}).")
    else:
        bearish_points += 1
        reasons.append(f"Giá đóng cửa ({close:,.1f}) nằm DƯỚI đường trung bình SMA20 ({sma20:,.1f}).")

    # Kiểm tra Đột biến khối lượng (Volume Breakout)
    vol_ratio = latest.get("VOL_Ratio", 1.0)
    if vol_ratio >= 1.5:
        if close > prev["close"]:
            bullish_points += 2
            reasons.append(f"Khối lượng giao dịch bùng nổ ({vol_ratio:.1f}x so với TB 20 phiên) kèm giá tăng mạnh.")
        else:
            bearish_points += 2
            reasons.append(f"Khối lượng giao dịch tăng cao ({vol_ratio:.1f}x) kèm giá giảm - Cảnh báo phân phối.")

    # Vùng hỗ trợ và kháng cự ngắn hạn (20 phiên gần nhất)
    recent_20 = df.tail(20)
    support = float(recent_20["low"].min())
    resistance = float(recent_20["high"].max())

    total_points = bullish_points + bearish_points
    if total_points == 0:
        score = 50
    else:
        score = int((bullish_points / total_points) * 100)

    if score >= 65:
        action = "TÍCH CỰC / NÊN MUA"
    elif score <= 35:
        action = "TIÊU CỰC / NÊN BÁN"
    else:
        action = "TRUNG LẬP / QUAN SÁT"

    return {
        "action": action,
        "score": score,
        "bullish_points": bullish_points,
        "bearish_points": bearish_points,
        "reasons": reasons,
        "support": support,
        "resistance": resistance,
    }
