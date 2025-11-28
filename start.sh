#!/bin/bash

echo "🚀 正在啟動 13 Moon System..."

# --- 資料庫檢查 ---
# 如果資料庫檔案不存在，就執行初始化程式
if [ ! -f "13moon.db" ]; then
    echo "⚠️  未偵測到資料庫，開始執行初始化 (create_db.py)..."
    python create_db.py
else
    echo "✅ 資料庫 (13moon.db) 已存在，跳過初始化。"
fi

# --- 啟動 Streamlit ---
# 關鍵參數說明：
# --server.port=$PORT : 強制使用 Railway 分配的埠號 (這行最重要！)
# --server.address=0.0.0.0 : 允許外部連線
# --server.headless=true : 不顯示伺服器端視窗
# --server.enableCORS=false : 關閉跨來源資源共享檢查 (避免瀏覽器擋連線)

echo "🌟 啟動網頁伺服器..."
streamlit run app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false
