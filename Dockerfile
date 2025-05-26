# 使用Python 3.11作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY string_generator_bot.py .

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 暴露端口（虽然Telegram bot不需要HTTP端口，但Render需要）
EXPOSE 8000

# 启动应用
CMD ["python", "string_generator_bot.py"]
