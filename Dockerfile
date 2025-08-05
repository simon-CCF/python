FROM python:3.11-slim

WORKDIR /app

# 避免 interactive 問題
ENV PYTHONUNBUFFERED=1

# 安裝必要套件（可擴充）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製並安裝 python 依賴
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 複製整個程式碼
COPY . .

# 預設不指定 CMD，讓 docker-compose 用 command 覆蓋
EXPOSE 8000
