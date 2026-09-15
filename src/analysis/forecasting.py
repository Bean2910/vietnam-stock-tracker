"""
Module Dự báo Xu hướng & Kịch bản Giá Cổ phiếu (Stock Price & Trend Forecasting)
Tích hợp mô hình chuỗi thời gian định lượng và mô phỏng Monte Carlo xác suất,
dự báo giá mục tiêu ngắn hạn (5 - 15 phiên) kèm dải tin cậy xác suất.
"""
from typing import Dict, Any, List
import pandas as pd
import numpy as np


def forecast_price_trend(df: pd.DataFrame, forecast_days: int = 7) -> Dict[str, Any]:
    """
    Dự báo xu hướng giá và sinh các kịch bản giá cho N phiên kế tiếp.
    Dựa trên:
    - Drift & Volatility (Lợi suất logarit & độ biến động lịch sử)
    - Mô phỏng Monte Carlo 500 kịch bản ngẫu nhiên
    - Khoảng tin cậy 80% (Bullish / Base / Bearish)
    """
    if df is None or len(df) < 20:
        return {
            "error": "Cần tối thiểu 20 phiên giao dịch để xây dựng mô hình dự báo",
            "forecast_data": None,
        }

    close_series = df["close"].dropna().values
    last_price = float(close_series[-1])

    # 1. Tính toán log returns và độ biến động (Volatility)
    log_returns = np.diff(np.log(close_series))
    mu = float(np.mean(log_returns))          # Lợi suất trung bình ngày
    sigma = float(np.std(log_returns))        # Độ biến động (Volatilty)

    # Nếu biến động quá nhỏ
    if sigma == 0:
        sigma = 0.01

    # Trọng số gia tăng cho xu hướng gần đây (Momentum weighting)
    recent_trend = (close_series[-1] - close_series[-10]) / close_series[-10]
    drift = mu + (recent_trend / 20.0)

    # 2. Mô phỏng Monte Carlo (500 lần lặp)
    num_simulations = 500
    np.random.seed(42)  # Cố định seed để kết quả dự báo nhất quán trong phiên

    daily_shocks = np.random.normal(loc=drift, scale=sigma, size=(num_simulations, forecast_days))
    price_paths = np.zeros((num_simulations, forecast_days + 1))
    price_paths[:, 0] = last_price

    for t in range(1, forecast_days + 1):
        price_paths[:, t] = price_paths[:, t - 1] * np.exp(daily_shocks[:, t - 1])

    # 3. Tổng hợp các kịch bản theo Percentile
    # P80: Kịch bản Lạc quan (Bullish)
    # P50: Kịch bản Cơ sở (Base/Neutral)
    # P20: Kịch bản Thận trọng (Bearish)
    base_case = np.percentile(price_paths, 50, axis=0)
    bull_case = np.percentile(price_paths, 80, axis=0)
    bear_case = np.percentile(price_paths, 20, axis=0)

    # Tính xác suất giá tăng sau N phiên
    final_prices = price_paths[:, -1]
    upward_probability = float(np.mean(final_prices > last_price) * 100)

    # Dự báo ngày tiếp theo
    dates = []
    last_date = df.index[-1] if hasattr(df.index, "strftime") else pd.Timestamp.now()
    if isinstance(last_date, str):
        try:
            last_date = pd.to_datetime(last_date)
        except Exception:
            last_date = pd.Timestamp.now()

    future_dates = []
    curr = last_date
    for _ in range(forecast_days):
        curr = curr + pd.Timedelta(days=1)
        # Bỏ qua thứ 7, CN
        while curr.weekday() >= 5:
            curr = curr + pd.Timedelta(days=1)
        future_dates.append(curr.strftime("%d/%m/%Y"))

    forecast_records = []
    for i in range(1, forecast_days + 1):
        forecast_records.append({
            "date": future_dates[i - 1],
            "day_step": f"+{i} phiên",
            "base_price": round(float(base_case[i]), 2),
            "bull_price": round(float(bull_case[i]), 2),
            "bear_price": round(float(bear_case[i]), 2),
            "expected_pct": round(((base_case[i] - last_price) / last_price) * 100, 2),
        })

    forecast_df = pd.DataFrame(forecast_records)

    target_1w = float(base_case[min(5, forecast_days)])
    target_pct = ((target_1w - last_price) / last_price) * 100

    if upward_probability >= 60:
        outlook = "XU HƯỚNG TĂNG GIÁ (BULLISH)"
        recommendation = "Ưu tiên nắm giữ hoặc gia tăng tỷ trọng ở các nhịp điều chỉnh."
    elif upward_probability <= 40:
        outlook = "XU HƯỚNG ĐIỀU CHỈNH (BEARISH)"
        recommendation = "Cân nhắc hiện thực hóa lợi nhuận hoặc hạ tỷ trọng phòng ngừa rủi ro."
    else:
        outlook = "ĐI NGANG TÍCH LŨY (SIDEWAY)"
        recommendation = "Kiên nhẫn quan sát, chờ đợi tín hiệu bứt phá kèm khối lượng xác nhận."

    return {
        "current_price": last_price,
        "forecast_days": forecast_days,
        "upward_probability": round(upward_probability, 1),
        "target_price_base": round(target_1w, 2),
        "target_price_bull": round(float(bull_case[min(5, forecast_days)]), 2),
        "target_price_bear": round(float(bear_case[min(5, forecast_days)]), 2),
        "expected_return_pct": round(target_pct, 2),
        "outlook": outlook,
        "recommendation": recommendation,
        "forecast_df": forecast_df,
    }
