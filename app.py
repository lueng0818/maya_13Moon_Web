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

# --- 1. 自動檢查並建立資料庫 ---
if not os.path.exists("13moon.db"):
    st.warning("正在初始化資料庫，請稍候...")
    init_db()
    st.success("資料庫建立完成！請重新整理頁面。")
    st.stop()

# --- 2. 頁面設定 ---
st.set_page_config(page_title="13 Moon Pro", layout="wide", page_icon="🌙")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fff; }
    h1, h2, h3 { color: #d4af37 !important; font-family: "Microsoft JhengHei"; }
    .kin-card {
        background: #262730; border: 1px solid #444; 
        border-radius: 12px; padding: 10px; text-align: center;
        transition: transform 0.2s;
    }
    .kin-card:hover { transform: scale(1.03); border-color: #d4af37; }
    .matrix-data {
        font-family: monospace; color: #00ff00; background: #000;
        padding: 10px; border-radius: 5px; margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 側邊欄
st.sidebar.title("🌌 13 Moon System")
mode = st.sidebar.radio("功能導航", ["個人星系解碼", "52流年城堡", "通訊錄/合盤", "矩陣資料庫"])

# --- 輔助顯示卡片 ---
def show_card(label, s_id, t_id, is_main=False):
    s_file = SEAL_FILES.get(s_id, "01紅龍.jpg")
    t_file = TONE_FILES.get(t_id, "瑪雅曆法圖騰-34.png")
    
    with st.container():
        st.markdown(f"<div class='kin-card' style='border:{'2px solid gold' if is_main else ''}'>", unsafe_allow_html=True)
        st.image(f"assets/tones/{t_file}", width=30 if not is_main else 40)
        st.image(f"assets/seals/{s_file}", width=70 if not is_main else 100)
        st.caption(label)
        st.markdown("</div>", unsafe_allow_html=True)

# === 頁面 1: 個人解碼 ===
if mode == "個人星系解碼":
    st.title("🔮 個人星系印記解碼")
    date_in = st.date_input("請選擇生日", datetime.date.today())
    
    if st.button("開始解碼"):
        kin = calculate_kin(date_in)
        data = get_full_kin_data(kin)
        oracle = get_oracle(kin)
        
        c1, c2 = st.columns([1, 2])
        
        # ... 上面是 c1, c2 = st.columns([1, 2]) ...

        with c1:
            # (注意：這裡必須要縮排！請確保這行前面有空格)
            # --- 修改後的圖片顯示邏輯 ---
            seal_path = f"assets/seals/{data.get('seal_img', '')}"
            
            # 檢查檔案是否存在
            if os.path.exists(seal_path):
                st.image(seal_path, width=180)
            else:
                # 找不到時顯示替代文字，避免崩潰
                st.warning(f"⚠️ 找不到圖片：{data.get('seal_img', '未知')}")
                st.caption(f"路徑: {seal_path}")
            # -----------------------------------

            st.markdown(f"## KIN {kin}")
            st.markdown(f"### {data.get('調性','')} {data.get('圖騰','')}")
            st.info(f"波符：{data.get('wave_name','')} 波符")
            
            # ... 下面繼續 ...
            
            # 矩陣數據
            st.markdown("#### 🧬 441 矩陣座標")
            st.markdown(f"""
            <div class="matrix-data">
            時間: {data.get('Matrix_Time')}<br>
            空間: {data.get('Matrix_Space')}<br>
            共時: {data.get('Matrix_Sync')}<br>
            BMU : {data.get('Matrix_BMU')}
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.subheader("📜 祈禱文")
            st.write(data.get('祈禱文', '（無資料）'))
            
            if 'IChing_Meaning' in data:
                with st.expander("查看易經卦象", expanded=True):
                    st.success(f"**{data.get('對應卦象','')}**\n\n{data.get('IChing_Meaning','')}\n\n_{data.get('IChing_Story','')}_")

            st.subheader("五大神諭")
            cols = st.columns(5)
            with cols[0]: show_card("引導", oracle['guide']['s'], oracle['guide']['t'])
            with cols[1]: show_card("擴展", oracle['antipode']['s'], oracle['antipode']['t'])
            with cols[2]: show_card("主印記", oracle['destiny']['s'], oracle['destiny']['t'], True)
            with cols[3]: show_card("支持", oracle['analog']['s'], oracle['analog']['t'])
            with cols[4]: show_card("推動", oracle['occult']['s'], oracle['occult']['t'])
            
            st.subheader("波符旅程")
            if os.path.exists(f"assets/wavespells/{data['wave_img']}"):
                st.image(f"assets/wavespells/{data['wave_img']}")

# === 頁面 2: 52流年 ===
elif mode == "52流年城堡":
    st.title("🏰 52 年生命城堡")
    date_in = st.date_input("請選擇生日", datetime.date(1990, 1, 1))
    
    if st.button("計算流年"):
        path = calculate_life_castle(date_in)
        
        # 顯示 0-51 歲 (第一輪)
        st.subheader("第一週期 (0-51歲)")
        cols = st.columns(4)
        for i, row in enumerate(path[:52]):
            with cols[i % 4]:
                info = row['Info']
                img_path = f"assets/seals/{info['seal_img']}"
                img_b64 = get_img_b64(img_path)
                
                st.markdown(f"""
                <div style="background:{row['Color']}; padding:8px; border-radius:8px; margin-bottom:8px; color:#333; text-align:center;">
                    <small>{row['Age']} 歲 ({row['Year']})</small><br>
                    <b style="color:#b8860b">KIN {row['KIN']}</b><br>
                    <img src="data:image/jpg;base64,{img_b64}" width="40" style="border-radius:50%"><br>
                    <span style="font-size:12px">{info.get('調性','')} {info.get('圖騰','')}</span>
                </div>
                """, unsafe_allow_html=True)

# === 頁面 3: 通訊錄 ===
elif mode == "通訊錄/合盤":
    st.title("👥 通訊錄與合盤")
    conn = sqlite3.connect("13moon.db")
    try:
        df = pd.read_sql("SELECT * FROM Users", conn)
        st.dataframe(df)
        
        st.subheader("❤️ 合盤計算器")
        names = df['名字'].tolist() if not df.empty else []
        c1, c2 = st.columns(2)
        p1 = c1.selectbox("選擇 A", ["手動輸入"] + names)
        p2 = c2.selectbox("選擇 B", ["手動輸入"] + names)
        
        if st.button("計算關係"):
            # 簡單範例：抓取 KIN 進行計算
            # 實際專案可在此擴充合盤邏輯
            st.info("合盤功能開發中... (可從 Users 表讀取 KIN 相加)")
            
    except:
        st.error("通訊錄讀取失敗，請確認 data/通訊錄.csv 是否存在")
    conn.close()

# === 頁面 4: 矩陣資料庫 ===
elif mode == "矩陣資料庫":
    st.title("🧬 核心資料庫預覽")
    conn = sqlite3.connect("13moon.db")
    
    tab1, tab2, tab3 = st.tabs(["卓爾金曆", "441矩陣", "星際年"])
    with tab1: st.dataframe(pd.read_sql("SELECT * FROM Kin_Data LIMIT 50", conn))
    with tab2: 
        try: st.dataframe(pd.read_sql("SELECT * FROM Matrix_Data LIMIT 50", conn))
        except: st.warning("矩陣資料未匯入")
    with tab3:
        try: st.dataframe(pd.read_sql("SELECT * FROM Star_Years LIMIT 50", conn))
        except: st.warning("星際年資料未匯入")
    conn.close()



