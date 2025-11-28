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
    with st.spinner("系統初始化中..."):
        st.cache_data.clear()
        init_db()
    st.success("完成！")

MIN_YEAR, MAX_YEAR = get_year_range()
if MIN_YEAR > 1800: MIN_YEAR = 1800
if MAX_USER_YEAR := 2100: pass
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
mode = st.sidebar.radio("功能導航", ["個人星系解碼", "52流年城堡", "人員管理系統", "通訊錄/合盤", "系統檢查員"])

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

# --- 1. 個人解碼 ---
if mode == "個人星系解碼":
    st.title("🔮 個人星系印記解碼")
    c1, c2 = st.columns([2,1])
    with c1: date_in, _ = render_date_selector("decode")
    with c2: 
        st.write(""); st.write("")
        go = st.button("🚀 開始解碼", type="primary")
        
    if go or st.session_state.get('run'):
        st.session_state['run'] = True
        kin, err = calculate_kin_v2(date_in)
        if not kin: st.warning(err); kin = calculate_kin_math(date_in)
        
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
            st.markdown("<div class='concept-text'><b>13:20 共時編碼：</b>結合13調性與20圖騰，理解時間的潛在結構與靈魂頻率。</div>", unsafe_allow_html=True)
            tc1, tc2 = st.columns([1, 1.6])
            with tc1:
                if os.path.exists(f"assets/seals/{data.get('seal_img','')}"): st.image(f"assets/seals/{data.get('seal_img','')}", width=180)
                st.markdown(f"## KIN {kin}")
                st.markdown(f"### {data.get('主印記','')}")
                st.info(f"🌊 **波符**：{data.get('wave_name','')} 波符")
                if psi and psi['KIN']: st.markdown(f"<div class='psi-box'><h4>🧬 PSI</h4><h3>KIN {psi['KIN']}</h3><small>{psi['Info'].get('主印記','')}</small></div>", unsafe_allow_html=True)
                if goddess and goddess['KIN']: st.markdown(f"<div class='goddess-box'><h4>💖 女神</h4><h3>KIN {goddess['KIN']}</h3><small>{goddess['Info'].get('主印記','')}</small></div>", unsafe_allow_html=True)
                with st.expander("✨ 進階星際密碼"):
                    st.markdown(f"**原型**：{data.get('星際原型','-')}<br>**BMU**：{data.get('BMU','-')}<br>**行星**：{data.get('行星','-')}", unsafe_allow_html=True)
                with st.expander("🧬 441 矩陣"):
                    st.markdown(f"<div class='matrix-data'>BMU: {data.get('BMU_Position','-')}<br>音符: {data.get('BMU_Note','-')}<br>時間: {data.get('Matrix_Time','-')}<br>空間: {data.get('Matrix_Space','-')}<br>共時: {data.get('Matrix_Sync','-')}</div>", unsafe_allow_html=True)
            with tc2:
                st.subheader("五大神諭盤")
                def gk(s, t): return (s + (t-1)*20 -1)%260 + 1
                st.markdown(f"""<div class="oracle-grid-container">
                    <div></div> <div>{get_card_html("引導", gk(oracle['guide']['s'],oracle['guide']['t']), oracle['guide']['s'], oracle['guide']['t'])}</div> <div></div>
                    <div>{get_card_html("擴展", gk(oracle['antipode']['s'],oracle['antipode']['t']), oracle['antipode']['s'], oracle['antipode']['t'])}</div> 
                    <div>{get_card_html("主印記", kin, oracle['destiny']['s'], oracle['destiny']['t'], True)}</div> 
                    <div>{get_card_html("支持", gk(oracle['analog']['s'],oracle['analog']['t']), oracle['analog']['s'], oracle['analog']['t'])}</div>
                    <div></div> <div>{get_card_html("推動", gk(oracle['occult']['s'],oracle['occult']['t']), oracle['occult']['s'], oracle['occult']['t'])}</div> <div></div>
                </div>""", unsafe_allow_html=True)
                st.markdown("---")
                st.subheader(f"🌊 {data.get('wave_name','')} 波符旅程")
                wavespell = get_wavespell_data(kin)
                with st.expander("📜 查看完整 13 天波符問答"):
                     for w in wavespell:
                        hl = "border: 2px solid #d4af37; background: #333;" if w['KIN'] == kin else "border: 1px solid #444;"
                        c_img, c_txt = st.columns([0.5, 4])
                        with c_img:
                             if os.path.exists(f"assets/seals/{w['Image']}"): st.image(f"assets/seals/{w['Image']}", width=40)
                        with c_txt:
                            st.markdown(f"<div style='{hl} padding: 8px; border-radius: 5px; margin-bottom: 5px;'><b style='color:#d4af37'>調性 {w['Tone']}：{w['Question']}</b><br><span style='font-size:14px;'>KIN {w['KIN']} {w['Name']}</span></div>", unsafe_allow_html=True)

        with t2:
            st.markdown("<div class='concept-text'><b>13:28 時間循環：</b>13個月x28天+無時間日，與自然韻律同步。</div>", unsafe_allow_html=True)
            lc1, lc2 = st.columns(2)
            with lc1:
                st.markdown(f"<div class='lunar-bg'><h3>🗓️ {maya['Solar_Year']}</h3><h2>{maya['Maya_Date']}</h2><p><b>月</b>：{maya['Maya_Month']}<br><b>週</b>：{maya['Maya_Week']}</p></div>", unsafe_allow_html=True)
                if wk: st.info(f"🔑 **週金句**：{wk}")
            with lc2:
                st.subheader("🛣️ 每日調頻")
                st.success(f"**等離子**：{maya['Plasma']}\n\n**路徑**：{maya['Heptad_Path']}")
                if pr: st.info(f"🙏 **祈禱文**：\n{pr}")

