@echo off
chcp 65001 >nul
title 30周均线交易系统 - 一键启动
echo ========================================
echo   30周均线交易系统 - 一键启动器
echo ========================================
echo.

REM 检查必要的目录
if not exist "trading_system" (
    echo [错误] 未找到trading_system目录
    pause
    exit /b 1
)

if not exist "trading-dashboard" (
    echo [错误] 未找到trading-dashboard目录
    pause
    exit /b 1
)

echo 即将同时启动前后端服务...
echo.
echo 后端: http://localhost:8000
echo 前端: http://localhost:5173
echo.
echo 按任意键开始启动...
pause >nul
echo.

REM 启动后端（在新窗口）
echo [1/2] 正在启动后端服务...
start "30周均线-后端" cmd /k "cd /d "%~dp0" && call start-backend.bat"

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 启动前端（在新窗口）
echo [2/2] 正在启动前端服务...
start "30周均线-前端" cmd /k "cd /d "%~dp0" && call start-frontend.bat"

echo.
echo ========================================
echo  启动完成！
echo ========================================
echo.
echo 请使用以下地址访问：
echo   - 前端界面: http://localhost:5173
echo   - API文档:  http://localhost:8000/docs
echo.
echo 关闭窗口即可停止服务
echo.
pause
