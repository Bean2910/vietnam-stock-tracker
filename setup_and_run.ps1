# ======================================================================
# KHỞI ĐỘNG HỆ THỐNG VIETNAM STOCK TRACKER & AI FORECAST (POWERSHELL)
# ======================================================================
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   KHỞI ĐỘNG HỆ THỐNG VIETNAM STOCK TRACKER & AI FORECAST" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Kiểm tra Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[LỖI] Không tìm thấy Python trên máy tính của bạn!" -ForegroundColor Red
    Write-Host "Vui lòng cài đặt Python (3.10 - 3.13) từ https://www.python.org/"
    Read-Host "Nhấn Enter để thoát..."
    exit 1
}

# 2. Tạo môi trường ảo .venv nếu chưa có
Write-Host "[1/4] Kiểm tra môi trường ảo Python (.venv)..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    Write-Host "      Chưa có môi trường ảo. Đang tạo .venv tự động..." -ForegroundColor Gray
    python -m venv .venv
    Write-Host "      -> Đã tạo .venv thành công." -ForegroundColor Green
} else {
    Write-Host "      -> Môi trường ảo .venv đã sẵn sàng." -ForegroundColor Green
}

# 3. Kích hoạt môi trường ảo
$activateScript = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
}

# 4. Kiểm tra file .env
Write-Host ""
Write-Host "[2/4] Kiểm tra file cấu hình .env..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "      -> Đã sao chép .env.example thành .env thành công." -ForegroundColor Green
    }
} else {
    Write-Host "      -> File cấu hình .env đã sẵn sàng." -ForegroundColor Green
}

# 5. Cài đặt các gói thư viện
Write-Host ""
Write-Host "[3/4] Cài đặt / cập nhật thư viện từ requirements.txt..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
Write-Host "      -> Thư viện đã được cài đặt đầy đủ." -ForegroundColor Green

# 6. Khởi chạy Streamlit
Write-Host ""
Write-Host "[4/4] Đang khởi chạy ứng dụng Dashboard Streamlit..." -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   Ứng dụng sẽ tự động mở tại trình duyệt: http://localhost:8501" -ForegroundColor Green
Write-Host "   (Để dừng ứng dụng, nhấn phím Ctrl + C)" -ForegroundColor Gray
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

streamlit run app.py