# 2. 52 流年
elif mode == "52流年城堡":
    st.title("🏰 52 年生命城堡")
    col_d, col_y = st.columns([1.5, 1.5])
    with col_d: d, _ = render_date_selector("castle")
    with col_y: sy = st.number_input("起始西元年", MIN_YEAR, MAX_YEAR, d.year)
    
    if st.button("計算流年", type="primary"):
        path = calculate_life_castle(datetime.date(sy, d.month, d.day))
        st.subheader(f"週期起始：{sy} 年")
        cols = st.columns(4)
        for i, r in enumerate(path[:52]):
            with cols[i%4]:
                inf = r['Info']
                img = f'<img src="data:image/png;base64,{get_img_b64(f"assets/seals/{inf.get("seal_img","")}")}" width="30">'
                st.markdown(f"<div style='background:{r['Color']}; padding:5px; border-radius:5px; margin-bottom:5px; color:#333; text-align:center; font-size:12px;'><b>{r['Age']}歲</b> ({r['Year']})<br><span style='color:#b8860b'>KIN {r['KIN']}</span><br>{img}<br>{inf.get('波符','')} | {inf.get('主印記','')}</div>", unsafe_allow_html=True)

# 3. 人員管理 (CRUD)
elif mode == "人員管理系統":
    st.title("👤 人員資料管理")
    
    tab_add, tab_list, tab_io = st.tabs(["➕ 新增人員", "📋 管理名單", "📂 匯入/匯出"])
    
    with tab_add:
        c1, c2 = st.columns(2)
        nm = c1.text_input("姓名")
        db = c2.date_input("生日", SAFE_DATE)
        if st.button("💾 存檔"):
            k, _ = calculate_kin_v2(db)
            if k:
                s = get_main_sign_text(k)
                ok, msg = save_user_data(nm, db.strftime('%Y-%m-%d'), k, s)
                if ok: st.success(msg)
                else: st.error(msg)
                
    with tab_list:
        df = get_user_list()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.subheader("✏️ 編輯 / 🗑️ 刪除")
            target = st.selectbox("選擇要操作的人員", df['姓名'])
            
            if target:
                row = df[df['姓名']==target].iloc[0]
                c_edit, c_del = st.columns(2)
                
                with c_edit:
                    with st.form("edit_form"):
                        new_name = st.text_input("新姓名", value=row['姓名'])
                        new_dob = st.date_input("新生日", value=datetime.datetime.strptime(row['生日'], "%Y-%m-%d").date())
                        if st.form_submit_button("更新資料"):
                            nk, _ = calculate_kin_v2(new_dob)
                            ns = get_main_sign_text(nk)
                            from kin_utils import update_user_data
                            ok, msg = update_user_data(target, new_name, new_dob.strftime('%Y-%m-%d'), nk, ns)
                            if ok: st.success("更新成功！請重新整理"); st.rerun()
                            else: st.error(msg)
                            
                with c_del:
                    if st.button("🗑️ 確認刪除此人", type="primary"):
                        from kin_utils import delete_user_data
                        ok, msg = delete_user_data([target])
                        if ok: st.success("已刪除！"); st.rerun()
        else:
            st.info("目前無資料")

    with tab_io:
        st.subheader("📥 匯入 CSV")
        up_file = st.file_uploader("上傳 CSV (需包含 '姓名', '出生年', '出生月', '出生日')", type="csv")
        if up_file:
            if st.button("確認匯入"):
                try:
                    df_in = pd.read_csv(up_file)
                    succ = 0
                    for _, r in df_in.iterrows():
                        try:
                            d_obj = datetime.date(int(r['出生年']), int(r['出生月']), int(r['出生日']))
                            k, _ = calculate_kin_v2(d_obj)
                            s = get_main_sign_text(k)
                            ok, _ = save_user_data(r['姓名'], d_obj.strftime('%Y-%m-%d'), k, s)
                            if ok: succ += 1
                        except: pass
                    st.success(f"成功匯入 {succ} 筆資料！")
                except Exception as e: st.error(f"匯入失敗: {e}")
        
        st.markdown("---")
        st.subheader("📤 匯出 CSV")
        if not df.empty:
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("下載通訊錄.csv", csv, "contacts.csv", "text/csv")

