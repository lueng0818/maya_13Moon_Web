import streamlit as st
import datetime
import os
import pandas as pd
import sqlite3
import base64
from create_db import init_db
from kin_utils import *

# 1. 初始化
st.set_page_config(page_title="13 Moon Pro", layout="wide", page_icon="🔮")

if not os.path.exists("13moon.db"):
    with st.spinner("系統初始化中 (建立資料庫)..."):
        st.cache_data.clear()
        init_db()
    st.success("完成！")

MIN_YEAR, MAX_YEAR = get_year_range()
if MIN_YEAR > 1800: MIN_YEAR = 1800
if MAX_YEAR < 2100: MAX_YEAR = 2100
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
mode = st.sidebar.radio("功能導航", [
    "個人星系解碼", "個人流年查詢", "52流年城堡", 
    "PSI查詢", "女神印記查詢", "對等印記查詢", "全腦調頻", "國王棋盤",
    "人員生日管理", "通訊錄/合盤", "系統檢查員"
])

# --- 共用函數 ---
def get_card_html(label, kin_num, s_id, t_id, is_main=False):
    s_f = SEAL_FILES.get(s_id, f"{str(s_id).zfill(2)}.png")
    t_f = TONE_FILES.get(t_id, f"tone-{t_id}.png")
    img_s = get_img_b64(f"assets/seals/{s_f}")
    img_t = get_img_b64(f"assets/tones/{t_f}")
    txt = get_main_sign_text(kin_num)
    if "查無" in txt: txt = f"{TONE_NAMES[t_id]} {SEALS_NAMES[s_id]}"
    border = "2px solid gold" if is_main else "1px solid #555"
    return f"""<div class="kin-card-grid" style="border:{border};"><img src="data:image/png;base64,{img_t}" style="width:30px; filter:invert(1); margin:0 auto 5px auto;"><img src="data:image/jpeg;base64,{img_s}" style="width:70px; margin-bottom:5px;"><div style="font-size:12px; color:#ddd; line-height:1.2;">{txt}</div><div style="font-size:10px; color:#888;">KIN {kin_num}</div></div>"""

def render_date_selector(key_prefix=""):
    m = st.radio("輸入方式", ["📅 自訂", "👤 通訊錄"], horizontal=True, key=f"{key_prefix}_m")
    d = SAFE_DATE; u = ""
    if m == "📅 自訂":
        d = st.date_input("生日", value=SAFE_DATE, min_value=datetime.date(MIN_YEAR,1,1), max_value=datetime.date(MAX_YEAR,12,31), key=f"{key_prefix}_d")
    else:
        us = get_user_list()
        if not us.empty:
            sel = st.selectbox("選擇人員", us['姓名'], key=f"{key_prefix}_u")
            if sel:
                u = sel
                try: d = datetime.datetime.strptime(us[us['姓名']==sel].iloc[0]['生日'], "%Y-%m-%d").date()
                except: st.error("日期錯誤")
        else: st.warning("無資料")
    return d, u

def show_basic_result(kin, data):
    if os.path.exists(f"assets/seals/{data.get('seal_img','' )}"):
        st.image(f"assets/seals/{data.get('seal_img','')}", width=150)
    st.markdown(f"## KIN {kin}")
    st.markdown(f"### {data.get('主印記','')}")
    st.info(f"🌊 **波符**：{data.get('wave_name','')} 波符")

