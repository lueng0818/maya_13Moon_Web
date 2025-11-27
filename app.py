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
st.set_page_config(page_title="13 Moon Pro", layout="wide", page_icon="🌙")

# 自動檢查資料庫
if not os.path.exists("13moon.db"):
    with st.spinner("正在初始化系統資料庫..."):
        init_db()
    st.success("資料庫建立完成！")

# CSS 美化
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fff; }
    h1, h2, h3 { color: #d4af37 !important; font-family: "Microsoft JhengHei"; }
    .kin-card {
        background: #262730; border: 1px solid #444; 
        border-radius: 12px; padding: 10px; text-align: center;
        transition: transform 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .kin-card:hover { transform: translateY(-5px); border-color: #d4af37; }
    .matrix-data {
        font-family: monospace; color: #00ff00; background: #000;
        padding: 10px; border-radius: 5px; margin-top: 10px; border: 1px solid #004400;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 核心功能：卡片顯示器 ---
def show_card(label, s_id, t_id, is_main=False):
    """
    顯示單張印記卡片
    s_id: 圖騰編號 (1-20)
    t_id: 調性編號 (1-13)
    """
    # 取得檔名 (確保 kin_utils.py 的對照表正確)
    s_file = SEAL_FILES.get(s_id, f"{str(s_id).zfill(2)}.jpg") # 預設檔名格式
    t_file = TONE_FILES.get(t_id, f"tone-{t_id}.png")
    
    # 組合路徑
    path_seal = f"assets/seals/{s_file}"
    path_tone = f"assets/tones/{t_file}"
    
    with st.container():
        # 卡片外框
        border_style = "2px solid gold" if is_main else "1px solid #444"
        st.markdown(f"<div class='kin-card' style='border:{border_style}'>", unsafe_allow_html=True)
        
        # 顯示調性 (上方)
        if os.path.exists(path_tone):
            st.image(path_tone, width=30 if not is_main else 40)
        else:
            st.caption(f"調性 {t_id}")
            
        # 顯示圖騰 (中間)
        if os.path.exists(path_seal):
            st.image(path_seal, width=70 if not is_main else 100)
        else:
            st.warning(f"缺圖: {s_file}")
            
        # 顯示標籤 (下方)
        st.caption(label)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 3. 側邊欄導航 ---
st.sidebar.title("🌌 13 Moon System")
mode = st.sidebar.radio("功能導航", ["個人星系解碼", "52流年城堡", "通訊錄/合盤", "資料庫檢查"])

# --- 頁面邏輯 ---

if mode == "個人星系解碼":
    st.title("🔮 個人星系印記解碼")
    
    col_date, col_btn = st.columns([2, 1])
    with col_date:
        date_in = st.date_input("請選擇生日", datetime.date.today())
    with col_btn:
        st.write("") # Spacer
        st.write("") 
        if st.button("🚀 開始解碼", type="primary"):
            st.session_state['run_decode'] = True

    if st.session_state.get('run_decode'):
        # 1. 計算 KIN
        kin = calculate_kin(date_in)
        
        # 2. 取得詳細資料 (文字)
        data = get_full_kin_data(kin)
        
        # 3. 計算五大神諭 (ID)
        oracle = get_oracle(kin)
        
        st.divider()
        
        # 版面配置：左邊主資訊，右邊神諭盤
        c1, c2 = st.columns([1, 1.5])
        
        with c1:
            # 主印記大圖
            show_card("主印記", oracle['destiny']['s'], oracle['destiny']['t'], is_main=True)
            
            st.markdown(f"## KIN {kin}")
            st.markdown(f"### {data.get('調性','')} {data.get('圖騰','')}")
            st.info(f"🌊 **波符**：{data.get('wave_name','')} 波符")
            
            # 矩陣數據展示
            with st.expander("🧬 查看 441 矩陣數據"):
                st.markdown(f"""
                <div class="matrix-data">
                時間矩陣: {data.get('Matrix_Time', '-')}<br>
                空間矩陣: {data.get('Matrix_Space', '-')}<br>
                共時矩陣: {data.get('Matrix_Sync', '-')}<br>
                BMU : {data.get('Matrix_BMU', '-')}
                </div>
                """, unsafe_allow_html=True)

        with c2:
            st.subheader("五大神諭盤")
            
            # 使用 3x3 Grid 排版
            r1c1, r1c2, r1c3 = st.columns(3)
            with r1c2: show_card("引導 (Guide)", oracle['guide']['s'], oracle['guide']['t'])
            
            r2c1, r2c2, r2c3 = st.columns(3)
            with r2c1: show_card("擴展 (Antipode)", oracle['antipode']['s'], oracle['antipode']['t'])
            with r2c2: st.markdown("<br><div style='text-align:center; color:#aaa'>Destiny</div>", unsafe_allow_html=True) # 中央留白或放文字
            with r2c3: show_card("支持 (Analog)", oracle['analog']['s'], oracle['analog']['t'])
            
            r3c1, r3c2, r3c3 = st.columns(3)
            with r3c2: show_card("推動 (Occult)", oracle['occult']['s'], oracle['occult']['t'])

            # 祈禱文與易經
            st.markdown("---")
            if '祈禱文' in data:
                st.markdown(f"**📜 祈禱文**")
                st.write(data['祈禱文'])
            
            if 'IChing_Meaning' in data:
                st.markdown(f"**☯️ 易經：{data.get('對應卦象','')}**")
                st.caption(data.get('IChing_Meaning',''))

elif mode == "52流年城堡":
    st.title("🏰 52 年生命城堡")
    d = st.date_input("請選擇生日", datetime.date(1990, 1, 1))
    
    if st.button("計算流年"):
        path = calculate_life_castle(d)
        
        st.subheader("第一週期 (0-51歲)")
        cols = st.columns(4)
        for i, row in enumerate(path[:52]):
            with cols[i % 4]:
                info = row['Info']
                # 這裡使用簡單的 HTML 顯示小卡
                seal_img_path = f"assets/seals/{info.get('seal_img','')}"
                img_html = ""
                if os.path.exists(seal_img_path):
                    b64 = get_img_b64(seal_img_path)
                    img_html = f'<img src="data:image/jpg;base64,{b64}" width="40" style="border-radius:50%">'
                
                st.markdown(f"""
                <div style="background:{row['Color']}; padding:5px; border-radius:5px; margin-bottom:5px; color:#333; text-align:center; font-size:12px;">
                    <b>{row['Age']}歲</b> ({row['Year']})<br>
                    <span style="color:#b8860b">KIN {row['KIN']}</span><br>
                    {img_html}<br>
                    {info.get('圖騰','')}
                </div>
                """, unsafe_allow_html=True)

elif mode == "資料庫檢查":
    st.title("🔍 系統檢查員")
    
    st.subheader("1. 檔案檢查")
    if os.path.exists("assets/seals"):
        files = os.listdir("assets/seals")
        st.success(f"✅ 圖騰圖片庫: 找到 {len(files)} 張圖片")
        with st.expander("查看所有圖檔名"):
            st.write(files)
    else:
        st.error("❌ 找不到 assets/seals 資料夾")

    st.subheader("2. 資料庫連接")
    if os.path.exists("13moon.db"):
        conn = sqlite3.connect("13moon.db")
        try:
            df = pd.read_sql("SELECT count(*) FROM Kin_Data", conn)
            cnt = df.iloc[0,0]
            st.success(f"✅ Kin_Data 連接成功 (共 {cnt} 筆資料)")
            
            # 測試查詢
            kin1 = pd.read_sql("SELECT * FROM Kin_Data WHERE KIN=1", conn)
            st.write("KIN 1 測試數據:", kin1)
            
        except Exception as e:
            st.error(f"❌ 資料表讀取失敗: {e}")
        conn.close()
    else:
        st.error("❌ 13moon.db 不存在")
