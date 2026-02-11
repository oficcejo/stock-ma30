@echo off
chcp 65001 >nul
title 30周均线交易系统 - 后端服务
echo ========================================
echo   30周均线交易系统 - 后端服务启动器
echo ========================================
echo.

REM 切换到后端目录
cd /d "%~dp0\trading_system"

REM 检查venv是否存在
if not exist "venv\Scripts\activate.bat" (
    echo [错误] 未找到Python虚拟环境venv
    echo 请先运行 install.bat 安装依赖
    pause
    exit /b 1
)

echo [1/3] 激活Python虚拟环境...
call venv\Scripts\activate.bat

echo [2/3] 检查环境...
python --version
echo.

echo [3/3] 启动FastAPI服务...
echo 服务将运行在 http://localhost:8000
echo 按Ctrl+C停止服务
echo.

REM 启动后端服务
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

REM 服务停止后
echo.
echo 后端服务已停止
deactivate
pause
