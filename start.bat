@echo off
chcp 65001 >nul
title 跑跑卡丁車官網公告監控 - Discord 通知機器人

echo ======================================================
echo    跑跑卡丁車官網 (popkart.tiancity.com) 公告監控
echo ======================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [錯誤] 找不到 Python，請先安裝 Python 並加入 PATH 環境變數！
    echo.
    pause
    exit /b
)

echo [1/2] 檢查相依套件...
python -m pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [警告] 安裝套件時可能發生異常，嘗試繼續執行...
)

echo [2/2] 啟動監控服務...
echo.
python notifier.py

echo.
echo 監控程式已停止。
pause