# 4. 合盤
elif mode == "通訊錄/合盤":
    st.title("❤️ 關係合盤")
    us = get_user_list()
    names = [""] + us['姓名'].tolist() if not us.empty else []
    ts, tm = st.tabs(["選取人員", "手動輸入"])
    
    with ts:
        if not names: st.warning("請先建檔")
        c1, c2 = st.columns(2)
        p1 = c1.selectbox("夥伴 A", names)
        p2 = c2.selectbox("夥伴 B", names)
        if p1 and p2 and st.button("計算"):
            k1, _ = get_user_kin(p1, us)
            k2, _ = get_user_kin(p2, us)
            ck = calculate_composite(k1, k2)
            ci = get_full_kin_data(ck)
            st.success(f"🎉 合盤 KIN {ck}：{ci.get('主印記','')}")
            if os.path.exists(f"assets/seals/{ci.get('seal_img','')}"): st.image(f"assets/seals/{ci.get('seal_img','')}", width=100)

    with tm:
        c3, c4 = st.columns(2)
        ka = c3.number_input("KIN A", 1, 260, 100)
        kb = c4.number_input("KIN B", 1, 260, 100)
        if st.button("手動計算"):
            ck = calculate_composite(ka, kb)
            ci = get_full_kin_data(ck)
            st.success(f"🎉 合盤 KIN {ck}：{ci.get('主印記','')}")
            st.image(f"assets/seals/{ci.get('seal_img','')}", width=100)

# 5. 系統檢查
elif mode == "系統檢查員":
    st.title("🔍 系統檢查")
    if os.path.exists("13moon.db"):
        conn = sqlite3.connect("13moon.db")
        st.success("資料庫連線正常")
        st.write("表格清單:", pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn))
        conn.close()
    else: st.error("資料庫遺失")
