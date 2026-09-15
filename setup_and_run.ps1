# ======================================================================
# KHỞI ĐỘNG HỆ THỐNG VIETNAM STOCK TRACKER & AI FORECAST (POWERSHELL)
# ======================================================================
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   KHỞI ĐỘNG HỆ THỐNG VIETNAM STOCK TRACKER & AI FORECAST (1-CLICK)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Kiểm tra Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[LỖI] Không tìm thấy Python trên máy tính của bạn!" -ForegroundColor Red
    Write-Host "Vui lòng cài đặt Python (3.10 - 3.13) từ https://www.python.org/"
    Write-Host "Nhớ tích chọn vào ô 'Add Python to PATH' khi cài đặt."
    Read-Host "Nhấn Enter để thoát..."
    exit 1
}

# 2. Kiểm tra mã nguồn (Tự tải về nếu thư mục mới)
Write-Host "[1/5] Kiểm tra mã nguồn dự án..." -ForegroundColor Yellow
if (-not (Test-Path "app.py")) {
    Write-Host "      Phát hiện thư mục mới! Đang tự động tải toàn bộ mã nguồn từ GitHub..." -ForegroundColor Gray
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if (-not $gitCmd) {
        Write-Host "[LỖI] Chưa cài đặt Git trên máy tính! Vui lòng tải tại: https://git-scm.com/" -ForegroundColor Red
        Read-Host "Nhấn Enter để thoát..."
        exit 1
    }
    git init 2>$null | Out-Null
    git remote add origin https://github.com/Bean2910/vietnam-stock-tracker.git 2>$null | Out-Null
    git fetch origin main --quiet
    git checkout -f -B main origin/main --quiet
    Write-Host "      -> Đã tải mã nguồn về thư mục thành công!" -ForegroundColor Green
} else {
    Write-Host "      Mã nguồn đã có sẵn. Đang kiểm tra cập nhật mới nhất từ GitHub..." -ForegroundColor Gray
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if ($gitCmd) {
        git pull origin main --quiet 2>$null
        Write-Host "      -> Đã đồng bộ mã nguồn mới nhất!" -ForegroundColor Green
    }
}

# 3. Tạo môi trường ảo .venv nếu chưa có
Write-Host ""
Write-Host "[2/5] Kiểm tra môi trường ảo Python (.venv)..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    Write-Host "      Chưa có môi trường ảo. Đang tạo .venv tự động..." -ForegroundColor Gray
    python -m venv .venv
    Write-Host "      -> Đã tạo .venv thành công." -ForegroundColor Green
} else {
    Write-Host "      -> Môi trường ảo .venv đã sẵn sàng." -ForegroundColor Green
}

# 4. Kích hoạt môi trường ảo
$activateScript = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
}

# 5. Kiểm tra file .env
Write-Host ""
Write-Host "[3/5] Kiểm tra file cấu hình .env..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "      -> Đã sao chép .env.example thành .env thành công." -ForegroundColor Green
    }
} else {
    Write-Host "      -> File cấu hình .env đã sẵn sàng." -ForegroundColor Green
}

# 6. Cài đặt các gói thư viện
Write-Host ""
Write-Host "[4/5] Cài đặt / cập nhật thư viện từ requirements.txt..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt --quiet
    Write-Host "      -> Thư viện đã được cài đặt đầy đủ." -ForegroundColor Green
}

# 7. Khởi chạy Streamlit
Write-Host ""
Write-Host "[5/5] Đang khởi chạy ứng dụng Dashboard Streamlit..." -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   ỨNG DỤNG SẼ TỰ ĐỘNG MỞ TRÊN TRÌNH DUYỆT: http://localhost:8501" -ForegroundColor Green
Write-Host "   (Để dừng ứng dụng, nhấn phím Ctrl + C)" -ForegroundColor Gray
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

streamlit run app.py
