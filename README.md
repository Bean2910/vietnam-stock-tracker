# 📈 Vietnam Stock Tracker & Forecast (VN-Stock)

Hệ thống theo dõi bảng giá tức thì, quản lý danh sách cổ phiếu yêu thích (Watchlist NoSQL), phân tích kỹ thuật và dự báo xu hướng giá cho thị trường chứng khoán Việt Nam.

---

## 🌟 Tính Năng Nổi Bật

1. **Bảng Giá Tức Thì (Real-time Market Data)**:
   - Theo dõi sát sao các chỉ số VN-Index, VN30, HNX, UPCoM, độ rộng thị trường và thanh khoản.
   - Bảng giá realtime các mã cổ phiếu với đầy đủ mức giá Khớp, Tham chiếu, Trần, Sàn, Khối lượng.

2. **Quản Lý Danh Mục Yêu Thích (Watchlist - TinyDB NoSQL)**:
   - Lưu trữ dạng Document NoSQL chuẩn JSON qua thư viện `TinyDB` (không phụ thuộc SQL).
   - Thiết lập giá mục tiêu (Take Profit) và ngưỡng cắt lỗ (Stop Loss).
   - Tự động kiểm tra và thông báo khi cổ phiếu chạm ngưỡng cảnh báo.

3. **Phân Tích Kỹ Thuật & Tín Hiệu Mua/Bán (Technical Indicators)**:
   - Biểu đồ nến Nhật tương tác đa khung thời gian (Plotly).
   - Bộ chỉ báo: SMA 20/50/200, EMA, MACD, RSI(14), Bollinger Bands, Khối lượng TB 20 phiên.
   - Tự động chấm điểm kỹ thuật và đưa ra khuyến nghị: `TÍCH CỰC / NÊN MUA`, `TRUNG LẬP`, `TIÊU CỰC / NÊN BÁN`.

4. **Dự Báo Máy Học AI (Gradient Boosting / LightGBM)**:
   - Mô hình học máy huấn luyện trực tiếp trên chuỗi nến lịch sử thực tế của cổ phiếu.
   - Trích xuất các đặc trưng tài chính định lượng: Lợi suất trễ (Return lags), độ lệch đường MA, xung lực RSI/MACD, đột biến khối lượng.
   - Dự báo giá cụ thể 5 phiên kế tiếp (T+1 đến T+5) và phân tích tỷ lệ đóng góp của các yếu tố chi phối (Feature Importance).
   - Tốc độ tính toán siêu nhanh (< 0.5s), không làm nặng máy hay chậm giao diện.

5. **Mô Phỏng Kịch Bản Xác Suất Monte Carlo**:
   - Dự báo kịch bản giá 7 - 15 phiên dựa trên độ biến động lịch sử (Volatility).
   - 500 kịch bản ngẫu nhiên đo lường dải tin cậy: Lạc quan (+80%), Cơ sở (Base), Thận trọng (-20%).

6. **Xuất Báo Cáo Phân Tích (Reporting Engine)**:
   - Xuất file báo cáo phân tích định dạng **HTML** giao diện sang trọng hoặc **Markdown** để lưu trữ/in ấn/chia sẻ.

---

## 🚀 Hướng Dẫn Khởi Chạy Nhanh

### 1. Kích hoạt môi trường ảo
```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Cấu hình file `.env`
Mở file `.env` để điều chỉnh tần suất tự động làm mới hoặc danh mục mã mặc định nếu muốn:
```env
AUTO_REFRESH_INTERVAL=10
DEFAULT_TICKERS=VNM,HPG,FPT,SSI,MWG,TCB,VHM,VIC
```

### 3. Khởi chạy Ứng dụng Dashboard
```powershell
.\.venv\Scripts\streamlit.exe run app.py
```
Ứng dụng sẽ tự động mở tại trình duyệt: `http://localhost:8501`.

---

## 📁 Cấu Trúc Dự Án

- `app.py`: Giao diện chính của ứng dụng Streamlit.
- `config/settings.py`: Đọc cấu hình bảo mật và linh hoạt từ `.env`.
- `data_store/watchlist.json`: Cơ sở dữ liệu NoSQL TinyDB lưu danh mục theo dõi.
- `data_store/cache/`: Thư mục lưu đệm nến lịch sử định dạng Parquet.
- `src/database/tinydb_manager.py`: Logic CRUD Watchlist và Cảnh báo giá.
- `src/data/stock_data.py`: Engine lấy dữ liệu giá tức thì và lịch sử nến.
- `src/data/market_data.py`: Dữ liệu VN-Index và độ rộng thị trường.
- `src/analysis/indicators.py`: Thuật toán tính toán chỉ báo kỹ thuật.
- `src/analysis/forecasting.py`: Mô hình dự báo xu hướng giá & Monte Carlo.
- `src/reporting/report_builder.py`: Sinh báo cáo phân tích HTML/Markdown.
- `tests/test_data_fetch.py`: Bộ kiểm thử tự động toàn diện.
