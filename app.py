import streamlit as st
import datetime
import os
import pandas as pd
import sqlite3
import base64
from create_db import init_db
from kin_utils import (
    calculate_kin_v2, calculate_kin_math, get_full_kin_data, get_oracle, 
    calculate_life_castle, get_img_b64, get_psi_kin, get_goddess_kin,
    get_maya_calendar_info, get_week_key_sentence, get_heptad_prayer,
    get_main_sign_text, save_user_data, get_user_list, get_user_kin, calculate_composite,
    SEAL_FILES, TONE_FILES, SEALS_NAMES, TONE_NAMES 
)

st.set_page_config(page_title="13 Moon Pro", layout="wide", page_icon="🔮")

if not os.path.exists("13moon.db"):
    with st.spinner("系統初始化中..."):
        st.cache_data.clear()
        init_db()
    st.success("初始化完成！")

MIN_USER_YEAR = 1800
MAX_USER_YEAR = 2100
SAFE_DEFAULT_DATE = datetime.date(1990, 1, 1)

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fff; }
    h1, h2, h3 { color: #d4af37 !important; font-family: "Microsoft JhengHei"; }
    .kin-card-grid {
        display: flex; flex-direction: column; align-items: center; justify-content: flex-start; 
        background: #262730; border: 1px solid #444; border-radius: 8px;
        padding: 5px; width: 100%; height: 100%; box-shadow: 0 2px 5px rgba(0,0,0,0.5);
        text-align: center; gap: 0; 
    }
    .oracle-grid-container {
        display: grid; grid-template-columns: 100px 100px 100px;
        grid-template-rows: 100px 140px 100px; gap: 12px; 
        justify-content: center; align-items: center;
    }
    .psi-box { background: linear-gradient(135deg, #2b1055, #7597de); padding: 15px; border-radius: 10px; color: white; margin-top: 20px; }
    .goddess-box { background: linear-gradient(135deg, #7c244c, #d5739c); padding: 15px; border-radius: 10px; color: white; margin-top: 15px; }
    .matrix-data {
        font-family: monospace; color: #00ff00; background: #000;
        padding: 10px; border-radius: 5px; margin-top: 10px; border: 1px solid #004400;
    }
    .concept-text {
        font-size: 14px; color: #aaa; background-color: #1f1f1f; 
        padding: 10px; border-left: 4px solid #d4af37; margin-bottom: 20px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🌌 13 Moon System")
mode = st.sidebar.radio("功能導航", ["個人星系解碼", "52流年城堡", "人員生日管理", "通訊錄/合盤", "系統檢查員"])

def get_card_html(label, kin_num, s_id, t_id, is_main=False):
    s_f = SEAL_FILES.get(s_id, f"{str(s_id).zfill(2)}.png")
    t_f = TONE_FILES.get(t_id, f"tone-{t_id}.png")
    img_s = get_img_b64(f"assets/seals/{s_f}")
    img_t = get_img_b64(f"assets/tones/{t_f}")
    
    display_text = get_main_sign_text(kin_num)
    if "查無" in display_text:
        seal_name = SEALS_NAMES[s_id] if 0 < s_id < 21 else "未知"
        tone_name = TONE_NAMES[t_id] if 0 < t_id < 14 else "未知"
        display_text = f"{tone_name} {seal_name}"

    border = "2px solid gold" if is_main else "1px solid #555"
    return f"""
    <div class="kin-card-grid" style="border:{border};">
        <img src="data:image/png;base64,{img_t}" style="width:30px; filter:invert(1); margin:0 auto 5px auto;">
        <img src="data:image/jpeg;base64,{img_s}" style="width:70px; margin-bottom:5px;">
        <div style="font-size:12px; color:#ddd; line-height:1.2;">{display_text}</div>
        <div style="font-size:10px; color:#888;">KIN {kin_num}</div>
    </div>
    """

if mode == "個人星系解碼":
    st.title("🔮 個人星系印記解碼")
    c1, c2 = st.columns([2,1])
    with c1: date_in = st.date_input("生日", value=SAFE_DEFAULT_DATE, min_value=datetime.date(MIN_USER_YEAR,1,1), max_value=datetime.date(MAX_USER_YEAR,12,31))
    with c2: 
        st.write(""); st.write("")
        go = st.button("🚀 開始解碼", type="primary")
        
    if go or st.session_state.get('run', False):
        st.session_state['run'] = True
        kin, err = calculate_kin_v2(date_in)
        if not kin: st.error(err); kin = calculate_kin_math(date_in)
        
        data = get_full_kin_data(kin)
        oracle = get_oracle(kin)
        psi = get_psi_kin(date_in)
        goddess = get_goddess_kin(kin)
        maya = get_maya_calendar_info(date_in)
        w_key = get_week_key_sentence(maya.get('Maya_Week',''))
        h_prayer = get_heptad_prayer(maya.get('Heptad_Path',''))
        
        st.divider()
        tab_20, tab_28 = st.tabs(["1️⃣3️⃣ : 2️⃣0️⃣ 共時編碼", "1️⃣3️⃣ : 2️⃣8️⃣ 時間循環"])
        
        with tab_20:
            tc1, tc2 = st.columns([1, 1.6])
            with tc1:
                if os.path.exists(f"assets/seals/{data.get('seal_img','' )}"):
                    st.image(f"assets/seals/{data.get('seal_img','')}", width=180)
                st.markdown(f"## KIN {kin}")
                st.markdown(f"### {data.get('主印記','')}")
                st.info(f"🌊 **波符**：{data.get('wave_name','')} 波符")
                st.caption(f"🏰 **城堡**：{data.get('城堡','')}")
                
                if psi and psi['KIN']!=0:
                    st.markdown(f"<div class='psi-box'><h4>🧬 PSI 行星記憶庫</h4><h3>KIN {psi['KIN']}</h3><small>{psi['Info'].get('主印記','')}</small></div>", unsafe_allow_html=True)
                if goddess and goddess['KIN']!=0:
                    st.markdown(f"<div class='goddess-box'><h4>💖 女神力量</h4><h3>KIN {goddess['KIN']}</h3><small>{goddess['Info'].get('主印記','')}</small></div>", unsafe_allow_html=True)
                
                with st.expander("🧬 441 矩陣"):
                    st.markdown(f"<div class='matrix-data'>時間: {data.get('Matrix_Time','-')}<br>空間: {data.get('Matrix_Space','-')}<br>共時: {data.get('Matrix_Sync','-')}<br>BMU : {data.get('Matrix_BMU','-')}</div>", unsafe_allow_html=True)
            
            with tc2:
                st.subheader("五大神諭盤")
                def gk(s, t): return (s + (t-1)*20 -1)%260 + 1
                guide_k = gk(oracle['guide']['s'], oracle['guide']['t'])
                ana_k = gk(oracle['analog']['s'], oracle['analog']['t'])
                anti_k = gk(oracle['antipode']['s'], oracle['antipode']['t'])
                occ_k = gk(oracle['occult']['s'], oracle['occult']['t'])
                
                st.markdown(f"""
                <div class="oracle-grid-container">
                    <div></div> <div>{get_card_html("引導", guide_k, oracle['guide']['s'], oracle['guide']['t'])}</div> <div></div>
                    <div>{get_card_html("擴展", anti_k, oracle['antipode']['s'], oracle['antipode']['t'])}</div> 
                    <div>{get_card_html("主印記", kin, oracle['destiny']['s'], oracle['destiny']['t'], True)}</div> 
                    <div>{get_card_html("支持", ana_k, oracle['analog']['s'], oracle['analog']['t'])}</div>
                    <div></div> <div>{get_card_html("推動", occ_k, oracle['occult']['s'], oracle['occult']['t'])}</div> <div></div>
                </div>""", unsafe_allow_html=True)
                
                st.markdown("---")
                if 'IChing_Meaning' in data: st.success(f"**☯️ {data.get('對應卦象','')}**：{data.get('IChing_Meaning','')}")
                if '祈禱文' in data: 
                    with st.expander("📜 祈禱文"): st.write(data['祈禱文'])

        with tab_28:
            tc1, tc2 = st.columns(2)
            with tc1:
                if maya['Status']=="查詢成功":
                    st.markdown(f"### 🗓️ 瑪雅曆法\n**日期**：{maya['Maya_Date']}\n\n**月**：{maya['Maya_Month']}\n\n**週**：{maya['Maya_Week']}")
                    if w_key: st.info(f"🔑 **本週金句**：{w_key}")
            with tc2:
                st.markdown(f"### 🛣️ 調頻\n**等離子**：{maya['Plasma']}\n\n**路徑**：{maya['Heptad_Path']}")
                if h_prayer: st.success(f"**🙏 祈禱文**：{h_prayer}")

elif mode == "52流年城堡":
    st.title("🏰 52 年生命城堡")
    d = st.date_input("出生日期", datetime.date(1990, 1, 1))
    col_y, col_b = st.columns([2,1])
    with col_y: start_year = st.number_input("起始西元年", 1800, 2100, d.year)
    with col_b: 
        st.write(""); st.write("")
        calc = st.button("計算流年", type="primary")
    
    if calc:
        start_d = datetime.date(start_year, d.month, d.day)
        path = calculate_life_castle(start_d)
        st.subheader(f"週期起始：{start_year} 年")
        cols = st.columns(4)
        for i, row in enumerate(path[:52]):
            with cols[i % 4]:
                info = row['Info']
                s_p = f"assets/seals/{info.get('seal_img','')}"
                img = f'<img src="data:image/png;base64,{get_img_b64(s_p)}" width="40" style="border-radius:50%">' if os.path.exists(s_p) else ""
                st.markdown(f"""<div style="background:{row['Color']}; padding:5px; border-radius:5px; margin-bottom:5px; color:#333; text-align:center; font-size:12px;">
                <b>{row['Age']}歲</b> ({row['Year']})<br><span style="color:#b8860b">KIN {row['KIN']}</span><br>{img}<br>{info.get('波符','')} | {info.get('主印記','')}</div>""", unsafe_allow_html=True)

elif mode == "人員生日管理":
    st.title("👤 人員建檔")
    c1, c2 = st.columns(2)
    name = c1.text_input("姓名")
    dob = c2.date_input("生日", datetime.date(1990,1,1))
    if st.button("💾 存檔", type="primary"):
        kin, _ = calculate_kin_v2(dob)
        if kin:
            sign = get_main_sign_text(kin)
            ok, msg = save_user_data(name, dob.strftime('%Y-%m-%d'), kin, sign)
            if ok: st.success(msg)
            else: st.error(msg)
    st.dataframe(get_user_list())

elif mode == "通訊錄/合盤":
    st.title("❤️ 合盤計算")
    users = get_user_list()
    if not users.empty:
        names = [""] + users['姓名'].tolist()
        c1, c2 = st.columns(2)
        p1 = c1.selectbox("夥伴 A", names)
        p2 = c2.selectbox("夥伴 B", names)
        if p1 and p2 and st.button("計算"):
            k1, _ = get_user_kin(p1, users)
            k2, _ = get_user_kin(p2, users)
            if k1 and k2:
                ck = calculate_composite(k1, k2)
                info = get_full_kin_data(ck)
                st.success(f"🎉 合盤 KIN {ck}：{info.get('主印記','')}")
                if os.path.exists(f"assets/seals/{info.get('seal_img','' )}"): st.image(f"assets/seals/{info.get('seal_img','')}", width=100)
    else: st.warning("請先建檔")
