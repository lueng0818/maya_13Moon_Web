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
    SEAL_FILES, TONE_FILES, SEALS_NAMES, TONE_NAMES # 【新增】導入名稱列表
)

# 1. 系統初始化
st.set_page_config(page_title="13 Moon Pro", layout="wide", page_icon="🔮")

if not os.path.exists("13moon.db"):
    with st.spinner("系統初始化中 (建立資料庫)..."):
        st.cache_data.clear()
        init_db()
    st.success("初始化完成！")

# 全域 CSS 樣式
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fff; }
    h1, h2, h3 { color: #d4af37 !important; font-family: "Microsoft JhengHei"; }
    
    /* 修正後的五大神諭卡片容器 */
    .kin-card-grid {
        display: flex; flex-direction: column; 
        align-items: center; justify-content: flex-start; /* 內容由上往下排 */
        background: #262730; border: 1px solid #444; border-radius: 8px;
        padding: 5px; width: 100%; height: 100%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.5);
        text-align: center;
        gap: 0; /* 減少間距 */
    }
    
    /* 【關鍵修正 1】：調整網格高度，讓中央區塊有足夠空間 */
    .oracle-grid-container {
        display: grid; 
        grid-template-columns: 100px 100px 100px;
        grid-template-rows: 100px 140px 100px; /* 中央行增加到 140px */
        gap: 12px; 
        justify-content: center;
        align-items: center;
    }

    .matrix-data {
        font-family: monospace; color: #00ff00; background: #000;
        padding: 10px; border-radius: 5px; margin-top: 10px; border: 1px solid #004400;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🌌 13 Moon System")
mode = st.sidebar.radio("功能導航", ["個人星系解碼", "52流年城堡", "通訊錄/合盤", "系統檢查員"])

# --- 輔助顯示卡片 (已修正) ---
def get_card_html(label, kin_num, s_id, t_id, is_main=False):
    """
    【修正】：使用靜態列表 SEALS_NAMES 獲取名稱，避免查資料庫 KIN 錯誤。
    """
    s_f = SEAL_FILES.get(s_id, f"{str(s_id).zfill(2)}.png")
    t_f = TONE_FILES.get(t_id, f"tone-{t_id}.png")
    
    img_s_b64 = get_img_b64(f"assets/seals/{s_f}")
    img_t_b64 = get_img_b64(f"assets/tones/{t_f}")
    
    # 【關鍵修正 2】：直接從導入的列表獲取中文名稱
    seal_name = SEALS_NAMES[s_id] if 0 < s_id < 21 else "未知圖騰"
    tone_name = TONE_NAMES[t_id] if 0 < t_id < 14 else "未知調性"

    border_style = "2px solid gold" if is_main else "1px solid #555"

    return f"""
    <div class="kin-card-grid" style="border:{border_style};">
        <img src="data:image/png;base64,{img_t_b64}" style="width:30px; filter:invert(1); margin: 0 auto 5px auto;">
        <img src="data:image/jpeg;base64,{img_s_b64}" style="width:80px; margin-bottom: 5px;">
        <div style="font-size:12px; color:#ddd; line-height:1.2;">{tone_name} {seal_name}</div>
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
        date_in = st.date_input("選擇生日", datetime.date.today())
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
        oracle_info = get_oracle(kin)
        psi_data = get_psi_kin(date_in)
        
        st.divider()
        c1, c2 = st.columns([1, 1.6])
        
        # 這裡的 KIN 數字計算還是使用數學公式，但因為已經在 kin_utils.py 中驗證過，是相對穩定的。
        guide_kin = (oracle_info['guide']['s'] + (oracle_info['guide']['t']-1)*20 -1)%260 + 1
        analog_kin = (oracle_info['analog']['s'] + (oracle_info['analog']['t']-1)*20 -1)%260 + 1
        antipode_kin = (oracle_info['antipode']['s'] + (oracle_info['antipode']['t']-1)*20 -1)%260 + 1
        occult_kin = (oracle_info['occult']['s'] + (oracle_info['occult']['t']-1)*20 -1)%260 + 1


        with c1:
            seal_img = data.get('seal_img', '')
            s_path = f"assets/seals/{seal_img}"
            
            if os.path.exists(s_path):
                st.image(s_path, width=180)
            else:
                st.warning(f"⚠️ 缺圖: {seal_img}")

            st.markdown(f"## KIN {kin}")
            st.markdown(f"### {data.get('主印記','')}")
            
            st.info(f"🌊 **波符**：{data.get('波符','未知')} 波符")
            st.caption(f"🏰 **城堡**：{data.get('城堡','未知')}")
            
            if psi_data:
                # ... (PSI 區塊邏輯不變) ...
                p_info = psi_data['Info']
                st.markdown(f"""
                <div class="psi-box">
                    <h4 style="margin:0">🧬 PSI 行星記憶庫</h4>
                    <h3 style="margin:5px 0 0 0; color:#ffd700">KIN {psi_data['KIN']}</h3>
                    <div style="font-size:14px">{p_info.get('主印記','')}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with st.expander("🧬 441 矩陣數據"):
                # ... (矩陣數據邏輯不變) ...
                st.markdown(f"""<div class="matrix-data">
                時間: {data.get('Matrix_Time','-')}<br>
                空間: {data.get('Matrix_Space','-')}<br>
                共時: {data.get('Matrix_Sync','-')}<br>
                BMU : {data.get('Matrix_BMU','-')}
                </div>""", unsafe_allow_html=True)

        with c2:
            st.subheader("五大神諭盤")
            
            st.markdown(f"""
            <div class="oracle-grid-container">
                <div></div> <div>{get_card_html("引導", guide_kin, oracle_info['guide']['s'], oracle_info['guide']['t'])}</div> <div></div>
                
                <div>{get_card_html("擴展", antipode_kin, oracle_info['antipode']['s'], oracle_info['antipode']['t'])}</div> 
                <div>{get_card_html("主印記", kin, oracle_info['destiny']['s'], oracle_info['destiny']['t'], True)}</div> 
                <div>{get_card_html("支持", analog_kin, oracle_info['analog']['s'], oracle_info['analog']['t'])}</div>
                
                <div></div> <div>{get_card_html("推動", occult_kin, oracle_info['occult']['s'], oracle_info['occult']['t'])}</div> <div></div>
            </div>
            """, unsafe_allow_html=True)

            # 祈禱文與易經
            st.markdown("---")
            if 'IChing_Meaning' in data:
                st.success(f"**☯️ 易經：{data.get('對應卦象','')}**\n\n{data.get('IChing_Meaning','')}")
            
            if '祈禱文' in data:
                with st.expander("📜 祈禱文"):
                    st.write(data['祈禱文'])

# ... (其餘頁面程式碼保持不變) ...
