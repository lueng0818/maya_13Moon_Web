import streamlit as st
import datetime
import os
import pandas as pd
import sqlite3
import base64
from create_db import init_db
from kin_utils import * # 匯入所有函數

# 1. 初始化
st.set_page_config(page_title="13 Moon Pro", layout="wide", page_icon="🔮")

if not os.path.exists("13moon.db"):
    with st.spinner("系統初始化中 (建立資料庫)..."):
        st.cache_data.clear()
        init_db()
    st.success("初始化完成！")

# 獲取年份範圍
MIN_YEAR, MAX_YEAR = get_year_range()
if MIN_YEAR > 1900: MIN_YEAR = 1800 # 強制擴大範圍
if MAX_YEAR < 2100: MAX_YEAR = 2100
SAFE_DATE = datetime.date(1990, 1, 1)

# CSS 美化
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fff; }
    h1, h2, h3 { color: #d4af37 !important; font-family: "Microsoft JhengHei"; }
    
    /* 卡片樣式 */
    .kin-card {
        background: #262730; border: 1px solid #444; border-radius: 10px;
        padding: 10px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    .kin-card:hover { transform: translateY(-5px); border-color: #d4af37; }
    
    /* 資訊區塊 */
    .info-box { padding: 15px; border-radius: 8px; margin-bottom: 10px; color: white; }
    .bg-psi { background: linear-gradient(135deg, #4b0082, #8a2be2); }
    .bg-goddess { background: linear-gradient(135deg, #c71585, #ff69b4); }
    .bg-lunar { background: linear-gradient(135deg, #00008b, #1e90ff); }
    
    /* 神諭盤網格 */
    .oracle-grid {
        display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
        max_width: 320px; margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)

# 側邊欄
st.sidebar.title("🌌 13 Moon System")
mode = st.sidebar.radio("功能導航", ["🔮 個人星系解碼", "🏰 52流年城堡", "👤 人員管理", "❤️ 合盤計算", "🔍 系統檢查"])

# --- 輔助：顯示卡片 ---
def render_card(kin_num, s_id, t_id, label, is_main=False):
    s_f = SEAL_FILES.get(s_id, f"{str(s_id).zfill(2)}.png")
    t_f = TONE_FILES.get(t_id, f"tone-{t_id}.png")
    
    txt = get_main_sign_text(kin_num)
    if "查無" in txt: txt = f"{TONE_NAMES[t_id]} {SEALS_NAMES[s_id]}"
    
    border = "2px solid gold" if is_main else "1px solid #555"
    
    return f"""
    <div class="kin-card" style="border:{border}">
        <div style="font-size:10px; color:#aaa; margin-bottom:5px;">{label}</div>
        <img src="data:image/png;base64,{get_img_b64(f'assets/tones/{t_f}')}" style="width:25px; filter:invert(1);">
        <br>
        <img src="data:image/png;base64,{get_img_b64(f'assets/seals/{s_f}')}" style="width:60px; margin:5px 0;">
        <div style="font-size:12px; font-weight:bold;">{txt}</div>
        <div style="font-size:10px; color:#d4af37;">KIN {kin_num}</div>
    </div>
    """

# ==========================================
# 功能 1: 個人解碼
# ==========================================
if mode == "🔮 個人星系解碼":
    st.title("🔮 個人星系印記解碼")
    
    # 輸入區塊 (使用 Tabs 切換輸入方式，更直觀)
    tab_date, tab_user = st.tabs(["📅 自訂日期", "👤 從通訊錄選擇"])
    
    date_in = SAFE_DATE
    
    with tab_date:
        date_in = st.date_input("選擇生日", value=SAFE_DATE, min_value=datetime.date(MIN_YEAR,1,1), max_value=datetime.date(MAX_YEAR,12,31))
    
    with tab_user:
        users = get_user_list()
        if not users.empty:
            u_name = st.selectbox("選擇人員", users['姓名'].tolist())
            if u_name:
                u_row = users[users['姓名']==u_name].iloc[0]
                try: date_in = datetime.datetime.strptime(u_row['生日'], "%Y-%m-%d").date()
                except: pass
                st.info(f"已選取：{u_name} ({date_in})")
        else: st.warning("通訊錄為空")

    if st.button("🚀 開始解碼", type="primary", use_container_width=True):
        # 計算
        kin, err = calculate_kin_v2(date_in)
        if not kin: st.warning(err); kin = calculate_kin_math(date_in)
        
        # 獲取資料
        data = get_full_kin_data(kin)
        oracle = get_oracle(kin)
        psi = get_psi_kin(date_in)
        goddess = get_goddess_kin(kin)
        maya = get_maya_calendar_info(date_in)
        wk_key = get_week_key_sentence(maya.get('Maya_Week'))
        prayer = get_heptad_prayer(maya.get('Heptad_Path'))
        
        st.divider()
        
        # 雙核心展示
        col_20, col_28 = st.columns(2)
        
        # 左欄：13:20
        with col_20:
            st.subheader("🌌 13:20 共時序")
            st.info(f"**KIN {kin} {data.get('主印記','')}**\n\n🌊 {data.get('wave_name','')}波符 | 🏰 {data.get('城堡','')}")
            
            # PSI & Goddess
            c_p, c_g = st.columns(2)
            with c_p:
                if psi and psi['KIN']:
                    st.markdown(f"<div class='info-box bg-psi'><b>🧬 PSI</b><br>KIN {psi['KIN']}<br><small>{psi['Info'].get('主印記','')}</small></div>", unsafe_allow_html=True)
            with c_g:
                if goddess and goddess['KIN']:
                    st.markdown(f"<div class='info-box bg-goddess'><b>💖 女神</b><br>KIN {goddess['KIN']}<br><small>{goddess['Info'].get('主印記','')}</small></div>", unsafe_allow_html=True)
            
            # 神諭盤
            def gk(s, t): return (s + (t-1)*20 -1)%260 + 1
            
            guide_html = render_card(gk(oracle['guide']['s'], oracle['guide']['t']), oracle['guide']['s'], oracle['guide']['t'], "引導")
            anti_html = render_card(gk(oracle['antipode']['s'], oracle['antipode']['t']), oracle['antipode']['s'], oracle['antipode']['t'], "擴展")
            main_html = render_card(kin, oracle['destiny']['s'], oracle['destiny']['t'], "主印記", True)
            ana_html = render_card(gk(oracle['analog']['s'], oracle['analog']['t']), oracle['analog']['s'], oracle['analog']['t'], "支持")
            occ_html = render_card(gk(oracle['occult']['s'], oracle['occult']['t']), oracle['occult']['s'], oracle['occult']['t'], "推動")
            
            st.markdown(f"""
            <div class="oracle-grid">
                <div></div> <div>{guide_html}</div> <div></div>
                <div>{anti_html}</div> <div>{main_html}</div> <div>{ana_html}</div>
                <div></div> <div>{occ_html}</div> <div></div>
            </div>
            """, unsafe_allow_html=True)

        # 右欄：13:28
        with col_28:
            st.subheader("🗓️ 13:28 週期序")
            
            # 顯示日期資訊
            if maya['Status'] == "查詢成功":
                st.markdown(f"""
                <div class="info-box bg-lunar">
                    <h3>{maya['Maya_Date']}</h3>
                    <p>{maya['Maya_Month']} | {maya['Maya_Week']}</p>
                    <hr>
                    <p>🌞 等離子：{maya['Plasma']}</p>
                    <p>🛣️ 路徑：{maya['Heptad_Path']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if wk_key: st.success(f"🔑 **週金句**：{wk_key}")
                if prayer: st.info(f"🙏 **祈禱文**：\n\n{prayer}")
            else:
                st.error("查無瑪雅曆法資料，請確認日期範圍。")

# ==========================================
# 功能 2: 52 流年
# ==========================================
elif mode == "🏰 52流年城堡":
    st.title("🏰 52 年生命城堡")
    
    t1, t2 = st.tabs(["自訂輸入", "通訊錄選擇"])
    d = SAFE_DATE
    with t1: d = st.date_input("出生日期", SAFE_DATE)
    with t2: 
        us = get_user_list()
        if not us.empty:
            u = st.selectbox("人員", us['姓名'])
            if u: d = datetime.datetime.strptime(us[us['姓名']==u].iloc[0]['生日'], "%Y-%m-%d").date()

    sy = st.number_input("起始西元年", MIN_YEAR, MAX_YEAR, d.year)
    
    if st.button("計算流年"):
        path = calculate_life_castle(datetime.date(sy, d.month, d.day))
        st.subheader(f"週期起始：{sy} 年")
        
        cols = st.columns(4)
        for i, r in enumerate(path[:52]):
            with cols[i%4]:
                inf = r['Info']
                img = f'<img src="data:image/png;base64,{get_img_b64(f"assets/seals/{inf.get("seal_img","")}")}" width="30">'
                st.markdown(f"""
                <div style="background:{r['Color']}; color:#333; padding:5px; border-radius:5px; margin-bottom:5px; text-align:center; font-size:12px;">
                    <b>{r['Age']}歲</b> ({r['Year']})<br>
                    <span style="color:#b8860b">KIN {r['KIN']}</span><br>
                    {img}<br>
                    {inf.get('主印記','')}
                </div>""", unsafe_allow_html=True)

# ==========================================
# 功能 3: 人員管理
# ==========================================
elif mode == "👤 人員管理":
    st.title("👤 人員建檔")
    c1, c2 = st.columns(2)
    nm = c1.text_input("姓名")
    db = c2.date_input("生日", SAFE_DATE)
    
    if st.button("💾 存檔", type="primary"):
        k, _ = calculate_kin_v2(db)
        if k:
            s = get_main_sign_text(k)
            ok, m = save_user_data(nm, db.strftime('%Y-%m-%d'), k, s)
            if ok: st.success(m)
            else: st.error(m)
    
    st.markdown("---")
    st.dataframe(get_user_list(), use_container_width=True)

# ... (合盤與系統檢查保持不變) ...
elif mode == "❤️ 合盤計算":
    st.title("❤️ 關係合盤")
    us = get_user_list()
    if not us.empty:
        ns = [""] + us['姓名'].tolist()
        p1 = st.selectbox("夥伴 A", ns)
        p2 = st.selectbox("夥伴 B", ns)
        if p1 and p2 and st.button("計算"):
            k1, _ = get_user_kin(p1, us)
            k2, _ = get_user_kin(p2, us)
            ck = calculate_composite(k1, k2)
            ci = get_full_kin_data(ck)
            st.success(f"🎉 合盤 KIN {ck}：{ci.get('主印記','')}")
            if os.path.exists(f"assets/seals/{ci.get('seal_img','')}"):
                st.image(f"assets/seals/{ci.get('seal_img','')}", width=100)

elif mode == "🔍 系統檢查":
    st.title("🔍 系統檢查")
    if os.path.exists("13moon.db"):
        conn = sqlite3.connect("13moon.db")
        st.success("資料庫連線正常")
        st.write("表格清單:", pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn))
        conn.close()
