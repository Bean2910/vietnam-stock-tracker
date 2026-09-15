@echo off
chcp 65001 >nul
title Vietnam Stock Tracker - Khởi Động Tự Động

echo ======================================================================
echo    KHỞI ĐỘNG HỆ THỐNG VIETNAM STOCK TRACKER & AI FORECAST
echo ======================================================================
echo.

:: 1. Kiểm tra Python đã cài đặt hay chưa
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [LỖI] Không tìm thấy Python trên máy tính của bạn!
    echo Vui lòng cài đặt Python (3.10 - 3.13) từ https://www.python.org/
    echo Nhớ tích chọn "Add Python to PATH" khi cài đặt.
    echo.
    pause
    exit /b 1
)

echo [1/4] Kiểm tra môi trường ảo Python (.venv)...
if not exist ".venv" (
    echo       Chưa có môi trường ảo. Đang tạo .venv tự động...
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

:: 2. Kích hoạt môi trường ảo
call .venv\Scripts\activate.bat

:: 3. Kiểm tra file cấu hình .env
echo.
echo [2/4] Kiểm tra cấu hình .env...
if not exist ".env" (
    if exist ".env.example" (
        echo       Đang tạo file .env từ file mẫu .env.example...
        copy .env.example .env >nul
        echo       -> Đã tạo file .env thành công.
    ) else (
        echo       [Cảnh báo] Không tìm thấy .env.example, bỏ qua bước này.
    )
) else (
    echo       -> File cấu hình .env đã sẵn sàng.
)

:: 4. Cài đặt / cập nhật các thư viện phụ thuộc
echo.
echo [3/4] Kiểm tra và cập nhật các thư viện (requirements.txt)...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [Cảnh báo] Quá trình cài đặt thư viện gặp lỗi hoặc cần kết nối mạng.
) else (
    echo       -> Toàn bộ thư viện đã được cài đặt đầy đủ.
)

:: 5. Khởi chạy Dashboard ứng dụng Streamlit
echo.
echo [4/4] Đang khởi chạy ứng dụng Dashboard Streamlit...
echo ======================================================================
echo    Ứng dụng sẽ tự động mở tại trình duyệt: http://localhost:8501
echo    (Để dừng ứng dụng, nhấn phím Ctrl + C trong cửa sổ này)
echo ======================================================================
echo.

streamlit run app.py

if %errorlevel% neq 0 (
    echo.
    echo [Thông báo] Ứng dụng đã dừng lại.
    pause
)
