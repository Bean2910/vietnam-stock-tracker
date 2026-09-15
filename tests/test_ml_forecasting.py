"""
Kiểm thử Hệ thống Dự báo Đa Mô hình với Dữ liệu Thật
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.stock_data import stock_engine
from src.analysis.indicators import calculate_indicators
from src.analysis.ml_forecasting import train_multi_model_forecast


def test_multi_model():
    print("=" * 70)
    print("   KIỂM THỬ HỆ THỐNG DỰ BÁO ĐA MÔ HÌNH (MULTI-MODEL ENSEMBLE)")
    print("=" * 70)

    ticker = "HPG"
    print(f"\n1. Tải nến lịch sử thực tế của {ticker}...")
    df = stock_engine.get_historical_ohlcv(ticker, days=120)
    print(f"   [OK] Đã tải {len(df)} phiên nến thật.")

    print("\n2. Huấn luyện và dự báo đa mô hình...")
    df_ind = calculate_indicators(df)
    res = train_multi_model_forecast(df_ind, forecast_days=5, target_ticker=ticker)

    print(f"\n3. ĐỒNG THUẬN TỔNG HỢP: {res['consensus_view']}")
    print(f"   * {res['consensus_desc']}")

    print("\n4. SO SÁNH GIÁ DỰ BÁO CỦA CÁC MÔ HÌNH CHO 5 PHIÊN TỚI:")
    for m_name, m_info in res["models"].items():
        print(f"   * {m_name:<32}: Giá T+5 = {m_info['final_price']:>6,.2f} k | Biến động: {m_info['expected_return']:>+5.2f}%")

    print("\n5. BẢNG CHI TIẾT TỪNG PHIÊN:")
    for row in res["comparison_table"]:
        print(f"   - {row['Phiên']} ({row['Ngày']}): GB={row['Gradient Boosting']} | RF={row['Random Forest']} | Tech={row['Quán Tính Kỹ Thuật']} | Consensus={row['Đồng Thuận AI']}")

    assert len(res["models"]) == 5, "Kỳ vọng 5 mô hình dự báo"
    print("\n[THÀNH CÔNG] Đã kiểm thử thành công hệ thống đối chiếu đa mô hình!")


if __name__ == "__main__":
    test_multi_model()
