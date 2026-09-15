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

4. **Đối Chiếu Đa Chiều Các Mô Hình Dự Báo AI & Định Lượng (Multi-Model Ensemble)**:
   - Huấn luyện song song 5 thuật toán Machine Learning & Định lượng trên dữ liệu thực tế:
     + **Gradient Boosting (AI)**: Bắt nhịp các mẫu hình phi tuyến tính ngắn hạn.
     + **Random Forest**: Hạn chế nhiễu và giảm thiểu độ lệch cực đoan.
     + **Quán Tính Kỹ Thuật (Momentum)**: Dựa trên phân kỳ MACD, độ dốc MA20 và lực mua RSI.
     + **Monte Carlo (Cơ Sở)**: Mô phỏng xác suất lợi suất logarit chu kỳ lịch sử.
     + **Đồng Thuận Tổng Hợp (AI Consensus)**: Kết hợp trung bình có trọng số của cả 4 mô hình.
   - Bộ chọn lọc tương tác linh hoạt (chọn hiển thị mô hình bất kỳ trên biểu đồ).
   - Biểu đồ Plotly đối chiếu toàn màn hình, tự động zoom ôm sát biên độ giá (Auto-scale).
   - **Bảng so sánh chi tiết từng phiên ($T+0 \rightarrow T+N$)**:
     + Mốc tham chiếu $T+0$ hiển thị màu vàng đất nhạt chuẩn thị trường.
     + Tăng giá so với $T+0$: mũi tên lên **`▲`**, chữ màu **xanh lá**.
     + Giảm giá so với $T+0$: mũi tên xuống **`▼`**, chữ màu **đỏ**.

5. **Mô Phỏng Kịch Bản Xác Suất Monte Carlo**:
   - Dự báo kịch bản giá 7 - 15 phiên dựa trên độ biến động lịch sử (Volatility).
   - 500 kịch bản ngẫu nhiên đo lường dải tin cậy: Lạc quan (+80%), Cơ sở (Base), Thận trọng (-20%).

6. **Xuất Báo Cáo Phân Tích (Reporting Engine)**:
   - Xuất file báo cáo phân tích định dạng **HTML** giao diện sang trọng hoặc **Markdown** để lưu trữ/in ấn/chia sẻ.

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Lại Trên Máy Mới (Máy Ở Nhà)

Sau khi kéo mã nguồn về máy tính cá nhân ở nhà qua lệnh:
```bash
git clone https://github.com/Bean2910/vietnam-stock-tracker.git
cd vietnam-stock-tracker
```
*(Hoặc nếu đã clone trước đó thì chỉ cần chạy `git pull origin main`)*.

---

### ⚡ Cách 1: Khởi động 1-Click Tự Động (Khuyên dùng cho Windows)
Chỉ cần chạy file script tự động:
- **Click đúp chuột** vào file **`setup_and_run.bat`** (hoặc gõ `.\setup_and_run.bat` trong terminal).
- Hoặc chạy trên PowerShell:
  ```powershell
  .\setup_and_run.ps1
  ```
👉 File script sẽ **tự động hoàn toàn 100%**:
1. Kiểm tra & tạo môi trường ảo `.venv` nếu chưa có.
2. Tự động sao chép file cấu hình `.env`.
3. Tự động cài đặt đầy đủ tất cả thư viện trong `requirements.txt`.
4. Tự động bật ứng dụng Streamlit Dashboard trên trình duyệt web tại `http://localhost:8501`.

---

### 🛠️ Cách 2: Thực hiện thủ công từng bước (Nếu muốn tự cấu hình)

### Bước 3: Kích hoạt môi trường ảo
- **Trên Windows (PowerShell)**:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
  *(Nếu gặp lỗi Execution Policy trên PowerShell, chạy lệnh: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` rồi chạy lại lệnh Activate).*
- **Trên Windows (Command Prompt - CMD)**:
  ```cmd
  .\.venv\Scripts\activate.bat
  ```
- **Trên macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```

### Bước 4: Cài đặt các thư viện cần thiết
```bash
pip install -r requirements.txt
```

### Bước 5: Thiết lập file cấu hình môi trường `.env`
Sao chép từ file mẫu `.env.example`:
```powershell
copy .env.example .env
```
*(Trên Mac/Linux dùng `cp .env.example .env`).*

### Bước 6: Khởi chạy Ứng dụng
```powershell
streamlit run app.py
```
Trình duyệt web sẽ tự động mở trang Dashboard tại: **`http://localhost:8501`**.

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
