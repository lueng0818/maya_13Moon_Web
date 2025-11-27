import streamlit as st
import datetime
import os
import pandas as pd
import sqlite3
import base64
from create_db import init_db
from kin_utils import (
    calculate_kin, get_full_kin_data, get_oracle, 
    calculate_life_castle, get_img_b64, 
    SEAL_FILES, TONE_FILES
)

# --- 1. 系統初始化 ---
st.set_page_config(page_title="13 Moon Pro", layout="wide", page_icon="🔮")

# 自動檢查資料庫 (若不存在則初始化)
if not os.path.exists("13moon.db"):
    with st.spinner("正在初始化系統資料庫..."):
        st.cache_data.clear() # 清除快取，確保讀取最新 CSV
        init_db()
    st.success("資料庫建立完成！請重新整理頁面。")

# 全域 CSS 美化
st.markdown("""
<style>
    /* 背景與字體 */
    .stApp { background-color: #0e1117; color: #fff; }
    h1, h2, h3 { color: #d4af37 !important; font-family: "Microsoft JhengHei"; }
    
    /* 卡片通用樣式 */
    .kin-card-grid {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        background: #262730; border: 1px solid #444; border-radius: 8px;
        padding: 5px; width: 100%; height: 100%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.5);
        transition: transform 0.2s;
    }
    .kin-card-grid:hover { transform: scale(1.02); border-color: #d4af37; }
    
    /* 矩陣數據框 */
    .matrix-data {
        font-family: monospace; color: #00ff00; background: #000;
        padding: 10px; border-radius: 5px; margin-top: 10px; border: 1px solid #004400;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 側邊欄導航 ---
st.sidebar.title("🌌 13 Moon System")
mode = st.sidebar.radio("功能導航", ["個人星系解碼", "52流年城堡", "通訊錄/合盤", "系統檢查員"])

# ==========================================
# 功能 1: 個人星系解碼 (核心功能)
# ==========================================
if mode == "個人星系解碼":
    st.title("🔮 個人星系印記解碼")
    
    # 輸入區
    col_d, col_b = st.columns([2, 1])
    with col_d:
        date_in = st.date_input("請選擇生日", datetime.date.today())
    with col_b:
        st.write("")
        st.write("")
        start_btn = st.button("🚀 開始解碼", type="primary")

    # 執行解碼
    if start_btn or st.session_state.get('run_decode'):
        st.session_state['run_decode'] = True
        
        # 1. 計算 KIN 與 取得資料
        kin = calculate_kin(date_in)
        data = get_full_kin_data(kin) # 包含文字、圖片路徑、矩陣資料
        oracle = get_oracle(kin)      # 計算五大神諭 ID
        
        st.divider()
        c1, c2 = st.columns([1, 1.6])
        
        # --- 左側：主印記大圖與數據 ---
        with c1:
            # 圖片顯示 (支援 PNG)
            seal_img = data.get('seal_img', '') # 從 kin_utils 取得檔名 (如 01紅龍.png)
            s_path = f"assets/seals/{seal_img}"
            
            if os.path.exists(s_path):
                st.image(s_path, width=180)
            else:
                st.warning(f"⚠️ 缺圖: {seal_img}")
                st.caption("請檢查 assets/seals 資料夾")

            st.markdown(f"## KIN {kin}")
            st.markdown(f"### {data.get('調性','')} {data.get('圖騰','')}")
            st.info(f"🌊 **波符**：{data.get('wave_name','')} 波符")
            
            # 矩陣數據 (展開顯示)
            with st.expander("🧬 查看 441 矩陣數據", expanded=True):
                st.markdown(f"""
                <div class="matrix-data">
                時間: {data.get('Matrix_Time','-')}<br>
                空間: {data.get('Matrix_Space','-')}<br>
                共時: {data.get('Matrix_Sync','-')}<br>
                BMU : {data.get('Matrix_BMU','-')}
                </div>
                """, unsafe_allow_html=True)

        # --- 右側：五大神諭盤 (HTML/CSS Grid 排版) ---
        with c2:
            st.subheader("五大神諭盤")
            
            # 定義產生 HTML 卡片的函數
            def get_card_html(label, s_id, t_id, is_main=False):
                # 取得檔名 (確保是 .png)
                # 若 kin_utils 字典裡找不到，就用預設格式補救
                s_name = SEAL_FILES.get(s_id, f"{str(s_id).zfill(2)}.png")
                if not s_name.endswith(".png") and not s_name.endswith(".jpg"): 
                    s_name += ".png"
                    
                t_name = TONE_FILES.get(t_id, f"tone-{t_id}.png")
                
                # 轉 Base64 顯示
                img_s = get_img_b64(f"assets/seals/{s_name}")
                img_t = get_img_b64(f"assets/tones/{t_name}")
                
                border = "2px solid #d4af37" if is_main else "1px solid #555"
                bg_color = "#2a2a2a" if is_main else "#222"
                
                return f"""
                <div class="kin-card-grid" style="border:{border}; background:{bg_color};">
                    <img src="data:image/png;base64,{img_t}" style="width:20px; margin-bottom:2px; filter: invert(1);">
                    <img src="data:image/png;base64,{img_s}" style="width:50px; border-radius:50%;">
                    <div style="font-size:11px; color:#aaa; margin-top:2px;">{label}</div>
                </div>
                """

            # 產生 5 張卡片的 HTML
            html_guide = get_card_html("引導", oracle['guide']['s'], oracle['guide']['t'])
            html_anti  = get_card_html("擴展", oracle['antipode']['s'], oracle['antipode']['t'])
            html_main  = get_card_html("主印記", oracle['destiny']['s'], oracle['destiny']['t'], True)
            html_analog= get_card_html("支持", oracle['analog']['s'], oracle['analog']['t'])
            html_occult= get_card_html("推動", oracle['occult']['s'], oracle['occult']['t'])

            # 使用 Grid 3x3 排列
            st.markdown(f"""
            <div style="
                display: grid;
                grid-template-columns: 80px 80px 80px;
                grid-template-rows: 90px 90px 90px;
                gap: 12px;
                justify-content: center;
                margin-top: 10px;
            ">
                <div></div> <div>{html_guide}</div> <div></div>
                
                <div>{html_anti}</div> <div>{html_main}</div> <div>{html_analog}</div>
                
                <div></div> <div>{html_occult}</div> <div></div>
            </div>
            """, unsafe_allow_html=True)

            # 易經與祈禱文區塊
            st.markdown("---")
            if 'IChing_Meaning' in data:
                st.success(f"**☯️ 易經：{data.get('對應卦象','')}**\n\n{data.get('IChing_Meaning','')}")
            
            if '祈禱文' in data:
                with st.expander("📜 查看祈禱文"):
                    st.write(data['祈禱文'])

# ==========================================
# 功能 2: 52 年生命城堡 (流年)
# ==========================================
elif mode == "52流年城堡":
    st.title("🏰 52 年生命城堡")
    d = st.date_input("請選擇出生日期", datetime.date(1990, 1, 1))
    
    if st.button("計算流年路徑"):
        path = calculate_life_castle(d)
        
        st.subheader("第一週期 (0-51歲)")
        
        # 使用 Streamlit columns 顯示 (每行4個)
        cols = st.columns(4)
        for i, row in enumerate(path[:52]):
            with cols[i % 4]:
                info = row['Info']
                # 取得圖片 HTML
                s_path = f"assets/seals/{info.get('seal_img','')}"
                img_html = ""
                if os.path.exists(s_path):
                    b64 = get_img_b64(s_path)
                    img_html = f'<img src="data:image/png;base64,{b64}" width="40" style="border-radius:50%; margin:5px 0;">'
                
                st.markdown(f"""
                <div style="background:{row['Color']}; padding:8px; border-radius:8px; margin-bottom:8px; color:#333; text-align:center; font-size:12px;">
                    <b style="font-size:14px;">{row['Age']} 歲</b> <span style="color:#666">({row['Year']})</span><br>
                    <span style="color:#b8860b; font-weight:bold;">KIN {row['KIN']}</span><br>
                    {img_html}<br>
                    {info.get('圖騰','')}
                </div>
                """, unsafe_allow_html=True)

# ==========================================
# 功能 3: 通訊錄與合盤
# ==========================================
elif mode == "通訊錄/合盤":
    st.title("👥 通訊錄與合盤")
    if os.path.exists("13moon.db"):
        conn = sqlite3.connect("13moon.db")
        try:
            df = pd.read_sql("SELECT * FROM Users", conn)
            st.dataframe(df)
            st.info("合盤計算功能開發中... (可使用上方的個人解碼分別查詢兩人的 KIN 再對照)")
        except:
            st.warning("通訊錄資料未匯入，請檢查 data/通訊錄.csv 是否存在")
        conn.close()
    else:
        st.error("資料庫尚未建立")

# ==========================================
# 功能 4: 系統檢查員 (除錯專用)
# ==========================================
elif mode == "系統檢查員":
    st.title("🔍 系統狀態檢查")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("1. 圖片庫檢查")
        if os.path.exists("assets/seals"):
            files = os.listdir("assets/seals")
            st.success(f"✅ 圖騰資料夾: 找到 {len(files)} 張圖片")
            # 列出前 5 張確認檔名
            st.text(f"範例: {files[:5]}")
        else:
            st.error("❌ 找不到 assets/seals 資料夾")
            
    with c2:
        st.subheader("2. 資料庫檢查")
        if os.path.exists("13moon.db"):
            conn = sqlite3.connect("13moon.db")
            try:
                cnt = pd.read_sql("SELECT count(*) FROM Kin_Data", conn).iloc[0,0]
                st.success(f"✅ 資料庫連接正常 (KIN資料: {cnt}筆)")
                
                # 測試讀取 KIN 1
                kin1 = pd.read_sql("SELECT * FROM Kin_Data WHERE KIN=1", conn).iloc[0]
                st.info(f"KIN 1 測試: {kin1.get('主印記', '無資料')}")
                st.json(dict(kin1)) # 顯示完整欄位，方便檢查
            except Exception as e:
                st.error(f"❌ 資料讀取失敗: {e}")
            conn.close()
        else:
            st.error("❌ 資料庫檔案不存在")
