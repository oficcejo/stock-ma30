@echo off
chcp 65001 >nul
title 30周均线交易系统 - 安装依赖
echo ========================================
echo   30周均线交易系统 - 依赖安装
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

echo [1/4] Python版本:
python --version
echo.

REM 安装后端依赖
echo [2/4] 安装后端依赖...
cd /d "%~dp0\trading_system"

if not exist "venv" (
    echo 创建Python虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 后端依赖安装失败
    pause
    exit /b 1
)
echo 后端依赖安装完成
echo.

deactivate

REM 安装前端依赖
echo [3/4] 安装前端依赖...
cd /d "%~dp0\trading-dashboard"

call npm --version >nul 2>&1
if errorlevel 1 (
    echo [警告] 未找到Node.js，跳过前端依赖安装
    echo 请手动安装Node.js后运行 npm install
) else (
    call npm install
    if errorlevel 1 (
        echo [错误] 前端依赖安装失败
        pause
        exit /b 1
    )
    echo 前端依赖安装完成
)
echo.

REM 创建数据目录
echo [4/4] 创建数据目录...
cd /d "%~dp0"
if not exist "data" mkdir data
if not exist "logs" mkdir logs
echo 数据目录创建完成
echo.

echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 请运行以下命令启动系统：
echo   start-all.bat      - 一键启动前后端
echo   start-backend.bat  - 只启动后端
echo   start-frontend.bat - 只启动前端
echo.
pause