# ==========================================
# 頁面 1: 個人星系解碼
# ==========================================
if mode == "個人星系解碼":
    st.title("🔮 個人星系印記解碼")
    date_in, _ = render_date_selector("main")
    if st.button("🚀 開始解碼", type="primary"):
        kin, err = calculate_kin_v2(date_in)
        if not kin: kin = calculate_kin_math(date_in)
        data = get_full_kin_data(kin)
        oracle = get_oracle(kin)
        psi = get_psi_kin(date_in)
        goddess = get_goddess_kin(kin)
        maya = get_maya_calendar_info(date_in)
        wk = get_week_key_sentence(maya.get('Maya_Week'))
        pr = get_heptad_prayer(maya.get('Heptad_Path'))
        
        st.divider()
        t1, t2 = st.tabs(["1️⃣3️⃣ : 2️⃣0️⃣ 共時編碼", "1️⃣3️⃣ : 2️⃣8️⃣ 時間循環"])
        
        with t1:
            c1, c2 = st.columns([1, 1.6])
            with c1:
                show_basic_result(kin, data)
                if psi and psi['KIN']: st.markdown(f"<div class='psi-box'><h4>🧬 PSI</h4>KIN {psi['KIN']} {psi['Info'].get('主印記','')}</div>", unsafe_allow_html=True)
                if goddess and goddess['KIN']: st.markdown(f"<div class='goddess-box'><h4>💖 女神</h4>KIN {goddess['KIN']} {goddess['Info'].get('主印記','')}</div>", unsafe_allow_html=True)
                with st.expander("🧬 矩陣"): st.write(f"BMU: {data.get('BMU_Position','-')}")
            with c2:
                st.subheader("五大神諭")
                def gk(s, t): return (s + (t-1)*20 -1)%260 + 1
                st.markdown(f"""<div class="oracle-grid-container">
                    <div></div> <div>{get_card_html("引導", gk(oracle['guide']['s'],oracle['guide']['t']), oracle['guide']['s'], oracle['guide']['t'])}</div> <div></div>
                    <div>{get_card_html("擴展", gk(oracle['antipode']['s'],oracle['antipode']['t']), oracle['antipode']['s'], oracle['antipode']['t'])}</div> 
                    <div>{get_card_html("主印記", kin, oracle['destiny']['s'], oracle['destiny']['t'], True)}</div> 
                    <div>{get_card_html("支持", gk(oracle['analog']['s'],oracle['analog']['t']), oracle['analog']['s'], oracle['analog']['t'])}</div>
                    <div></div> <div>{get_card_html("推動", gk(oracle['occult']['s'],oracle['occult']['t']), oracle['occult']['s'], oracle['occult']['t'])}</div> <div></div>
                </div>""", unsafe_allow_html=True)
                if '祈禱文' in data: st.info(data['祈禱文'])

        with t2:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"<div class='lunar-bg'><h3>{maya['Solar_Year']}</h3><h2>{maya['Maya_Date']}</h2></div>", unsafe_allow_html=True)
                if wk: st.success(wk)
            with c2:
                st.info(f"等離子: {maya['Plasma']}\n\n路徑: {maya['Heptad_Path']}")
                if pr: st.write(pr)

# ==========================================
# 頁面: PSI / 女神 / 對等 (單獨查詢)
# ==========================================
elif mode == "PSI查詢":
    st.title("🧬 PSI 行星記憶庫查詢")
    d, _ = render_date_selector("psi")
    if st.button("查詢"):
        res = get_psi_kin(d)
        if res and res['KIN']:
            st.success(f"PSI: KIN {res['KIN']}")
            show_basic_result(res['KIN'], res['Info'])
            st.info(f"矩陣位置: {res.get('Matrix','-')}")
        else: st.warning("查無資料")

elif mode == "女神印記查詢":
    st.title("💖 女神印記查詢")
    d, _ = render_date_selector("god")
    if st.button("查詢"):
        k, _ = calculate_kin_v2(d)
        if not k: k = calculate_kin_math(d)
        res = get_goddess_kin(k)
        st.success(f"女神: KIN {res['KIN']}")
        show_basic_result(res['KIN'], res['Info'])
        st.caption(f"源頭隱藏印記: KIN {res['Base_KIN']}")

elif mode == "對等印記查詢":
    st.title("🔄 對等印記查詢")
    d, _ = render_date_selector("eq")
    if st.button("查詢"):
        k, _ = calculate_kin_v2(d)
        if not k: k = calculate_kin_math(d)
        res = calculate_equivalent_kin(k)
        if res:
            st.success(f"TFI: {res['TFI']} -> 對等 KIN {res['Eq_Kin']}")
            show_basic_result(res['Eq_Kin'], res['Eq_Info'])
            st.write("計算細節:", res['Coords'])
        else: st.error("矩陣資料不足，無法計算")

# ==========================================
# 頁面: 流年 / 52城堡
# ==========================================
elif mode == "個人流年查詢":
    st.title("📅 個人流年查詢")
    d, _ = render_date_selector("flow")
    ty = st.number_input("流年年份", 1900, 2100, datetime.date.today().year)
    if st.button("查詢"):
        bk, _ = calculate_kin_v2(d)
        if not bk: bk = calculate_kin_math(d)
        age = ty - d.year
        fk = (bk + age*105)%260
        if fk==0: fk=260
        st.subheader(f"{ty} 年 ( {age} 歲 )")
        show_basic_result(fk, get_full_kin_data(fk))

