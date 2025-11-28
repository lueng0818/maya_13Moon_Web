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
    get_main_sign_text, save_user_data, get_user_list, get_user_kin, 
    calculate_composite, get_year_range, get_octave_positions,
    SEAL_FILES, TONE_FILES, SEALS_NAMES, TONE_NAMES 
)

# 1. 初始化
st.set_page_config(page_title="13 Moon Pro", layout="wide", page_icon="🔮")

if not os.path.exists("13moon.db"):
    with st.spinner("系統初始化中..."):
        st.cache_data.clear()
        init_db()
    st.success("完成！")

# 動態獲取年份範圍
MIN_YEAR, MAX_YEAR = get_year_range()
SAFE_DATE = datetime.date(1990, 1, 1)

# CSS
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
    .lunar-bg { background: linear-gradient(135deg, #1e3c72, #2a5298); padding: 15px; border-radius: 10px; color: white; margin-bottom: 15px; }
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
mode = st.sidebar.radio("功能導航", ["個人星系解碼", "52流年城堡", "人員生日管理", "通訊錄/合盤", "八度音階查詢", "系統檢查員"])

# 卡片顯示函數
def get_card_html(kin_num, s_id, t_id, is_main=False):
    s_f = SEAL_FILES.get(s_id, f"{str(s_id).zfill(2)}.png")
    t_f = TONE_FILES.get(t_id, f"tone-{t_id}.png")
    img_s = get_img_b64(f"assets/seals/{s_f}")
    img_t = get_img_b64(f"assets/tones/{t_f}")
    
    txt = get_main_sign_text(kin_num)
    if "查無" in txt: txt = f"{TONE_NAMES[t_id]} {SEALS_NAMES[s_id]}"
    
    border = "2px solid gold" if is_main else "1px solid #555"
    return f"""<div class="kin-card-grid" style="border:{border};"><img src="data:image/png;base64,{img_t}" style="width:30px; filter:invert(1); margin:0 auto 5px auto;"><img src="data:image/jpeg;base64,{img_s}" style="width:70px; margin-bottom:5px;"><div style="font-size:12px; color:#ddd; line-height:1.2;">{txt}</div><div style="font-size:10px; color:#888;">KIN {kin_num}</div></div>"""

# --- 頁面邏輯 ---
if mode == "個人星系解碼":
    st.title("🔮 個人星系印記解碼")
    c1, c2 = st.columns([2,1])
    with c1: date_in = st.date_input("生日", value=SAFE_DATE, min_value=datetime.date(MIN_YEAR,1,1), max_value=datetime.date(MAX_YEAR,12,31))
    with c2: 
        st.write(""); st.write("")
        go = st.button("🚀 開始解碼", type="primary")
        
    if go or st.session_state.get('run'):
        st.session_state['run'] = True
        kin, err = calculate_kin_v2(date_in)
        if not kin: st.error(err); kin = calculate_kin_math(date_in)
        
        data = get_full_kin_data(kin)
        oracle = get_oracle(kin)
        psi = get_psi_kin(date_in)
        goddess = get_goddess_kin(kin)
        maya = get_maya_calendar_info(date_in)
        wk_key = get_week_key_sentence(maya.get('Maya_Week',''))
        h_prayer = get_heptad_prayer(maya.get('Heptad_Path',''))
        
        st.divider()
        t1, t2 = st.tabs(["1️⃣3️⃣ : 2️⃣0️⃣ 共時編碼", "1️⃣3️⃣ : 2️⃣8️⃣ 時間循環"])
        
        with t1:
            st.markdown("<div class='concept-text'><b>13:20 共時編碼：</b>結合13調性與20圖騰，理解時間的潛在結構與靈魂頻率。</div>", unsafe_allow_html=True)
            tc1, tc2 = st.columns([1, 1.6])
            
            with tc1:
                if os.path.exists(f"assets/seals/{data.get('seal_img','')}"): st.image(f"assets/seals/{data.get('seal_img','')}", width=180)
                st.markdown(f"## KIN {kin}")
                st.markdown(f"### {data.get('主印記','')}")
                st.info(f"🌊 **波符**：{data.get('wave_name','')} 波符")
                
                if psi and psi['KIN']: st.markdown(f"<div class='psi-box'><h4>🧬 PSI 行星記憶庫</h4><h3>KIN {psi['KIN']}</h3><small>{psi['Info'].get('主印記','')}</small></div>", unsafe_allow_html=True)
                if goddess and goddess['KIN']: st.markdown(f"<div class='goddess-box'><h4>💖 女神力量</h4><h3>KIN {goddess['KIN']}</h3><small>{goddess['Info'].get('主印記','')}</small></div>", unsafe_allow_html=True)
                
                with st.expander("✨ 進階星際密碼"):
                    st.markdown(f"**原型**：{data.get('星際原型','-')}<br>**BMU**：{data.get('BMU','-')}<br>**行星**：{data.get('行星','-')}<br>**家族**：{data.get('家族','-')}", unsafe_allow_html=True)
                
                with st.expander("🧬 441 矩陣數據"):
                    st.markdown(f"<div class='matrix-data'>基礎BMU: {data.get('BMU_Position','-')}<br>音符: {data.get('BMU_Note','-')}<br>腦部: {data.get('BMU_Brain','-')}<hr>時間: {data.get('Matrix_Time','-')}<br>空間: {data.get('Matrix_Space','-')}<br>共時: {data.get('Matrix_Sync','-')}</div>", unsafe_allow_html=True)

            with tc2:
                st.subheader("五大神諭盤")
                def gk(s, t): return (s + (t-1)*20 -1)%260 + 1
                k_g = gk(oracle['guide']['s'], oracle['guide']['t'])
                k_an = gk(oracle['analog']['s'], oracle['analog']['t'])
                k_anti = gk(oracle['antipode']['s'], oracle['antipode']['t'])
                k_occ = gk(oracle['occult']['s'], oracle['occult']['t'])
                
                st.markdown(f"""<div class="oracle-grid-container">
                    <div></div> <div>{get_card_html(k_g, oracle['guide']['s'], oracle['guide']['t'])}</div> <div></div>
                    <div>{get_card_html(k_anti, oracle['antipode']['s'], oracle['antipode']['t'])}</div> 
                    <div>{get_card_html(kin, oracle['destiny']['s'], oracle['destiny']['t'], True)}</div> 
                    <div>{get_card_html(k_an, oracle['analog']['s'], oracle['analog']['t'])}</div>
                    <div></div> <div>{get_card_html(k_occ, oracle['occult']['s'], oracle['occult']['t'])}</div> <div></div>
                </div>""", unsafe_allow_html=True)
                
                st.markdown("---")
                if 'IChing_Meaning' in data: st.success(f"**☯️ 易經：{data.get('對應卦象','')}**\n\n{data.get('IChing_Meaning','')}")
                if '祈禱文' in data: 
                    with st.expander("📜 查看祈禱文"): st.write(data['祈禱文'])

        with t2:
            st.markdown("<div class='concept-text'><b>13:28 時間循環：</b>13個月x28天+無時間日，與自然韻律同步。</div>", unsafe_allow_html=True)
            lc1, lc2 = st.columns(2)
            with lc1:
                st.markdown(f"<div class='lunar-bg'><h3>🗓️ {maya['Solar_Year']}</h3><h2>{maya['Maya_Date']}</h2><p><b>月</b>：{maya['Maya_Month']}<br><b>週</b>：{maya['Maya_Week']}</p></div>", unsafe_allow_html=True)
                if wk_key: st.info(f"🔑 **週金句**：{wk_key}")
            with lc2:
                st.subheader("🛣️ 每日調頻")
                st.success(f"**等離子**：{maya['Plasma']}\n\n**路徑**：{maya['Heptad_Path']}")
                if h_prayer: 
                    with st.expander("🙏 七價祈禱文"): st.write(h_prayer)

elif mode == "52流年城堡":
    st.title("🏰 52 年生命城堡")
    d = st.date_input("出生日期", value=SAFE_DATE, min_value=datetime.date(MIN_YEAR,1,1), max_value=datetime.date(MAX_YEAR,12,31))
    col_y, col_b = st.columns([1.5, 2])
    with col_y: sy = st.number_input("起始西元年 (遇年改年)", MIN_YEAR, MAX_YEAR, d.year)
    with col_b: 
        st.write(""); st.write("")
        if st.button("計算流年", type="primary"):
            path = calculate_life_castle(datetime.date(sy, d.month, d.day))
            st.subheader(f"週期起始：{sy} 年")
            cols = st.columns(4)
            for i, r in enumerate(path[:52]):
                with cols[i%4]:
                    inf = r['Info']
                    sp = f"assets/seals/{inf.get('seal_img','')}"
                    im = f'<img src="data:image/png;base64,{get_img_b64(sp)}" width="40">' if os.path.exists(sp) else ""
                    st.markdown(f"<div style='background:{r['Color']}; padding:5px; border-radius:5px; margin-bottom:5px; color:#333; text-align:center; font-size:12px;'><b>{r['Age']}歲</b> ({r['Year']})<br><span style='color:#b8860b'>KIN {r['KIN']}</span><br>{im}<br>{inf.get('波符','')} | {inf.get('主印記','')}</div>", unsafe_allow_html=True)

elif mode == "人員生日管理":
    st.title("👤 人員建檔")
    c1, c2 = st.columns(2)
    nm = c1.text_input("姓名")
    db = c2.date_input("生日", value=SAFE_DATE, min_value=datetime.date(MIN_YEAR,1,1), max_value=datetime.date(MAX_YEAR,12,31))
    if st.button("💾 存檔", type="primary"):
        k, _ = calculate_kin_v2(db)
        if k:
            ok, msg = save_user_data(nm, db.strftime('%Y-%m-%d'), k, get_main_sign_text(k))
            if ok: st.success(msg)
            else: st.error(msg)
        else: st.error("日期計算失敗")
    st.dataframe(get_user_list())

elif mode == "通訊錄/合盤":
    st.title("❤️ 關係合盤")
    usrs = get_user_list()
    if not usrs.empty:
        nms = [""] + usrs['姓名'].tolist()
        p1 = st.selectbox("夥伴 A", nms)
        p2 = st.selectbox("夥伴 B", nms)
        if p1 and p2 and st.button("計算合盤"):
            k1, _ = get_user_kin(p1, usrs)
            k2, _ = get_user_kin(p2, usrs)
            if k1 and k2:
                ck = calculate_composite(k1, k2)
                ci = get_full_kin_data(ck)
                st.success(f"🎉 合盤 KIN {ck}：{ci.get('主印記','')}")
                if os.path.exists(f"assets/seals/{ci.get('seal_img','')}"): st.image(f"assets/seals/{ci.get('seal_img','')}", width=100)
                st.info(f"波符：{ci.get('wave_name','')}")
    else: st.warning("請先至人員管理建檔")

elif mode == "八度音階查詢":
    st.title("🎵 八度音階查詢")
    note = st.selectbox("選擇音符", ['Do','Re','Mi','Fa','Sol','La','Si',"Do'"])
    if st.button("查詢"):
        from kin_utils import get_octave_positions
        st.dataframe(pd.DataFrame(get_octave_positions(note)))

elif mode == "系統檢查員":
    st.title("🔍 系統檢查")
    if os.path.exists("13moon.db"):
        conn = sqlite3.connect("13moon.db")
        st.success("資料庫連線正常")
        st.write("表格清單:", pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn))
        conn.close()
    else: st.error("資料庫遺失")
