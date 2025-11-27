import streamlit as st
import datetime
import os
import pandas as pd
import sqlite3
from create_db import init_db
from kin_utils import (
    calculate_kin, get_full_kin_data, get_oracle, 
    calculate_life_castle, get_img_b64, 
    SEAL_FILES, TONE_FILES
)

# --- 1. 自動檢查資料庫 ---
if not os.path.exists("13moon.db"):
    st.cache_data.clear() # 清除快取以防萬一
    init_db()

# --- 2. 頁面設定 ---
st.set_page_config(page_title="13 Moon Pro", layout="wide", page_icon="🔮")

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

# 側邊欄
st.sidebar.title("🌌 13 Moon System")
mode = st.sidebar.radio("功能導航", ["個人星系解碼", "52流年城堡", "通訊錄/合盤"])

# === 功能 1: 個人星系解碼 ===
if mode == "個人星系解碼":
    st.title("🔮 個人星系印記解碼")
    
    col_d, col_b = st.columns([2, 1])
    with col_d:
        date_in = st.date_input("請選擇生日", datetime.date.today())
    with col_b:
        st.write("")
        st.write("")
        start_btn = st.button("🚀 開始解碼", type="primary")

    if start_btn or st.session_state.get('run_decode'):
        st.session_state['run_decode'] = True
        
        # 計算資料
        kin = calculate_kin(date_in)
        data = get_full_kin_data(kin)
        oracle = get_oracle(kin)
        
        st.divider()
        c1, c2 = st.columns([1, 1.5])
        
        # --- 左側：主資訊 ---
        with c1:
            # 主印記大圖
            s_path = f"assets/seals/{data.get('seal_img','')}"
            if os.path.exists(s_path):
                st.image(s_path, width=180)
            else:
                st.warning(f"缺圖: {data.get('seal_img','')}")

            st.markdown(f"## KIN {kin}")
            st.markdown(f"### {data.get('調性','')} {data.get('圖騰','')}")
            st.info(f"🌊 **波符**：{data.get('wave_name','')} 波符")
            
            with st.expander("🧬 查看 441 矩陣"):
                st.markdown(f"""<div class="matrix-data">
                時間: {data.get('Matrix_Time','-')}<br>
                空間: {data.get('Matrix_Space','-')}<br>
                共時: {data.get('Matrix_Sync','-')}<br>
                BMU : {data.get('Matrix_BMU','-')}
                </div>""", unsafe_allow_html=True)

        # --- 右側：五大神諭盤 (CSS Grid 完美版) ---
        with c2:
            st.subheader("五大神諭盤")
            
            # 產生卡片 HTML 的函數
            def get_html(label, s_id, t_id, is_main=False):
                s_f = SEAL_FILES.get(s_id, "01紅龍.jpg")
                t_f = TONE_FILES.get(t_id, "瑪雅曆法圖騰-34.png")
                
                img_s = get_img_b64(f"assets/seals/{s_f}")
                img_t = get_img_b64(f"assets/tones/{t_f}")
                
                border = "2px solid gold" if is_main else "1px solid #555"
                
                return f"""
                <div class="kin-card-grid" style="border:{border}">
                    <img src="data:image/png;base64,{img_t}" style="width:20px; margin-bottom:2px;">
                    <img src="data:image/jpeg;base64,{img_s}" style="width:50px; border-radius:50%;">
                    <div style="font-size:10px; color:#aaa;">{label}</div>
                </div>
                """

            # 產生五張卡
            card_guide = get_html("引導", oracle['guide']['s'], oracle['guide']['t'])
            card_anti  = get_html("擴展", oracle['antipode']['s'], oracle['antipode']['t'])
            card_main  = get_html("主印記", oracle['destiny']['s'], oracle['destiny']['t'], True)
            card_analog= get_html("支持", oracle['analog']['s'], oracle['analog']['t'])
            card_occult= get_html("推動", oracle['occult']['s'], oracle['occult']['t'])

            # Grid 佈局 (3x3)
            st.markdown(f"""
            <div style="display: grid; grid-template-columns: 80px 80px 80px; grid-template-rows: 90px 90px 90px; gap: 10px; justify-content: center;">
                <div></div> <div>{card_guide}</div> <div></div>
                <div>{card_anti}</div> <div>{card_main}</div> <div>{card_analog}</div>
                <div></div> <div>{card_occult}</div> <div></div>
            </div>
            """, unsafe_allow_html=True)

            # 易經與祈禱文
            st.markdown("---")
            if 'IChing_Meaning' in data:
                st.success(f"**☯️ 易經**：{data.get('對應卦象','')}\n\n{data.get('IChing_Meaning','')}")
            if '祈禱文' in data:
                with st.expander("📜 祈禱文"):
                    st.write(data['祈禱文'])

# === 功能 2: 52 流年 ===
elif mode == "52流年城堡":
    st.title("🏰 52 年生命城堡")
    d = st.date_input("請選擇生日", datetime.date(1990, 1, 1))
    if st.button("計算流年"):
        path = calculate_life_castle(d)
        st.subheader("第一週期 (0-51歲)")
        
        # 使用 Streamlit columns 顯示 (每行 4 個)
        cols = st.columns(4)
        for i, row in enumerate(path[:52]):
            with cols[i % 4]:
                info = row['Info']
                s_path = f"assets/seals/{info.get('seal_img','')}"
                img_html = f'<img src="data:image/jpeg;base64,{get_img_b64(s_path)}" width="40" style="border-radius:50%">' if os.path.exists(s_path) else ""
                
                st.markdown(f"""
                <div style="background:{row['Color']}; padding:5px; border-radius:5px; margin-bottom:5px; color:#333; text-align:center; font-size:12px;">
                    <b>{row['Age']}歲</b> ({row['Year']})<br>
                    <span style="color:#b8860b">KIN {row['KIN']}</span><br>
                    {img_html}<br>
                    {info.get('圖騰','')}
                </div>
                """, unsafe_allow_html=True)

# === 功能 3: 通訊錄 ===
elif mode == "通訊錄/合盤":
    st.title("👥 通訊錄")
    conn = sqlite3.connect("13moon.db")
    try:
        df = pd.read_sql("SELECT * FROM Users", conn)
        st.dataframe(df)
    except:
        st.warning("通訊錄資料未匯入")
    conn.close()
