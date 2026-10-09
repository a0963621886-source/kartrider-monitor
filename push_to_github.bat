@echo off
chcp 65001 >nul
echo ========================================================
echo   🏎️ 上傳公告監控機器人到 GitHub (啟用 24 小時免費運行)
echo ========================================================
echo.

set "GIT_PATH=%LOCALAPPDATA%\Programs\Git\cmd\git.exe"
if exist "%GIT_PATH%" (
    set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%PATH%"
)

git remote get-url origin >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo 目前已設定遠端儲存庫:
    git remote -v
    echo.
    set /p PUSH_NOW="是否立即推送到 GitHub? (Y/N, 預設 Y): "
    if /i "%PUSH_NOW%"=="N" goto END
    goto DO_PUSH
)

echo 請先在 GitHub 建立一個全新的 Public Repository (不要勾選 Add README)
echo.
set /p REPO_URL="請貼上你的 GitHub Repository 網址 (例如 https://github.com/你的帳號/你的儲存庫.git): "

if "%REPO_URL%"=="" (
    echo [錯誤] 網址不能為空！請重新執行此批次檔。
    pause
    exit /b 1
)

git remote add origin %REPO_URL%
echo.
echo [資訊] 成功加入遠端儲存庫: %REPO_URL%
echo.

:DO_PUSH
echo 正在推送到 GitHub main 分支...
echo.
git push -u origin main

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================================
    echo   🎉 上傳成功！
    echo ========================================================
    echo.
    echo 下一步設定 (只需做一次，讓它 24 小時自動跑):
    echo 1. 前往你的 GitHub 專案頁面。
    echo 2. 點擊 [Settings] -> [Secrets and variables] -> [Actions]。
    echo 3. 點擊 [New repository secret]：
    echo      Name  : DISCORD_WEBHOOK_URL
    echo      Secret: (貼上你的 Discord Webhook 網址)
    echo 4. 切換到 [Actions] 標籤頁，啟用工作流程。
    echo 5. GitHub Actions 雲端伺服器每 5 分鐘會自動檢查一次，電腦關機也能 24H 運行！
    echo.
) else (
    echo.
    echo [提示] 推送時若遇到權限問題，請確認：
    echo 1. 是否已登入你的 GitHub 帳號。
    echo 2. 若使用 Personal Access Token (PAT)，請將 Token 做為密碼輸入。
    echo.
)

:END
pause
