# 使用Python 3.12作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制Python依赖文件
COPY trading_system/requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY trading_system/ ./trading_system/

# 创建数据目录
RUN mkdir -p /app/trading_system/data /app/trading_system/logs

# 设置环境变量
ENV PYTHONPATH=/app
ENV TDX_API_URL=http://43.138.33.77:8080
ENV LOG_LEVEL=INFO

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "uvicorn", "trading_system.main:app", "--host", "0.0.0.0", "--port", "8000"]
