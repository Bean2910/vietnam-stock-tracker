@echo off
chcp 65001 >nul
title Vietnam Stock Tracker - Tự Động Cài Đặt & Khởi Chạy 1-Click

echo ======================================================================
echo    KHỞI ĐỘNG HỆ THỐNG VIETNAM STOCK TRACKER & AI FORECAST (1-CLICK)
echo ======================================================================
echo.

:: 1. Kiểm tra Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [LỖI] Không tìm thấy Python trên máy tính của bạn!
    echo Vui lòng cài đặt Python (3.10 - 3.13) từ: https://www.python.org/
    echo QUAN TRỌNG: Nhớ tích chọn vào ô "Add Python to PATH" khi cài đặt.
    echo.
    pause
    exit /b 1
)

:: 2. Kiểm tra mã nguồn (Tự động tải về nếu folder mới tinh chỉ có file bat)
echo [1/5] Kiểm tra mã nguồn dự án...
if not exist "app.py" (
    echo       Phát hiện thư mục mới! Đang tự động tải toàn bộ mã nguồn từ GitHub...
    where git >nul 2>nul
    if %errorlevel% neq 0 (
        echo [LỖI] Máy tính của bạn chưa cài Git!
        echo Vui lòng tải và cài Git từ: https://git-scm.com/
        pause
        exit /b 1
    )
    git init >nul 2>nul
    git remote add origin https://github.com/Bean2910/vietnam-stock-tracker.git >nul 2>nul
    git fetch origin main --quiet
    git checkout -f -B main origin/main --quiet
    if not exist "app.py" (
        echo [LỖI] Không thể tải mã nguồn từ GitHub. Vui lòng kiểm tra kết nối mạng!
        pause
        exit /b 1
    )
    echo       -> Đã tải toàn bộ mã nguồn thành công!
) else (
    echo       Mã nguồn đã có sẵn. Đang kiểm tra cập nhật mới nhất từ GitHub...
    where git >nul 2>nul
    if %errorlevel% equ 0 (
        git pull origin main --quiet 2>nul
        echo       -> Đã đồng bộ mã nguồn mới nhất!
    ) else (
        echo       -> Đã có mã nguồn, bỏ qua bước cập nhật Git.
    )
)

:: 3. Kiểm tra môi trường ảo Python (.venv)
echo.
echo [2/5] Kiểm tra môi trường ảo Python (.venv)...
if not exist ".venv" (
    echo       Đang tự động khởi tạo môi trường ảo .venv...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [LỖI] Không thể tạo môi trường ảo .venv!
        pause
        exit /b 1
    )
    echo       -> Đã tạo .venv thành công.
) else (
    echo       -> Môi trường ảo .venv đã sẵn sàng.
)

:: 4. Kích hoạt môi trường ảo
call .venv\Scripts\activate.bat

:: 5. Kiểm tra file cấu hình .env
echo.
echo [3/5] Kiểm tra cấu hình môi trường (.env)...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo       -> Đã tự động tạo file cấu hình .env từ .env.example.
    ) else (
        echo       [Bỏ qua] Không tìm thấy file mẫu .env.example.
    )
) else (
    echo       -> File cấu hình .env đã sẵn sàng.
)

:: 6. Cài đặt / Cập nhật thư viện
echo.
echo [4/5] Kiểm tra và cài đặt các thư viện (requirements.txt)...
python -m pip install --upgrade pip --quiet
if exist "requirements.txt" (
    pip install -r requirements.txt --quiet
    echo       -> Đã cài đặt đầy đủ tất cả thư viện cần thiết.
)

:: 7. Khởi chạy Ứng dụng Streamlit Dashboard
echo.
echo [5/5] Đang khởi chạy ứng dụng Dashboard...
echo ======================================================================
echo    ỨNG DỤNG SẼ TỰ ĐỘNG MỞ TRÊN TRÌNH DUYỆT: http://localhost:8501
echo    (Để tắt ứng dụng, chỉ cần đóng cửa sổ đen này hoặc bấm Ctrl + C)
echo ======================================================================
echo.

streamlit run app.py

if %errorlevel% neq 0 (
    echo.
    echo [Thông báo] Ứng dụng đã dừng lại.
    pause
)
