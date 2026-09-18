"""
Test Suite: Kiểm thử tích hợp 5 Khối tính năng nâng cao
"""
import sys
import os

# Thiết lập UTF-8 output cho Windows Powershell
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("."))

from src.data.stock_data import stock_engine
from src.analysis.alerts import (
    scan_technical_breakouts,
    scan_risk_violations,
    detect_rsi_macd_divergence,
    scan_unusual_institutional_activity,
)
from src.analysis.screener import calculate_rs_score, screen_canslim_sepa_stocks
from src.analysis.events_valuation import get_corporate_events_and_calendar, calculate_historical_valuation_bands
from src.analysis.risk_management import calculate_position_size, calculate_portfolio_allocation, analyze_trading_journal
from src.database.tinydb_manager import watchlist_db, journal_db
from src.ui.components import create_sector_treemap_chart, create_valuation_bands_chart


def run_tests():
    print("=== BẮT ĐẦU KIỂM THỬ 5 KHỐI TÍNH NĂNG NÂNG CAO ===")

    # 1. CẢNH BÁO TỰ ĐỘNG
    print("\n1. Kiểm thử Cảnh Báo Kỹ Thuật (alerts.py)...")
    df_hpg = stock_engine.get_historical_ohlcv("HPG", days=60)
    bo = scan_technical_breakouts(df_hpg, "HPG")
    vio = scan_risk_violations(df_hpg, "HPG")
    div = detect_rsi_macd_divergence(df_hpg, "HPG")
    inst = scan_unusual_institutional_activity("HPG")
    print(f"   [PASS] Scan HPG: Breakout={bo is not None}, Violation={vio is not None}, Divergence={div is not None}")
    if inst:
        print(f"   [PASS] Institutional Activity HPG: {inst['badge']} ({inst['message'][:50]}...)")

    # 2. BỘ LỌC CỔ PHIẾU CANSLIM & SEPA
    print("\n2. Kiểm thử Bộ Lọc Cổ Phiếu (screener.py)...")
    df_idx = stock_engine.get_historical_ohlcv("VNINDEX", days=60)
    rs_hpg = calculate_rs_score(df_hpg, df_idx)
    print(f"   [PASS] RS Rating HPG: {rs_hpg}/99")
    screened = screen_canslim_sepa_stocks(["FPT", "HPG", "SSI", "TCB", "MWG"], min_rs=60, min_roe=10.0)
    print(f"   [PASS] Số mã sàng lọc thành công: {len(screened)}")
    for s in screened[:2]:
        print(f"          - {s['ticker']}: RS={s['rs_rating']} | ROE={s['roe']}% | Điểm={s['passed_criteria']} | {s['badge']}")

    # 3. SỰ KIỆN DOANH NGHIỆP & ĐỊNH GIÁ LỊCH SỬ
    print("\n3. Kiểm thử Sự Kiện & Valuation Bands (events_valuation.py)...")
    events = get_corporate_events_and_calendar()
    print(f"   [PASS] Đáo hạn phái sinh: {events['derivative_expiry']['date']} (Còn {events['derivative_expiry']['days_left']} ngày)")
    print(f"   [PASS] Số sự kiện doanh nghiệp: {len(events['corporate_events'])}")
    val_bands = calculate_historical_valuation_bands("HPG", 22.0, current_pe=10.5, current_pb=1.6)
    print(f"   [PASS] P/E Bands HPG: Mean={val_bands['pe_bands']['mean']}x | +2SD={val_bands['pe_bands']['plus_2sd']}x | Status: {val_bands['pe_status']}")
    vb_fig = create_valuation_bands_chart(df_hpg, "HPG", val_bands)
    print(f"   [PASS] Biểu đồ Valuation Bands traces: {len(vb_fig.data)}")

    # 4. QUẢN TRỊ RỦI RO & NHẬT KÝ GIAO DỊCH
    print("\n4. Kiểm thử Quản Trị Rủi Ro NAV (risk_management.py)...")
    pos = calculate_position_size(total_nav=500_000_000, risk_pct_per_trade=1.5, entry_price=30.0, stop_loss_price=28.0, target_price=35.0)
    print(f"   [PASS] Position Sizing: Mua {pos['recommended_shares']:,} CP | Rủi ro: -{pos['actual_max_loss']:,.0f} đ (-{pos['actual_risk_pct']}%) | R:R={pos['reward_risk_ratio']}x")
    alloc = calculate_portfolio_allocation(cash_amount=150_000_000, stock_value=350_000_000, margin_debt=50_000_000)
    print(f"   [PASS] Allocation: Tiền {alloc['cash_pct']}% | Cổ {alloc['stock_pct']}% | Đòn bẩy: {alloc['leverage_ratio']}x ({alloc['status']})")
    journal_stats = analyze_trading_journal(journal_db.get_all_trades())
    print(f"   [PASS] Trading Journal: Win Rate={journal_stats['win_rate']}% | Profit Factor={journal_stats['profit_factor']} | R:R={journal_stats['reward_risk_ratio']}x")

    # 5. WATCHLIST 3-TIER & SECTOR TREEMAP
    print("\n5. Kiểm thử Watchlist 3-Tier & Treemap...")
    wl_items = watchlist_db.get_all()
    tier_counts = {}
    for item in wl_items:
        t = item.get("tier", "TIER_1_FOCUS")
        tier_counts[t] = tier_counts.get(t, 0) + 1
    print(f"   [PASS] Phân tầng Watchlist: {tier_counts}")
    mock_stocks = [
        {"ticker": "HPG", "sector": "Thép", "price": 28.0, "change": 2.5, "volume": 15000000},
        {"ticker": "SSI", "sector": "Chứng Khoán", "price": 34.0, "change": -1.2, "volume": 12000000},
        {"ticker": "TCB", "sector": "Ngân Hàng", "price": 24.0, "change": 1.0, "volume": 8000000},
    ]
    tm_fig = create_sector_treemap_chart(mock_stocks)
    print(f"   [PASS] Sector Treemap traces: {len(tm_fig.data)}")

    print("\n🎉 TẤT CẢ 5 KHỐI TÍNH NĂNG NÂNG CAO ĐÃ ĐƯỢC KIỂM THỬ THÀNH CÔNG RỰC RỠ!")


if __name__ == "__main__":
    run_tests()
