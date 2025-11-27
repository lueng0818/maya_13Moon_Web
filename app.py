import streamlit as st
import datetime
import os
import pandas as pd
import sqlite3
import base64
from create_db import init_db
# 這裡就是報錯的地方，只要 kin_utils.py 正確，這裡就會正常
from kin_utils import (
    calculate_kin, get_full_kin_data, get_oracle, 
    calculate_life_castle, get_img_b64, 
    SEAL_FILES, TONE_FILES
)

# --- 系統初始化 ---
st.set_page_config(page_title="13 Moon Pro", layout="wide", page_icon="🔮")

if not os.path.exists("13moon.db"):
    with st.spinner("正在初始化系統資料庫..."):
        st.cache_data.clear()
        init_db()
    st.success("資料庫建立完成！請重新整理頁面。")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fff; }
    h1, h2, h3 { color: #d4af37 !important; font-family: "Microsoft JhengHei"; }
    .kin-card-grid {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        background: #262730; border: 1px solid #444; border-radius: 8px;
        padding: 5px; width: 100%; height: 100%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.5);
    }
    .matrix-data {
        font-family: monospace; color: #00ff00; background: #000;
        padding: 10px; border-radius: 5px; margin-top: 10px; border: 1px solid #004400;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🌌 13 Moon System")
mode = st.sidebar.radio("功能導航", ["個人星系解碼", "52流年城堡", "通訊錄/合盤", "系統檢查員"])

# ... (其餘程式碼與之前相同) ...
# 如果您需要完整的 app.py 程式碼，請參考上一次的回覆
# 重點是確保 kin_utils.py 已經更新
