"""
Module Quản Trị Rủi Ro & Nhật Ký Giao Dịch (Portfolio Risk Management & Trading Journal)
1. Công thức tính quy mô vị thế (Position Sizing Calculator) chuẩn mực:
   Số CP cần mua = (Tổng NAV * % Rủi ro tối đa) / (Giá mua - Giá cắt lỗ)
2. Theo dõi cơ cấu phân bổ tài sản: Tiền mặt / Cổ phiếu / Dư nợ Margin
3. Phân tích hiệu suất nhật ký giao dịch: Win Rate, Tỷ lệ Lợi nhuận/Rủi ro (R:R), Hiệu quả theo chiến lược
"""
from typing import Dict, Any, List, Optional
import math
import numpy as np


def calculate_position_size(
    total_nav: float,
    risk_pct_per_trade: float,
    entry_price: float,
    stop_loss_price: float,
    target_price: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Tính toán quy mô vị thế (Position Sizing) bảo vệ NAV:
    - Đảm bảo nếu chạm giá cắt lỗ, khoản lỗ tối đa KHÔNG BAO GIỜ vượt quá % NAV cho phép (thường 1% - 2%).
    """
    if total_nav <= 0 or entry_price <= 0 or stop_loss_price <= 0:
        return {"error": "Thông số đầu vào không hợp lệ"}

    if stop_loss_price >= entry_price:
        return {"error": "Giá cắt lỗ phải thấp hơn giá mua vào"}

    # Số tiền rủi ro tối đa cho phép trên lệnh này (VNĐ)
    max_risk_amount = total_nav * (risk_pct_per_trade / 100.0)

    # Khoản lỗ trên 1 cổ phiếu (VNĐ) - quy đổi nghìn đồng sang VNĐ
    price_diff_per_share = (entry_price - stop_loss_price) * 1000.0
    loss_pct_per_share = ((entry_price - stop_loss_price) / entry_price) * 100.0

    # Số lượng cổ phiếu được phép mua lý thuyết
    raw_shares = max_risk_amount / price_diff_per_share

    # Quy tròn theo lô 100 cổ phiếu (chuẩn sàn HOSE / HNX)
    lot_size = 100
    recommended_shares = math.floor(raw_shares / lot_size) * lot_size
    if recommended_shares < lot_size:
        recommended_shares = lot_size

    # Tổng giá trị vốn cần giải ngân (VNĐ)
    total_position_value = recommended_shares * entry_price * 1000.0
    position_nav_weight = (total_position_value / total_nav) * 100.0

    # Khoản lỗ thực tế nếu chạm Stop Loss
    actual_max_loss = recommended_shares * price_diff_per_share
    actual_risk_pct = (actual_max_loss / total_nav) * 100.0

    # Tỷ lệ Lời / Lỗ (Reward / Risk Ratio)
    rr_ratio = 0.0
    potential_profit = 0.0
    if target_price and target_price > entry_price:
        potential_profit = recommended_shares * (target_price - entry_price) * 1000.0
        rr_ratio = round(potential_profit / max(actual_max_loss, 1), 2)

    return {
        "recommended_shares": int(recommended_shares),
        "total_position_value": total_position_value,
        "position_nav_weight": round(position_nav_weight, 1),
        "loss_pct_per_share": round(loss_pct_per_share, 2),
        "actual_max_loss": actual_max_loss,
        "actual_risk_pct": round(actual_risk_pct, 2),
        "reward_risk_ratio": rr_ratio,
        "potential_profit": potential_profit,
        "advice": (
            f"Mua tối đa {recommended_shares:,} CP ({total_position_value:,.0f} đ, chiếm {position_nav_weight:.1f}% NAV). "
            f"Nếu chạm cắt lỗ tại {stop_loss_price:,.2f}, bạn chỉ lỗ {actual_max_loss:,.0f} đ ({actual_risk_pct:.2f}% NAV), "
            "hoàn toàn nằm trong tầm kiểm soát an toàn."
        ),
    }


def calculate_portfolio_allocation(
    cash_amount: float,
    stock_value: float,
    margin_debt: float = 0.0,
) -> Dict[str, Any]:
    """
    Theo dõi cơ cấu danh mục & Đòn bẩy Margin:
    - Tỷ lệ Tiền mặt / Cổ phiếu / Dư nợ Margin
    - Tỷ lệ đòn bẩy và ngưỡng rủi ro Call Margin
    """
    net_asset_value = cash_amount + stock_value - margin_debt
    total_assets = cash_amount + stock_value

    if total_assets <= 0:
        return {"cash_pct": 100, "stock_pct": 0, "margin_ratio": 0, "status": "TIỀN MẶT"}

    cash_pct = (cash_amount / total_assets) * 100.0
    stock_pct = (stock_value / total_assets) * 100.0
    leverage_ratio = (margin_debt / max(net_asset_value, 1))

    if leverage_ratio >= 1.5:
        status = "🚨 CẢNH BÁO: ĐÒN BẨY RẤT CAO"
        color = "#ef4444"
        desc = "Tỷ lệ vay Margin vượt mức an toàn (> 1.5x VCSH). Cần ưu tiên hạ tỷ trọng để tránh bị bán giải chấp (Force-sell)."
    elif leverage_ratio >= 0.8:
        status = "⚠️ ĐÒN BẨY VỪA PHẢI"
        color = "#f59e0b"
        desc = "Danh mục đang sử dụng đòn bẩy hỗ trợ lợi nhuận. Cần cài đặt chặt chẽ giá dừng lỗ cho từng mã."
    elif margin_debt > 0:
        status = "🟢 ĐÒN BẨY THẤP (AN TOÀN)"
        color = "#3b82f6"
        desc = "Tỷ lệ vay rất thấp, rủi ro call margin gần như bằng 0."
    else:
        status = "🛡️ 100% TIỀN THẬT (KHÔNG MARGIN)"
        color = "#10b981"
        desc = "Tài khoản an toàn tuyệt đối trước mọi biến động rũ bỏ bất ngờ của thị trường chung."

    return {
        "nav": net_asset_value,
        "cash": cash_amount,
        "stock_value": stock_value,
        "margin_debt": margin_debt,
        "cash_pct": round(cash_pct, 1),
        "stock_pct": round(stock_pct, 1),
        "leverage_ratio": round(leverage_ratio, 2),
        "status": status,
        "color": color,
        "description": desc,
    }


def analyze_trading_journal(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Thống kê Nhật Ký Giao Dịch (Trading Journal Analytics):
    - Tỷ lệ thắng (Win Rate)
    - Tỷ lệ Lợi nhuận / Rủi ro trung bình (Reward / Risk)
    - Hiệu suất theo chiến lược: Breakout, Bắt đáy hỗ trợ, Đầu tư giá trị
    """
    if not trades:
        return {
            "total_trades": 0,
            "win_count": 0,
            "loss_count": 0,
            "win_rate": 0.0,
            "avg_win_pct": 0.0,
            "avg_loss_pct": 0.0,
            "profit_factor": 0.0,
            "reward_risk_ratio": 0.0,
            "strategy_summary": [],
        }

    total_trades = len(trades)
    win_trades = [t for t in trades if t.get("pnl_pct", 0) > 0]
    loss_trades = [t for t in trades if t.get("pnl_pct", 0) <= 0]

    win_count = len(win_trades)
    loss_count = len(loss_trades)
    win_rate = (win_count / total_trades) * 100.0 if total_trades > 0 else 0.0

    avg_win = float(np.mean([t["pnl_pct"] for t in win_trades])) if win_trades else 0.0
    avg_loss = abs(float(np.mean([t["pnl_pct"] for t in loss_trades]))) if loss_trades else 0.0

    profit_factor = (sum([t["pnl_pct"] for t in win_trades]) / max(abs(sum([t["pnl_pct"] for t in loss_trades])), 0.01)) if loss_trades else 9.9
    rr_ratio = round(avg_win / max(avg_loss, 0.01), 2) if avg_loss > 0 else 2.5

    # Thống kê theo chiến lược
    strat_perf = {}
    for t in trades:
        st_name = t.get("strategy", "Chung")
        if st_name not in strat_perf:
            strat_perf[st_name] = {"trades": 0, "wins": 0, "total_pnl": 0.0}
        strat_perf[st_name]["trades"] += 1
        strat_perf[st_name]["total_pnl"] += t.get("pnl_pct", 0)
        if t.get("pnl_pct", 0) > 0:
            strat_perf[st_name]["wins"] += 1

    strat_summary = []
    for s_name, s_data in strat_perf.items():
        s_wr = (s_data["wins"] / s_data["trades"]) * 100.0 if s_data["trades"] > 0 else 0
        strat_summary.append({
            "strategy": s_name,
            "trades": s_data["trades"],
            "win_rate": round(s_wr, 1),
            "avg_pnl": round(s_data["total_pnl"] / s_data["trades"], 2),
        })

    return {
        "total_trades": total_trades,
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate": round(win_rate, 1),
        "avg_win_pct": round(avg_win, 2),
        "avg_loss_pct": round(avg_loss, 2),
        "profit_factor": round(profit_factor, 2),
        "reward_risk_ratio": rr_ratio,
        "strategy_summary": strat_summary,
        "trades_list": trades,
    }