elif mode == "52流年城堡":
    st.title("🏰 52 年生命城堡")
    d, _ = render_date_selector("castle")
    sy = st.number_input("起始年", 1800, 2100, d.year)
    if st.button("計算"):
        path = calculate_life_castle(datetime.date(sy, d.month, d.day))
        cols = st.columns(4)
        for i, r in enumerate(path[:52]):
            with cols[i%4]:
                st.markdown(f"<div style='background:{r['Color']}; padding:5px; border-radius:5px; margin-bottom:5px; color:black; text-align:center;'><b>{r['Age']}歲</b><br>KIN {r['KIN']}<br><small>{r['Info'].get('主印記','')}</small></div>", unsafe_allow_html=True)

# ==========================================
# 頁面: 全腦調頻 / 國王棋盤
# ==========================================
elif mode == "全腦調頻":
    st.title("🧠 全腦調頻")
    data = get_whole_brain_tuning()
    if data:
        for item in data:
            with st.expander(f"{item['全腦調頻_對應腦部']}"):
                st.write(item['全腦調頻_調頻語'])
    else: st.warning("無資料")

elif mode == "國王棋盤":
    st.title("👑 國王預言棋盤")
    df = get_king_prophecy()
    if not df.empty: st.dataframe(df)
    else: st.warning("無資料")

# ==========================================
# 頁面: 管理與合盤
# ==========================================
elif mode == "人員生日管理":
    st.title("👤 人員管理")
    t1, t2, t3 = st.tabs(["新增", "列表/編輯", "匯入/匯出"])
    
    with t1:
        c1, c2 = st.columns(2)
        n = c1.text_input("姓名")
        db = c2.date_input("生日", SAFE_DATE)
        if st.button("存檔"):
            k, _ = calculate_kin_v2(db)
            if k:
                ok, m = save_user_data(n, db.strftime('%Y-%m-%d'), k, get_main_sign_text(k))
                if ok: st.success(m)
                else: st.error(m)
    
    with t2:
        df = get_user_list()
        st.dataframe(df)
        if not df.empty:
            sel = st.selectbox("編輯對象", df['姓名'])
            if sel:
                row = df[df['姓名']==sel].iloc[0]
                nn = st.text_input("新姓名", value=sel)
                nd = st.date_input("新生日", value=datetime.datetime.strptime(row['生日'],"%Y-%m-%d").date())
                c_up, c_del = st.columns(2)
                if c_up.button("更新"):
                    nk, _ = calculate_kin_v2(nd)
                    from kin_utils import update_user_data
                    update_user_data(sel, nn, nd.strftime('%Y-%m-%d'), nk, get_main_sign_text(nk))
                    st.success("更新成功"); st.rerun()
                if c_del.button("刪除"):
                    from kin_utils import delete_user_data
                    delete_user_data([sel])
                    st.success("已刪除"); st.rerun()

    with t3:
        st.download_button("匯出 CSV", df.to_csv(index=False).encode('utf-8-sig'), "users.csv")
        up = st.file_uploader("匯入 CSV", type="csv")
        if up and st.button("開始匯入"):
            try:
                d_in = pd.read_csv(up)
                for _, r in d_in.iterrows():
                    try:
                        dd = datetime.date(int(r['出生年']), int(r['出生月']), int(r['出生日']))
                        kk, _ = calculate_kin_v2(dd)
                        save_user_data(r['姓名'], dd.strftime('%Y-%m-%d'), kk, get_main_sign_text(kk))
                    except: pass
                st.success("匯入完成")
            except: st.error("格式錯誤")

elif mode == "通訊錄/合盤":
    st.title("❤️ 關係合盤")
    us = get_user_list()
    ns = [""] + us['姓名'].tolist() if not us.empty else []
    p1 = st.selectbox("A", ns)
    p2 = st.selectbox("B", ns)
    if p1 and p2 and st.button("計算"):
        k1, _ = get_user_kin(p1, us)
        k2, _ = get_user_kin(p2, us)
        if k1 and k2:
            ck = calculate_composite(k1, k2)
            info = get_full_kin_data(ck)
            st.success(f"合盤 KIN {ck}：{info.get('主印記','')}")
            show_basic_result(ck, info)

elif mode == "系統檢查員":
    st.title("🔍 系統檢查")
    if os.path.exists("13moon.db"):
        conn = sqlite3.connect("13moon.db")
        st.write(pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn))
        conn.close()
