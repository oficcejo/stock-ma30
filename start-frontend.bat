@echo off
chcp 65001 >nul
title 30周均线交易系统 - 前端服务
echo ========================================
echo   30周均线交易系统 - 前端服务启动器
echo ========================================
echo.

REM 切换到前端目录
cd /d "%~dp0\trading-dashboard"

REM 检查node_modules是否存在
if not exist "node_modules" (
    echo [错误] 未找到node_modules依赖
    echo 请先运行 install.bat 安装依赖
    pause
    exit /b 1
)

echo [1/2] 检查环境...
call npm --version
echo.

echo [2/2] 启动前端开发服务器...
echo 前端将运行在 http://localhost:5173
echo 按Ctrl+C停止服务
echo.

REM 启动前端服务
npm run dev

REM 服务停止后
echo.
echo 前端服务已停止
pause
