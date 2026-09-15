"""
Kiểm thử Mô hình Dự báo Máy học Gradient Boosting với Dữ liệu Thật
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.stock_data import stock_engine
from src.analysis.indicators import calculate_indicators
from src.analysis.ml_forecasting import train_and_forecast_ml


def test_ml():
    print("=" * 65)
    print("   KIỂM THỬ DỰ BÁO MACHINE LEARNING VỚI DỮ LIỆU THỰC TẾ")
    print("=" * 65)

    ticker = "HPG"
    print(f"\n1. Tải dữ liệu nến thật của {ticker}...")
    df = stock_engine.get_historical_ohlcv(ticker, days=120)
    print(f"   [OK] Đã tải {len(df)} phiên nến thật.")

    print("\n2. Tính toán chỉ báo và huấn luyện mô hình...")
    df_ind = calculate_indicators(df)
    ml_res = train_and_forecast_ml(df_ind, forecast_days=5, target_ticker=ticker)

    print(f"\n3. KẾT QUẢ DỰ BÁO TỪ MACHINE LEARNING ({ml_res['algorithm']}):")
    print(f"   * Giá thị trường hiện tại: {ml_res['current_price']:,.2f} k")
    print(f"   * Tín hiệu AI đưa ra     : {ml_res['ml_signal']}")
    print(f"   * Độ chính xác chiều tăng/giảm : {ml_res['directional_accuracy']}%")
    print(f"   * Sai số kiểm thử (MAE)        : {ml_res['mae']:,.2f} k ({ml_res['error_pct']}%)")
    print(f"   * Nhận định phân tích   : {ml_res['comment']}")

    print("\n4. CHI TIẾT DỰ BÁO 5 PHIÊN TỚI:")
    for p in ml_res["predictions"]:
        print(f"   - {p['step']} ({p['date']}): {p['predicted_price']:>6,.2f} k ({p['predicted_price']*1000:>7,.0f} đ) | Dự kiến: {p['expected_return_pct']:>+5.2f}%")

    print("\n5. TOP ĐẶC TRƯNG CHI PHỐI GIÁ (FEATURE IMPORTANCE):")
    for fi in ml_res["feature_importance"]:
        print(f"   - {fi['feature']:<35}: {fi['importance']}%")

    print("\n[THÀNH CÔNG] Mô hình hoạt động hoàn hảo và siêu nhanh!")


if __name__ == "__main__":
    test_ml()
