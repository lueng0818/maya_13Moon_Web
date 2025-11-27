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

if not os.path.exists("13moon.db"):
    with st.spinner("系統初始化中 (建立資料庫)..."):
        st.cache_data.clear()
        init_db()
    st.success("初始化完成！")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fff; }
    h1, h2, h3 { color: #d4af37 !important; font-family: "Microsoft JhengHei"; }
    .kin-card-grid {
        background: #262730; border: 1px solid #444; border-radius: 8px;
        padding: 5px; width: 100%; height: 100%; box-shadow: 0 2px 5px rgba(0,0,0,0.5);
    }
    .psi-box {
        background: linear-gradient(135deg, #2b1055, #7597de);
        padding: 15px; border-radius: 10px; color: white; margin-top: 20px;
    }
    .matrix-data {
        font-family: monospace; color: #00ff00; background: #000;
        padding: 10px; border-radius: 5px; margin-top: 10px; border: 1px solid #004400;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🌌 13 Moon System")
mode = st.sidebar.radio("功能導航", ["個人星系解碼", "52流年城堡", "通訊錄/合盤", "系統檢查員"])

# --- 輔助顯示卡片 (保持不變) ---
def get_card_html(label, s_id, t_id, is_main=False):
    s_f = SEAL_FILES.get(s_id, f"{str(s_id).zfill(2)}.png")
    t_f = TONE_FILES.get(t_id, f"tone-{t_id}.png")
    img_s = get_img_b64(f"assets/seals/{s_f}")
    img_t = get_img_b64(f"assets/tones/{t_f}")
    border = "2px solid gold" if is_main else "1px solid #555"
    return f"""
    <div class="kin-card-grid" style="border:{border}; background:#222;">
        <img src="data:image/png;base64,{img_t}" style="width:20px; filter:invert(1);">
        <img src="data:image/png;base64,{img_s}" style="width:50px; margin-top:2px;">
        <div style="font-size:10px; color:#aaa;">{label}</div>
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
        oracle = get_oracle(kin)
        psi_data = get_psi_kin(date_in)
        
        st.divider()
        c1, c2 = st.columns([1, 1.6])
        
        with c1:
            s_path = f"assets/seals/{data.get('seal_img','')}"
            if os.path.exists(s_path):
                st.image(s_path, width=180)
            
            st.markdown(f"## KIN {kin}")
            st.markdown(f"### {data.get('主印記','')}")
            
            # 【關鍵】顯示波符
            st.info(f"🌊 **波符**：{data.get('波符','未知')} 波符")
            st.caption(f"🏰 **城堡**：{data.get('城堡','未知')}")
            
            # PSI 區塊
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
            
            # ... (五大神諭的 HTML Grid 繪製邏輯保持不變) ...
            
            html_guide = get_card_html("引導", oracle['guide']['s'], oracle['guide']['t'])
            html_anti  = get_card_html("擴展", oracle['antipode']['s'], oracle['antipode']['t'])
            html_main  = get_card_html("主印記", oracle['destiny']['s'], oracle['destiny']['t'], True)
            html_analog= get_card_html("支持", oracle['analog']['s'], oracle['analog']['t'])
            html_occult= get_card_html("推動", oracle['occult']['s'], oracle['occult']['t'])

            st.markdown(f"""
            <div style="display: grid; grid-template-columns: 80px 80px 80px; grid-template-rows: 90px 90px 90px; gap: 10px; justify-content: center;">
                <div></div> <div>{html_guide}</div> <div></div>
                <div>{html_anti}</div> <div>{html_main}</div> <div>{html_analog}</div>
                <div></div> <div>{html_occult}</div> <div></div>
            </div>
            """, unsafe_allow_html=True)

            if 'IChing_Meaning' in data:
                st.markdown("---")
                st.success(f"**☯️ {data.get('對應卦象','')}**：{data.get('IChing_Meaning','')}")

# ... (其餘頁面程式碼保持不變) ...
