# 使用輕量級的 Python 3.9
FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 安裝必要的系統工具 (確保 SQLite 與 Git 能運作)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt 並安裝套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有程式碼到容器內
COPY . .

# 設定環境變數，確保 Python 輸出不被緩衝 (Logs 會即時顯示)
ENV PYTHONUNBUFFERED=1

# 給予啟動腳本執行權限
RUN chmod +x start.sh

# 雖然 Railway 會自動分配 Port，但宣告一下比較清楚
EXPOSE 8501

# 設定健康檢查 (讓 Railway 知道網站還活著)
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# 啟動指令
ENTRYPOINT ["./start.sh"]
