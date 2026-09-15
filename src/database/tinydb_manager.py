"""
Quản lý Danh sách Cổ phiếu Yêu thích (Watchlist) và Cảnh báo Giá bằng TinyDB (NoSQL)
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
        """Lấy toàn bộ danh sách cổ phiếu yêu thích"""
        return self.table.all()

    def get_ticker_list(self) -> List[str]:
        """Lấy danh sách mã ticker thuần (list of uppercase strings)"""
        return [doc["ticker"] for doc in self.table.all() if "ticker" in doc]

    def get_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin chi tiết của một mã"""
        ticker = ticker.strip().upper()
        results = self.table.search(self.TickerQuery.ticker == ticker)
        return results[0] if results else None

    def add_or_update(
        self,
        ticker: str,
        target_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        note: str = "",
        alert_enabled: bool = True,
    ) -> Dict[str, Any]:
        """Thêm mới hoặc cập nhật thông tin mã theo dõi"""
        ticker = ticker.strip().upper()
        existing = self.get_by_ticker(ticker)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        record = {
            "ticker": ticker,
            "target_price": float(target_price) if target_price else None,
            "stop_loss": float(stop_loss) if stop_loss else None,
            "note": note,
            "alert_enabled": alert_enabled,
            "updated_at": now_str,
        }

        if existing:
            self.table.update(record, self.TickerQuery.ticker == ticker)
        else:
            record["added_at"] = now_str
            self.table.insert(record)

        return record

    def remove(self, ticker: str) -> bool:
        """Xóa mã khỏi danh sách theo dõi"""
        ticker = ticker.strip().upper()
        removed_items = self.table.remove(self.TickerQuery.ticker == ticker)
        return len(removed_items) > 0

    def init_defaults_if_empty(self, defaults: Optional[List[str]] = None) -> None:
        """Khởi tạo danh sách mặc định nếu watchlist đang trống"""
        if len(self.table) == 0:
            ticker_list = defaults or DEFAULT_TICKERS
            for sym in ticker_list:
                self.add_or_update(
                    ticker=sym,
                    note=f"Mã mặc định khởi tạo ({sym})",
                    alert_enabled=True,
                )

    def check_price_alerts(self, ticker: str, current_price: float) -> List[str]:
        """
        Kiểm tra ngưỡng cảnh báo (Chốt lời / Cắt lỗ) cho một mã cổ phiếu.
        Trả về danh sách các cảnh báo kích hoạt.
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


# Singleton instance để dùng toàn app
watchlist_db = TinyDBWatchlistManager()
