import sys
from pathlib import Path

# Cấu hình UTF-8 cho console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Đảm bảo đường dẫn import được nhận diện
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.tinydb_manager import TinyDBWatchlistManager
from src.data.stock_data import StockDataEngine
from src.analysis.indicators import calculate_indicators, generate_technical_signals
from src.analysis.forecasting import forecast_price_trend
from src.reporting.report_builder import generate_ticker_report_markdown


def test_all():
    print("=== BẮT ĐẦU KIỂM THỬ HỆ THỐNG STOCK TRACKER ===")

    # 1. Kiểm thử TinyDB Watchlist
    print("\n1. Kiểm thử TinyDB Watchlist...")
    test_db_path = Path(__file__).resolve().parent / "test_watchlist.json"
    db = TinyDBWatchlistManager(db_path=test_db_path)
    
    # Thêm mã
    db.add_or_update("FPT", target_price=145.0, stop_loss=120.0, note="Kiểm tra FPT")
    db.add_or_update("HPG", target_price=35.0, stop_loss=25.0, note="Kiểm tra HPG")
    
    all_items = db.get_all()
    assert len(all_items) >= 2, f"Kỳ vọng ít nhất 2 mã, nhưng nhận {len(all_items)}"
    print(f"   [PASS] Đã thêm thành công: {[x['ticker'] for x in all_items]}")

    # Kiểm tra Alert
    alerts = db.check_price_alerts("FPT", 146.0)
    assert len(alerts) > 0, "Kỳ vọng kích hoạt cảnh báo chốt lời FPT"
    print(f"   [PASS] Kích hoạt cảnh báo: {alerts[0]}")

    # Đóng db và xóa file test
    db.close()
    if test_db_path.exists():
        test_db_path.unlink()

    # 2. Kiểm thử Data Engine
    print("\n2. Kiểm thử Stock Data Engine...")
    engine = StockDataEngine()
    quote = engine.get_realtime_quote("HPG")
    assert "price" in quote and quote["price"] > 0
    print(f"   [PASS] Giá HPG: {quote['price']:,.1f} | Thay đổi: {quote['change']:+,.1f} ({quote['pct_change']:+.2f}%)")

    # Lịch sử nến
    df = engine.get_historical_ohlcv("HPG", days=60)
    assert df is not None and len(df) > 0
    print(f"   [PASS] Nạp thành công {len(df)} phiên nến OHLCV")

    # 3. Kiểm thử Chỉ báo Kỹ thuật (Indicators)
    print("\n3. Kiểm thử Chỉ báo Kỹ thuật & Tín hiệu...")
    df_ind = calculate_indicators(df)
    assert "SMA20" in df_ind.columns and "RSI14" in df_ind.columns and "MACD" in df_ind.columns
    signals = generate_technical_signals(df_ind)
    print(f"   [PASS] Tín hiệu phân tích: {signals['action']} (Điểm số: {signals['score']}/100)")
    print(f"   [PASS] Số lý do đánh giá: {len(signals['reasons'])}")

    # 4. Kiểm thử Dự báo Xu hướng (Forecasting)
    print("\n4. Kiểm thử Dự báo Xu hướng Giá (Monte Carlo)...")
    forecast = forecast_price_trend(df_ind, forecast_days=7)
    assert "target_price_base" in forecast
    print(f"   [PASS] Định hướng: {forecast['outlook']} | Xác suất tăng: {forecast['upward_probability']}%")
    print(f"   [PASS] Giá mục tiêu cơ sở: {forecast['target_price_base']:,.1f} VND")

    # 5. Kiểm thử Sinh Báo cáo
    print("\n5. Kiểm thử Sinh Báo Cáo...")
    md = generate_ticker_report_markdown("HPG", quote, signals, forecast)
    assert "BÁO CÁO PHÂN TÍCH" in md
    print("   [PASS] Sinh báo cáo thành công")

    print("\n🎉 TẤT CẢ CÁC BÀI KIỂM THỬ ĐỀU HOÀN THÀNH VÀ ĐẠT TIÊU CHUẨN!")


if __name__ == "__main__":
    test_all()
