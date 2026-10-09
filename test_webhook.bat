@echo off
chcp 65001 >nul
title 跑跑卡丁車公告監控 - Webhook 連線測試

echo ======================================================
echo    測試 Discord Webhook 連線狀態
echo ======================================================
echo.

python notifier.py --test

echo.
pause
