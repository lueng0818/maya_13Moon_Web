import streamlit as st
import datetime
import os
import pandas as pd
import sqlite3
import base64
from create_db import init_db
from kin_utils import (
    calculate_kin_v2, calculate_kin_math, get_full_kin_data, get_oracle, 
    calculate_life_castle, get_img_b64, get_psi_kin,
    SEAL_FILES, TONE_FILES
)

# 1. 系統初始化
st.set_page_config(page_title="13 Moon Pro", layout="wide", page_icon="🔮")

# 檢查資料庫是否存在，若無則初始化
if not os.path.exists("13moon.db"):
    with st.spinner("系統初始化中 (建立資料庫)..."):
        st.cache_data.clear()
        init_db()
    st.success("初始化完成！")

# 全局 CSS 樣式
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fff; }
    h1, h2, h3 { color: #d4af37 !important; font-family: "Microsoft JhengHei"; }
    
    /* 五大神諭卡片容器 */
    .kin-card-grid {
        display: flex; /* 改為 flex 佈局 */
        flex-direction: column; /* 垂直排列 */
        align-items: center; /* 水平置中 */
        justify-content: flex-start; /* 內容置頂 */
        background: #262730; 
        border: 1px solid #444; 
        border-radius: 8px;
        padding: 5px; 
        width: 100%; 
        height: 100%; /* 確保高度 */
        box-shadow: 0 2px 5px rgba(0,0,0,0.5);
        text-align: center; /* 文字置中 */
        gap: 2px; /* 元素間距 */
    }
    .psi-box {
        background: linear-gradient(135deg, #2b1055, #7597de);
        padding: 15px; border-radius: 10px; color: white; margin-top: 20px;
    }
    .matrix-data {
        font-family: monospace; color: #00ff00; background: #000;
        padding: 10px; border-radius: 5px; margin-top: 10px; border: 1px solid #004400;
    }
    /* 調整五大神諭盤的網格佈局，增加單個卡片的大小 */
    .oracle-grid-container {
        display: grid; 
        grid-template-columns: 100px 100px 100px; /* 每列寬度 */
        grid-template-rows: 120px 120px 120px; /* 每行高度 */
        gap: 10px; 
        justify-content: center;
        align-items: center; /* 垂直置中網格項目 */
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🌌 13 Moon System")
mode = st.sidebar.radio("功能導航", ["個人星系解碼", "52流年城堡", "通訊錄/合盤", "系統檢查員"])

# --- 輔助顯示卡片 (已修改) ---
def get_card_html(label, kin_num, s_id, t_id, is_main=False):
    # 獲取印記和調性的圖片路徑
    s_f = SEAL_FILES.get(s_id, f"{str(s_id).zfill(2)}.png")
    t_f = TONE_FILES.get(t_id, f"tone-{t_id}.png")
    
    img_s_b64 = get_img_b64(f"assets/seals/{s_f}")
    img_t_b64 = get_img_b64(f"assets/tones/{t_f}")
    
    # 根據 kin_num 獲取印記名稱和調性名稱
    card_data = get_full_kin_data(kin_num)
    seal_name = card_data.get('圖騰', '')
    tone_name = card_data.get('調性', '')

    border_style = "2px solid gold" if is_main else "1px solid #555"

    return f"""
    <div class="kin-card-grid" style="border:{border_style};">
        <img src="data:image/png;base64,{img_t_b64}" style="width:25px; filter:invert(1); margin-bottom: 5px;">
        <img src="data:image/png;base64,{img_s_b64}" style="width:70px; margin-bottom: 5px;">
        <div style="font-size:12px; color:#ddd;">{tone_name}</div>
        <div style="font-size:12px; color:#aaa;">{seal_name}</div>
        <div style="font-size:10px; color:#888;">KIN {kin_num}</div>
    </div>
    """

# ==========================================
# 頁面 1: 個人星系解碼
# ==========================================
if mode == "個人星系解碼":
    st.title("🔮 個人星系印記解碼")
    
    col_d, col_b = st.columns([2, 1])
    with col_d:
        st.subheader("📅 查詢日期")
        date_in = st.date_input("選擇日期", datetime.date.today())
    with col_b:
        st.write("")
        st.write("")
        st.write("") 
        start_btn = st.button("🚀 開始解碼", type="primary")

    if start_btn or st.session_state.get('run_decode'):
        st.session_state['run_decode'] = True
        
        kin, err = calculate_kin_v2(date_in)
        if kin is None:
            st.error(f"⚠️ KIN計算失敗: {err} (將切換為數學備案)")
            kin = calculate_kin_math(date_in)
            
        data = get_full_kin_data(kin)
        oracle_info = get_oracle(kin) # 這裡改名為 oracle_info 避免與 data 混淆
        psi_data = get_psi_kin(date_in)
        
        st.divider()
        c1, c2 = st.columns([1, 1.6])
        
        with c1:
            s_path = f"assets/seals/{data.get('seal_img','')}"
            if os.path.exists(s_path):
                st.image(s_path, width=180)
            
            st.markdown(f"## KIN {kin}")
            st.markdown(f"### {data.get('主印記','')}")
            
            st.info(f"🌊 **波符**：{data.get('波符','未知')} 波符")
            st.caption(f"🏰 **城堡**：{data.get('城堡','未知')}")
            
            if psi_data:
                p_info = psi_data['Info']
                st.markdown(f"""
                <div class="psi-box">
                    <h4 style="margin:0">🧬 PSI 行星記憶庫</h4>
                    <h3 style="margin:5px 0 0 0; color:#ffd700">KIN {psi_data['KIN']}</h3>
                    <div style="font-size:14px">{p_info.get('主印記','')}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with st.expander("🧬 441 矩陣數據"):
                st.markdown(f"""<div class="matrix-data">
                時間: {data.get('Matrix_Time','-')}<br>
                空間: {data.get('Matrix_Space','-')}<br>
                共時: {data.get('Matrix_Sync','-')}<br>
                BMU : {data.get('Matrix_BMU','-')}
                </div>""", unsafe_allow_html=True)

        with c2:
            st.subheader("五大神諭盤")
            
            # 獲取每個神諭的 KIN 數字
            guide_kin = oracle_info['guide']['s'] + (oracle_info['guide']['t']-1)*20
            if guide_kin > 260: guide_kin %= 260
            if guide_kin == 0: guide_kin = 260 # 確保是 1-260

            analog_kin = oracle_info['analog']['s'] + (oracle_info['analog']['t']-1)*20
            if analog_kin > 260: analog_kin %= 260
            if analog_kin == 0: analog_kin = 260

            antipode_kin = oracle_info['antipode']['s'] + (oracle_info['antipode']['t']-1)*20
            if antipode_kin > 260: antipode_kin %= 260
            if antipode_kin == 0: antipode_kin = 260

            occult_kin = oracle_info['occult']['s'] + (oracle_info['occult']['t']-1)*20
            if occult_kin > 260: occult_kin %= 260
            if occult_kin == 0: occult_kin = 260


            html_guide = get_card_html("引導", guide_kin, oracle_info['guide']['s'], oracle_info['guide']['t'])
            html_anti  = get_card_html("擴展", antipode_kin, oracle_info['antipode']['s'], oracle_info['antipode']['t'])
            html_main  = get_card_html("主印記", kin, oracle_info['destiny']['s'], oracle_info['destiny']['t'], True)
            html_analog= get_card_html("支持", analog_kin, oracle_info['analog']['s'], oracle_info['analog']['t'])
            html_occult= get_card_html("推動", occult_kin, oracle_info['occult']['s'], oracle_info['occult']['t'])

            st.markdown(f"""
            <div class="oracle-grid-container">
                <div></div> <div>{html_guide}</div> <div></div>
                <div>{html_anti}</div> <div>{html_main}</div> <div>{html_analog}</div>
                <div></div> <div>{html_occult}</div> <div></div>
            </div>
            """, unsafe_allow_html=True)

            if 'IChing_Meaning' in data:
                st.markdown("---")
                st.success(f"**☯️ {data.get('對應卦象','')}**：{data.get('IChing_Meaning','')}")

# ==========================================
# 頁面 2: 52 流年城堡
# ==========================================
elif mode == "52流年城堡":
    st.title("🏰 52 年生命城堡")
    d = st.date_input("出生日期", datetime.date(1990, 1, 1))
    if st.button("計算"):
        path = calculate_life_castle(d)
        st.subheader("第一週期 (0-51歲)")
        cols = st.columns(4)
        for i, row in enumerate(path[:52]):
            with cols[i % 4]:
                info = row['Info']
                s_p = f"assets/seals/{info.get('seal_img','')}"
                img_html = f'<img src="data:image/png;base64,{get_img_b64(s_p)}" width="40" style="border-radius:50%">' if os.path.exists(s_p) else ""
                st.markdown(f"""
                <div style="background:{row['Color']}; padding:5px; border-radius:5px; margin-bottom:5px; color:#333; text-align:center; font-size:12px;">
                    <b>{row['Age']}歲</b> ({row['Year']})<br>
                    <span style="color:#b8860b">KIN {row['KIN']}</span><br>
                    {img_html}<br>
                    {info.get('主印記','')}
                </div>
                """, unsafe_allow_html=True)

# ==========================================
# 頁面 3: 通訊錄
# ==========================================
elif mode == "通訊錄/合盤":
    st.title("👥 通訊錄")
    conn = sqlite3.connect("13moon.db")
    try:
        df = pd.read_sql("SELECT * FROM Users", conn)
        st.dataframe(df)
    except:
        st.warning("無通訊錄資料")
    conn.close()

# ==========================================
# 頁面 4: 系統檢查員
# ==========================================
elif mode == "系統檢查員":
    st.title("🔍 系統檢查")
    if os.path.exists("13moon.db"):
        conn = sqlite3.connect("13moon.db")
        try:
            st.success("資料庫連接成功")
            # 檢查 Kin_Basic
            try:
                kb = pd.read_sql("SELECT * FROM Kin_Basic LIMIT 3", conn)
                st.write("Kin_Basic (前3筆):", kb)
            except: st.error("Kin_Basic 表格缺失")
            
            # 檢查 Kin_Start
            try:
                ks = pd.read_sql("SELECT * FROM Kin_Start LIMIT 3", conn)
                st.write("Kin_Start (前3筆):", ks)
            except: st.error("Kin_Start 表格缺失")
            
            # 檢查 Month_Accum
            try:
                ma = pd.read_sql("SELECT * FROM Month_Accum LIMIT 3", conn)
                st.write("Month_Accum (前3筆):", ma)
            except: st.error("Month_Accum 表格缺失")
            
        except Exception as e: st.error(f"錯誤: {e}")
        conn.close()
    else:
        st.error("資料庫未建立")
