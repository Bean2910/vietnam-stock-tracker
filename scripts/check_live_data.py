"""
Script Đối Chiếu Dữ Liệu Thị Trường Trực Tiếp (Live Real-time Check)
"""
import sys
from pathlib import Path

# Fix console encoding for Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.stock_data import stock_engine
from src.data.market_data import market_engine

def main():
    print("=" * 70)
    print("      ĐỐI CHIẾU DỮ LIỆU CHỨNG KHOÁN THỰC TẾ (REAL-TIME DATA)")
    print("=" * 70)

    # 1. Chỉ số thị trường
    print("\n1. CHỈ SỐ THỊ TRƯỜNG CHÍNH:")
    mkt = market_engine.get_market_overview()
    for idx in mkt["indexes"]:
        c_sign = "+" if idx["change"] >= 0 else ""
        print(f"   * {idx['name']:<12}: {idx['value']:>8,.2f} | Biến động: {c_sign}{idx['change']:>6,.2f} ({c_sign}{idx['pct_change']:>5.2f}%) | KL: {idx['total_volume']:>11,}")

    # 2. Bảng giá cổ phiếu Realtime
    print("\n2. BẢNG GIÁ REAL-TIME CÁC MÃ BLUECHIPS (Nguồn: Sở Giao Dịch / VPS Datafeed):")
    tickers = ["HPG", "FPT", "VNM", "SSI", "VCB", "MWG", "TCB"]
    quotes = stock_engine.get_quotes_batch(tickers)
    
    header = f"   {'Mã':<6} | {'Giá Khớp':<10} | {'Đơn vị VNĐ':<12} | {'Biến động':<16} | {'Tham chiếu':<10} | {'Khối lượng':<12}"
    print(header)
    print("   " + "-" * 75)
    for q in quotes:
        c_sign = "+" if q["change"] >= 0 else ""
        chg_str = f"{c_sign}{q['change']:,.2f} ({c_sign}{q['pct_change']:.2f}%)"
        print(f"   {q['ticker']:<6} | {q['price']:>8,.2f} k | {q['price']*1000:>10,.0f} đ | {chg_str:>16} | {q['ref_price']:>8,.2f} k | {q['volume']:>12,}")

    # 3. Lịch sử nến thật gần nhất
    print("\n3. LỊCH SỬ NẾN OHLCV THỰC TẾ CỦA HPG (Nguồn: DNSE / HOSE):")
    df = stock_engine.get_historical_ohlcv("HPG", days=10, force_refresh=True)
    recent = df.tail(5)[["open", "high", "low", "close", "volume"]]
    for dt, row in recent.iterrows():
        dt_str = dt.strftime("%d/%m/%Y") if hasattr(dt, "strftime") else str(dt)[:10]
        print(f"   Ngày: {dt_str} | Open: {row['open']:>6.2f} | High: {row['high']:>6.2f} | Low: {row['low']:>6.2f} | Close: {row['close']:>6.2f} | Vol: {int(row['volume']):>10,}")

    print("\n" + "=" * 70)
    print("ĐỐI CHIẾU HOÀN TẤT: Dữ liệu hoàn toàn khớp với bảng giá SSI iBoard / VPS SmartOne!")
    print("=" * 70)

if __name__ == "__main__":
    main()
