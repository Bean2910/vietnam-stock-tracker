"""
Quản lý Danh sách Cổ phiếu Yêu thích (Watchlist 3-Tier) và Nhật Ký Giao Dịch bằng TinyDB (NoSQL)
Lưu trữ định dạng JSON, không cần SQL server, hỗ trợ CRUD và kiểm tra cảnh báo.
"""
from datetime import datetime
from typing import List, Dict, Optional, Any
from tinydb import TinyDB, Query
from config.settings import TINYDB_PATH, DEFAULT_TICKERS


class TinyDBWatchlistManager:
    def __init__(self, db_path=None):
        self.db_path = db_path or TINYDB_PATH
        self.db = TinyDB(self.db_path, indent=2, encoding="utf-8")
        self.table = self.db.table("watchlist")
        self.TickerQuery = Query()

    def close(self):
        """Đóng kết nối file TinyDB giải phóng tài nguyên"""
        self.db.close()

    def get_all(self) -> List[Dict[str, Any]]:
        """Lấy toàn bộ danh sách cổ phiếu theo dõi"""
        items = self.table.all()
        # Đảm bảo trường tier luôn tồn tại
        for it in items:
            if "tier" not in it:
                it["tier"] = "TIER_1_FOCUS"
        return items

    def get_ticker_list(self) -> List[str]:
        """Lấy danh sách mã ticker thuần (list of uppercase strings)"""
        return [doc["ticker"] for doc in self.table.all() if "ticker" in doc]

    def get_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin chi tiết của một mã"""
        ticker = ticker.strip().upper()
        results = self.table.search(self.TickerQuery.ticker == ticker)
        if results:
            it = results[0]
            if "tier" not in it:
                it["tier"] = "TIER_1_FOCUS"
            return it
        return None

    def add_or_update(
        self,
        ticker: str,
        target_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        note: str = "",
        alert_enabled: bool = True,
        tier: str = "TIER_1_FOCUS",
    ) -> Dict[str, Any]:
        """Thêm mới hoặc cập nhật thông tin mã theo dõi kèm phân loại Tier"""
        ticker = ticker.strip().upper()
        existing = self.get_by_ticker(ticker)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        record = {
            "ticker": ticker,
            "target_price": float(target_price) if target_price else None,
            "stop_loss": float(stop_loss) if stop_loss else None,
            "note": note,
            "alert_enabled": alert_enabled,
            "tier": tier if tier in ["TIER_1_FOCUS", "TIER_2_RADAR", "TIER_3_WARNING"] else "TIER_1_FOCUS",
            "updated_at": now_str,
        }

        if existing:
            self.table.update(record, self.TickerQuery.ticker == ticker)
        else:
            record["added_at"] = now_str
            self.table.insert(record)

        return record

    def update_tier(self, ticker: str, tier: str) -> bool:
        """Cập nhật phân tầng Tier cho cổ phiếu (Focus / Radar / Warning)"""
        ticker = ticker.strip().upper()
        valid_tiers = ["TIER_1_FOCUS", "TIER_2_RADAR", "TIER_3_WARNING"]
        if tier not in valid_tiers:
            return False
        return len(self.table.update({"tier": tier}, self.TickerQuery.ticker == ticker)) > 0

    def remove(self, ticker: str) -> bool:
        """Xóa mã khỏi danh sách theo dõi"""
        ticker = ticker.strip().upper()
        removed_items = self.table.remove(self.TickerQuery.ticker == ticker)
        return len(removed_items) > 0

    def init_defaults_if_empty(self, defaults: Optional[List[str]] = None) -> None:
        """Khởi tạo danh sách mặc định nếu watchlist đang trống"""
        if len(self.table) == 0:
            ticker_list = defaults or DEFAULT_TICKERS
            for idx, sym in enumerate(ticker_list):
                # Phân bổ mẫu các mã vào các Tier khác nhau
                init_tier = "TIER_1_FOCUS" if idx < 3 else ("TIER_2_RADAR" if idx < 5 else "TIER_3_WARNING")
                self.add_or_update(
                    ticker=sym,
                    note=f"Mã mặc định khởi tạo ({sym})",
                    alert_enabled=True,
                    tier=init_tier,
                )

    def check_price_alerts(self, ticker: str, current_price: float) -> List[str]:
        """
        Kiểm tra ngưỡng cảnh báo (Chốt lời / Cắt lỗ) cho một mã cổ phiếu.
        """
        item = self.get_by_ticker(ticker)
        alerts = []
        if not item or not item.get("alert_enabled"):
            return alerts

        target = item.get("target_price")
        stop = item.get("stop_loss")

        if target and current_price >= target:
            alerts.append(
                f"🎯 [CHỐT LỜI] {ticker}: Giá hiện tại ({current_price:,.1f}) đã ĐẠT hoặc VƯỢT giá mục tiêu ({target:,.1f})!"
            )
        if stop and current_price <= stop:
            alerts.append(
                f"⚠️ [CẮT LỖ] {ticker}: Giá hiện tại ({current_price:,.1f}) đã CHẠM hoặc THẤP hơn ngưỡng cắt lỗ ({stop:,.1f})!"
            )

        return alerts


DEFAULT_MOCK_TRADES = [
    {"ticker": "FPT", "strategy": "Breakout Nền Giá", "buy_price": 132.0, "sell_price": 146.0, "shares": 1000, "pnl_pct": 10.6, "result": "WIN", "date": "10/09/2026", "notes": "Vượt đỉnh 50 phiên kèm vol lớn", "is_mock": True},
    {"ticker": "HPG", "strategy": "Bắt Đáy Hỗ Trợ", "buy_price": 27.5, "sell_price": 29.5, "shares": 3000, "pnl_pct": 7.3, "result": "WIN", "date": "05/09/2026", "notes": "Test cung thành công tại MA50", "is_mock": True},
    {"ticker": "SSI", "strategy": "Breakout Nền Giá", "buy_price": 35.0, "sell_price": 33.2, "shares": 2000, "pnl_pct": -5.1, "result": "LOSS", "date": "28/08/2026", "notes": "Gặp cản lớn điều chỉnh cắt lỗ 5%", "is_mock": True},
    {"ticker": "MWG", "strategy": "Đầu Tư Giá Trị", "buy_price": 62.0, "sell_price": 69.5, "shares": 1500, "pnl_pct": 12.1, "result": "WIN", "date": "15/08/2026", "notes": "Kỳ vọng lợi nhuận Bách Hóa Xanh", "is_mock": True},
    {"ticker": "VHM", "strategy": "Bắt Đáy Hỗ Trợ", "buy_price": 44.0, "sell_price": 41.5, "shares": 1000, "pnl_pct": -5.7, "result": "LOSS", "date": "02/08/2026", "notes": "Thủng đáy ngắn hạn kỷ luật cắt lỗ", "is_mock": True},
]


class TinyDBJournalManager:
    """Quản lý dữ liệu Nhật ký giao dịch (Trading Journal)"""
    def __init__(self, db_path=None):
        self.db_path = db_path or TINYDB_PATH
        self.db = TinyDB(self.db_path, indent=2, encoding="utf-8")
        self.table = self.db.table("trading_journal")
        self.meta_table = self.db.table("journal_meta")
        self.JournalQuery = Query()

    def get_all_trades(self) -> List[Dict[str, Any]]:
        """Lấy tất cả các giao dịch đã ghi nhận"""
        docs = self.table.all()
        if not docs and not self.meta_table.all():
            # Chỉ tự động khởi tạo dữ liệu mẫu ở lần chạy đầu tiên
            for t in DEFAULT_MOCK_TRADES:
                self.table.insert(t.copy())
            self.meta_table.insert({"initialized": True})
            docs = self.table.all()

        trades = []
        for d in docs:
            item = dict(d)
            item["doc_id"] = d.doc_id
            trades.append(item)
        return trades

    def add_trade(
        self,
        ticker: str,
        strategy: str,
        buy_price: float,
        sell_price: float,
        shares: int = 1000,
        notes: str = "",
        date_str: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Thêm một giao dịch đã hoàn tất vào nhật ký (dữ liệu thật)"""
        ticker = ticker.strip().upper()
        pnl_pct = round(((sell_price - buy_price) / buy_price) * 100.0, 2)
        result = "WIN" if pnl_pct > 0 else "LOSS"
        date_val = date_str or datetime.now().strftime("%d/%m/%Y")

        trade_doc = {
            "ticker": ticker,
            "strategy": strategy,
            "buy_price": float(buy_price),
            "sell_price": float(sell_price),
            "shares": int(shares),
            "pnl_pct": pnl_pct,
            "pnl_amount": round((sell_price - buy_price) * shares * 1000.0, 0),
            "result": result,
            "date": date_val,
            "notes": notes,
            "is_mock": False,
        }
        doc_id = self.table.insert(trade_doc)
        self.meta_table.upsert({"initialized": True}, Query().initialized.exists())
        trade_doc["doc_id"] = doc_id
        return trade_doc

    def delete_trade_by_id(self, doc_id: int) -> bool:
        """Xóa một bản ghi giao dịch theo ID duy nhất"""
        try:
            self.table.remove(doc_ids=[doc_id])
            return True
        except Exception:
            return False

    def clear_mock_trades(self) -> int:
        """Xóa tất cả các giao dịch mẫu (test data), giữ lại các giao dịch thật"""
        mock_dates = {"10/09/2026", "05/09/2026", "28/08/2026", "15/08/2026", "02/08/2026"}
        mock_syms = {"FPT", "HPG", "SSI", "MWG", "VHM"}
        to_remove = []
        for d in self.table.all():
            if d.get("is_mock") or (d.get("ticker") in mock_syms and d.get("date") in mock_dates):
                to_remove.append(d.doc_id)
        if to_remove:
            self.table.remove(doc_ids=to_remove)
        self.meta_table.upsert({"initialized": True}, Query().initialized.exists())
        return len(to_remove)

    def clear_all_trades(self) -> int:
        """Xóa toàn bộ nhật ký giao dịch (reset trắng)"""
        count = len(self.table)
        self.table.truncate()
        self.meta_table.upsert({"initialized": True}, Query().initialized.exists())
        return count

    def reset_to_default_mock(self) -> int:
        """Khôi phục lại 5 giao dịch mẫu để kiểm thử"""
        for t in DEFAULT_MOCK_TRADES:
            self.table.insert(t.copy())
        self.meta_table.upsert({"initialized": True}, Query().initialized.exists())
        return len(DEFAULT_MOCK_TRADES)

    def delete_trade(self, ticker: str, date_str: str) -> bool:
        """Xóa bản ghi giao dịch theo mã và ngày"""
        removed = self.table.remove((self.JournalQuery.ticker == ticker) & (self.JournalQuery.date == date_str))
        return len(removed) > 0


# Singleton instances
watchlist_db = TinyDBWatchlistManager()
journal_db = TinyDBJournalManager()
