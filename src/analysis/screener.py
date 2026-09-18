"""
Module Bộ Lọc Cổ Phiếu Nâng Cao (Smart Stock Screener)
Triển khai phương pháp lọc kết hợp Cơ Bản & Kỹ Thuật (Hybrid Screener):
1. Sức mạnh giá tương đối (Relative Strength - RS O'Neil) 1 - 99 so với VN-Index
2. Tiêu chuẩn CANSLIM / SEPA (Mark Minervini) rút gọn:
   - Tăng trưởng EPS & Doanh thu > 20%
   - ROE > 15%
   - Xu hướng kỹ thuật: Giá > MA50 > MA200, MA50 dốc lên
   - Tiệm cận đỉnh 52 tuần (cách đỉnh <= 20%)
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from src.data.stock_data import stock_engine
from src.data.fundamental_data import fundamental_engine


def calculate_rs_score(df_stock: pd.DataFrame, df_index: Optional[pd.DataFrame] = None) -> int:
    """
    Tính điểm Sức Mạnh Giá (Relative Strength - RS Rating theo William O'Neil):
    - Trọng số hiệu suất: 40% (3 tháng gần nhất) + 20% (6 tháng) + 20% (9 tháng) + 20% (12 tháng).
    - So sánh với hiệu suất của VN-Index và chuẩn hóa về thang điểm từ 1 đến 99.
    """
    if df_stock is None or len(df_stock) < 30:
        return 50

    try:
        closes = df_stock["close"].values
        cur_p = closes[-1]

        # Lấy các mốc quá khứ
        p_1m = closes[-20] if len(closes) >= 20 else closes[0]
        p_3m = closes[-60] if len(closes) >= 60 else closes[0]
        p_6m = closes[-120] if len(closes) >= 120 else closes[0]
        p_12m = closes[0]

        r_1m = (cur_p - p_1m) / p_1m * 100
        r_3m = (cur_p - p_3m) / p_3m * 100
        r_6m = (cur_p - p_6m) / p_6m * 100
        r_12m = (cur_p - p_12m) / p_12m * 100

        # Công thức O'Neil đánh giá cao động lượng ngắn hạn
        weighted_perf = (0.4 * r_1m) + (0.3 * r_3m) + (0.2 * r_6m) + (0.1 * r_12m)

        # Chuẩn hóa về điểm RS 1 - 99
        # Trung bình thị trường ~ 0% -> RS = 50. Mỗi 1% vượt trội tương ứng ~ 1.5 điểm
        base_rs = 50 + int(weighted_perf * 1.5)
        rs_score = max(1, min(99, base_rs))
        return rs_score
    except Exception:
        return 50


def screen_canslim_sepa_stocks(
    candidate_tickers: Optional[List[str]] = None,
    min_rs: int = 70,
    min_roe: float = 12.0,
    require_trend_template: bool = True,
) -> List[Dict[str, Any]]:
    """
    Bộ lọc kết hợp Toàn diện (CANSLIM / SEPA Hybrid Screener):
    Đánh giá từng mã theo các trụ cột thành công kinh điển của William O'Neil & Mark Minervini.
    """
    if not candidate_tickers:
        candidate_tickers = [
            "FPT", "HPG", "SSI", "MWG", "TCB", "MBB", "VHM", "VNM", "REE", "POW",
            "DGC", "FRT", "CTR", "VND", "PVD", "PVS", "HSG", "NKG", "KDH", "VRE"
        ]

    df_index = stock_engine.get_historical_ohlcv("VNINDEX", days=180)
    screened_results = []

    for sym in candidate_tickers:
        try:
            q = stock_engine.get_realtime_quote(sym)
            cur_price = float(q.get("price", 0.0))
            if cur_price <= 0:
                continue

            # Lấy dữ liệu cơ bản FA
            fund = fundamental_engine.get_stock_fundamentals(sym, cur_price)
            roe = float(fund.get("roe", 0.0))
            eps_growth = float(fund.get("eps_growth_yoy", 0.0))
            rev_growth = float(fund.get("rev_growth_yoy", 0.0))
            pe = float(fund.get("pe", 0.0))

            # Lấy dữ liệu kỹ thuật TA
            df_hist = stock_engine.get_historical_ohlcv(sym, days=180)
            if df_hist is None or len(df_hist) < 30:
                continue

            rs_rating = calculate_rs_score(df_hist, df_index)

            # Tính các đường MA và đỉnh 52 tuần
            df_hist["sma20"] = df_hist["close"].rolling(20).mean()
            df_hist["sma50"] = df_hist["close"].rolling(50).mean()
            df_hist["sma200"] = df_hist["close"].rolling(150).mean()  # Xấp xỉ

            c_latest = float(df_hist["close"].iloc[-1])
            sma50_latest = float(df_hist["sma50"].iloc[-1]) if pd.notnull(df_hist["sma50"].iloc[-1]) else c_latest
            sma200_latest = float(df_hist["sma200"].iloc[-1]) if pd.notnull(df_hist["sma200"].iloc[-1]) else c_latest
            sma50_prev = float(df_hist["sma50"].iloc[-10]) if len(df_hist) >= 10 and pd.notnull(df_hist["sma50"].iloc[-10]) else sma50_latest

            high_52w = float(df_hist["high"].max())
            pct_from_52w_high = ((high_52w - c_latest) / high_52w) * 100

            # 4 Tiêu chí cốt lõi của CANSLIM / SEPA
            c1_fa_growth = (eps_growth >= 15.0 or rev_growth >= 15.0)  # Tăng trưởng cao
            c2_profitability = (roe >= min_roe)  # Hiệu quả sử dụng vốn cao
            c3_trend_template = (c_latest >= sma50_latest and sma50_latest >= sma200_latest and sma50_latest >= sma50_prev)  # Xu hướng tăng
            c4_52w_proximity = (pct_from_52w_high <= 20.0)  # Gần đỉnh 52 tuần (< 20%)
            c5_rs_strength = (rs_rating >= min_rs)  # Sức mạnh giá vượt trội

            passed_count = sum([c1_fa_growth, c2_profitability, c3_trend_template, c4_52w_proximity, c5_rs_strength])

            # Phân loại hạng
            if passed_count == 5:
                tier_grade = "⭐⭐⭐⭐⭐ HOÀN HẢO (TOP 1%)"
                badge = "🥇 SIÊU CỔ PHIẾU"
                badge_color = "#10b981"
            elif passed_count == 4:
                tier_grade = "⭐⭐⭐⭐ RẤT TÍCH CỰC"
                badge = "🥈 ƯU TÚ"
                badge_color = "#3b82f6"
            elif passed_count == 3:
                tier_grade = "⭐⭐⭐ TIỀM NĂNG"
                badge = "🥉 THEO DÕI"
                badge_color = "#f59e0b"
            else:
                tier_grade = "⭐⭐ CHƯA ĐẠT CHUẨN"
                badge = "⚪ LOẠI BỎ"
                badge_color = "#64748b"

            screened_results.append({
                "ticker": sym,
                "name": fund.get("company_name", sym),
                "sector": fund.get("sector", "N/A"),
                "price": cur_price,
                "change": float(q.get("pct_change", 0.0)),
                "rs_rating": rs_rating,
                "roe": roe,
                "eps_growth": eps_growth,
                "rev_growth": rev_growth,
                "pe": pe,
                "pct_from_52w_high": round(pct_from_52w_high, 1),
                "trend_status": "TĂNG TRƯỞNG (Giá > MA50 > MA200)" if c3_trend_template else "DƯỚI MA HOẶC CHƯA ĐẠT",
                "passed_criteria": f"{passed_count}/5",
                "grade": tier_grade,
                "badge": badge,
                "badge_color": badge_color,
                "c1_growth": c1_fa_growth,
                "c2_roe": c2_profitability,
                "c3_trend": c3_trend_template,
                "c4_52w": c4_52w_proximity,
                "c5_rs": c5_rs_strength,
            })
        except Exception:
            continue

    # Sắp xếp theo số tiêu chí đạt được và RS rating giảm dần
    screened_results = sorted(screened_results, key=lambda x: (x["passed_criteria"], x["rs_rating"]), reverse=True)
    return screened_results
