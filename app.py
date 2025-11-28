import streamlit as st
import datetime
import os
import pandas as pd
import sqlite3
import base64
from create_db import init_db
from kin_utils import *

st.set_page_config(page_title="13 Moon Pro", layout="wide", page_icon="🔮")

if not os.path.exists("13moon.db"):
    with st.spinner("系統初始化中..."):
        st.cache_data.clear()
        init_db()
    st.success("完成！")

MIN_YEAR, MAX_YEAR = get_year_range()
if MIN_YEAR > 1800: MIN_YEAR = 1800
if MAX_YEAR < 2100: MAX_YEAR = 2100
SAFE_DATE = datetime.date(1990, 1, 1)

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
    "人員生日管理", "通訊錄/合盤", "八度音階查詢", "系統檢查員"
])

def get_card_html(label, kin_num, s_id, t_id, is_main=False):
    s_f = SEAL_FILES.get(s_id, f"{str(s_id).zfill(2)}.png")
    t_f = TONE_FILES.get(t_id, f"tone-{t_id}.png")
    img_s = get_img_b64(f"assets/seals/{s_f}")
    img_t = get_img_b64(f"assets/tones/{t_f}")
    
    txt = get_main_sign_text(kin_num)
    if "查無" in txt: txt = f"{TONE_NAMES[t_id]} {SEALS_NAMES[s_id]}"
    
    border = "2px solid gold" if is_main else "1px solid #555"
    return f"""<div class="kin-card-grid" style="border:{border};"><img src="data:image/png;base64,{img_t}" style="width:30px; filter:invert(1); margin:0 auto 5px auto;"><img src="data:image/jpeg;base64,{img_s}" style="width:70px; margin-bottom:5px;"><div style="font-size:12px; color:#ddd; line-height:1.2;">{txt}</div><div style="font-size:10px; color:#888;">KIN {kin_num}</div></div>"""

def user_selector(label, key):
    df = get_user_list()
    if df.empty: st.warning("通訊錄為空"); return None
    if '主印記' not in df.columns: return st.selectbox(f"選擇 {label}", df['姓名'].unique(), key=f"{key}_simple")

    fm = st.radio(f"篩選 {label}", ["全部", "依調性", "依圖騰"], horizontal=True, key=f"{key}_mode")
    fdf = df
    if fm == "依調性":
        t = st.selectbox("調性", TONE_NAMES[1:], key=f"{key}_t")
        fdf = df[df['主印記'].astype(str).str.contains(t, na=False)]
    elif fm == "依圖騰":
        s = st.selectbox("圖騰", SEALS_NAMES[1:], key=f"{key}_s")
        fdf = df[df['主印記'].astype(str).str.contains(s, na=False)]
    
    opts = fdf.apply(lambda x: f"{x['姓名']} ({x['主印記']})", axis=1).tolist()
    if not opts: st.warning("無符合"); return None
    sel = st.selectbox(f"選擇 {label}", opts, key=f"{key}_sel")
    return sel.split(" (")[0] if sel else None

def render_date_selector(key_prefix=""):
    m = st.radio("輸入方式", ["📅 自訂", "👤 通訊錄"], horizontal=True, key=f"{key_prefix}_m")
    d = SAFE_DATE; u = ""
    if m == "📅 自訂":
        d = st.date_input("生日", value=SAFE_DATE, min_value=datetime.date(MIN_YEAR,1,1), max_value=datetime.date(MAX_YEAR,12,31), key=f"{key_prefix}_d")
    else:
        sn = user_selector("人員", key_prefix)
        if sn:
            u = sn
            us = get_user_list()
            try: 
                dob = us[us['姓名']==sn].iloc[0]['生日']
                d = datetime.datetime.strptime(dob, "%Y-%m-%d").date()
                st.caption(f"已載入：{sn} ({d})")
            except: st.error("日期錯誤")
    return d, u

def show_basic_result(kin, data):
    if os.path.exists(f"assets/seals/{data.get('seal_img','' )}"):
        st.image(f"assets/seals/{data.get('seal_img','')}", width=150)
    st.markdown(f"## KIN {kin}")
    st.markdown(f"### {data.get('主印記','')}")
    st.info(f"🌊 **波符**：{data.get('wave_name','')} 波符")

# 1. 個人解碼
if mode == "個人星系解碼":
    st.title("🔮 個人星系印記解碼")
    c1, c2 = st.columns([2,1])
    with c1: date_in, _ = render_date_selector("decode")
    with c2: 
        st.write(""); st.write("")
        go = st.button("🚀 開始解碼", type="primary", use_container_width=True)
        
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
                show_basic_result(kin, data)
                if psi and psi['KIN']: st.markdown(f"<div class='psi-box'><h4>🧬 PSI</h4>KIN {psi['KIN']} {psi['Info'].get('主印記','')}<br><small>矩陣: {psi.get('Matrix','-')}</small></div>", unsafe_allow_html=True)
                if goddess and goddess['KIN']: st.markdown(f"<div class='goddess-box'><h4>💖 女神</h4>KIN {goddess['KIN']} {goddess['Info'].get('主印記','')}<br><small>源頭: KIN {goddess.get('Base_KIN')}</small></div>", unsafe_allow_html=True)
                with st.expander("✨ 進階星際密碼"):
                    st.markdown(f"**原型**：{data.get('星際原型','-')}<br>**BMU**：{data.get('BMU','-')}<br>**行星**：{data.get('行星','-')}<br>**家族**：{data.get('家族','-')}", unsafe_allow_html=True)
                with st.expander("🧬 441 矩陣"):
                    st.markdown(f"<div class='matrix-data'>BMU: {data.get('BMU_Position','-')}<br>音符: {data.get('BMU_Note','-')}<br>腦部: {data.get('BMU_Brain','-')}<hr>時間: {data.get('Matrix_Time','-')}<br>空間: {data.get('Matrix_Space','-')}<br>共時: {data.get('Matrix_Sync','-')}</div>", unsafe_allow_html=True)
            with tc2:
                st.subheader("五大神諭盤")
                # 這是正確的卓爾金曆反推公式：((調性 - 圖騰) * 40 + 圖騰)
                def gk(s, t): return ((t - s) * 40 + s - 1) % 260 + 1
                k_g = gk(oracle['guide']['s'], oracle['guide']['t'])
                k_an = gk(oracle['analog']['s'], oracle['analog']['t'])
                k_anti = gk(oracle['antipode']['s'], oracle['antipode']['t'])
                k_occ = gk(oracle['occult']['s'], oracle['occult']['t'])
                
                st.markdown(f"""<div class="oracle-grid-container">
                    <div></div> <div>{get_card_html("引導", k_g, oracle['guide']['s'], oracle['guide']['t'])}</div> <div></div>
                    <div>{get_card_html("擴展", k_anti, oracle['antipode']['s'], oracle['antipode']['t'])}</div> 
                    <div>{get_card_html("主印記", kin, oracle['destiny']['s'], oracle['destiny']['t'], True)}</div> 
                    <div>{get_card_html("支持", k_an, oracle['analog']['s'], oracle['analog']['t'])}</div>
                    <div></div> <div>{get_card_html("推動", k_occ, oracle['occult']['s'], oracle['occult']['t'])}</div> <div></div>
                </div>""", unsafe_allow_html=True)
                st.markdown("---")
                if 'IChing_Meaning' in data: st.success(f"**☯️ 易經：{data.get('對應卦象','')}**\n\n{data.get('IChing_Meaning','')}")
                if '祈禱文' in data: 
                    with st.expander("📜 查看祈禱文"): st.write(data['祈禱文'])
            st.markdown("---")
            st.subheader(f"🌊 {data.get('wave_name','')} 波符旅程")
            wz = get_wavespell_data(kin)
            with st.expander("📜 查看完整 13 天波符"):
                 for w in wz:
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
                st.markdown(f"<div class='lunar-bg'><h3>{maya['Solar_Year']}</h3><h2>{maya['Maya_Date']}</h2><p><b>月</b>：{maya['Maya_Month']}<br><b>週</b>：{maya['Maya_Week']}</p></div>", unsafe_allow_html=True)
                if wk: st.info(f"🔑 **週金句**：{wk}")
            with lc2:
                st.subheader("🛣️ 調頻")
                st.success(f"**等離子**：{maya['Plasma']}\n\n**路徑**：{maya['Heptad_Path']}")
                if pr: st.info(f"🙏 **祈禱文**：\n{pr}")

# 2. 個人流年
elif mode == "個人流年查詢":
    st.title("📅 個人流年查詢")
    d, u = render_date_selector("flow")
    ty = st.number_input("流年年份", 1900, 2100, datetime.date.today().year)
    if st.button("查詢"):
        bk, _ = calculate_kin_v2(d)
        if not bk: bk = calculate_kin_math(d)
        age = ty - d.year
        fk = (bk + age*105)%260
        if fk==0: fk=260
        st.subheader(f"{u or '此人'} {ty} 年 ( {age} 歲 )")
        fd = get_full_kin_data(fk)
        fo = get_oracle(fk)
        c1, c2 = st.columns([1, 1.6])
        with c1: show_basic_result(fk, fd)
        with c2:
            def gk(s, t): return (s + (t-1)*20 -1)%260 + 1
            k_g = gk(fo['guide']['s'], fo['guide']['t'])
            k_an = gk(fo['analog']['s'], fo['analog']['t'])
            k_anti = gk(fo['antipode']['s'], fo['antipode']['t'])
            k_occ = gk(fo['occult']['s'], fo['occult']['t'])
            
            st.markdown(f"""<div class="oracle-grid-container">
                    <div></div> <div>{get_card_html("引導", k_g, fo['guide']['s'], fo['guide']['t'])}</div> <div></div>
                    <div>{get_card_html("擴展", k_anti, fo['antipode']['s'], fo['antipode']['t'])}</div> 
                    <div>{get_card_html("流年", fk, fo['destiny']['s'], fo['destiny']['t'], True)}</div> 
                    <div>{get_card_html("支持", k_an, fo['analog']['s'], fo['analog']['t'])}</div>
                    <div></div> <div>{get_card_html("推動", k_occ, fo['occult']['s'], fo['occult']['t'])}</div> <div></div>
            </div>""", unsafe_allow_html=True)

# 3. 52流年
elif mode == "52流年城堡":
    st.title("🏰 52 年生命城堡")
    col_d, col_y = st.columns([1.5, 1.5])
    with col_d: d, _ = render_date_selector("castle")
    with col_y: sy = st.number_input("起始年", 1800, 2100, d.year)
    if st.button("計算"):
        path = calculate_life_castle(datetime.date(sy, d.month, d.day))
        st.subheader(f"週期起始：{sy} 年")
        cols = st.columns(4)
        for i, r in enumerate(path[:52]):
            with cols[i%4]:
                inf = r['Info']
                img = f'<img src="data:image/png;base64,{get_img_b64(f"assets/seals/{inf.get("seal_img","")}")}" width="30">'
                st.markdown(f"<div style='background:{r['Color']}; padding:5px; border-radius:5px; margin-bottom:5px; color:#333; text-align:center; font-size:12px;'><b>{r['Age']}歲</b><br><span style='color:#b8860b'>KIN {r['KIN']}</span><br>{img}<br>{inf.get('波符','')} | {inf.get('主印記','')}</div>", unsafe_allow_html=True)

# 4. PSI/女神/對等
elif mode == "PSI查詢":
    st.title("🧬 PSI 查詢")
    d, _ = render_date_selector("psi")
    if st.button("查詢"):
        res = get_psi_kin(d)
        if res and res['KIN']:
            st.success(f"PSI: KIN {res['KIN']}")
            show_basic_result(res['KIN'], res['Info'])
            st.info(f"矩陣: {res.get('Matrix','-')}")
        else: st.warning("無資料")

# ... (前面的程式碼)

elif mode == "女神印記查詢":
    st.title("💖 女神查詢")
    d, _ = render_date_selector("god")
    
    if st.button("查詢"):
        # 1. 計算原本的 KIN
        k, _ = calculate_kin_v2(d)
        if not k: k = calculate_kin_math(d)
        
        # 2. 計算女神 KIN
        res = get_goddess_kin(k)
        
        # 3. 顯示基本女神資訊
        st.success(f"原本 KIN {k} -> 女神力量: KIN {res['KIN']}")
        show_basic_result(res['KIN'], res['Info'])
        
        # --- ✨ 新增：顯示女神波符旅程 ---
        st.markdown("---")
        st.subheader(f"🌊 {res['Info'].get('wave_name','')} 波符旅程")
        
        # 取得波符資料
        wz = get_wavespell_data(res['KIN'])
        
        # 使用 Expander 顯示 (預設展開)
        with st.expander(f"📜 查看 KIN {res['KIN']} 的完整 13 天旅程", expanded=True):
             for w in wz:
                # 設定高亮樣式 (如果是女神 KIN 本身，顯示金色邊框)
                hl = "border: 2px solid #d4af37; background: #333;" if w['KIN'] == res['KIN'] else "border: 1px solid #444;"
                
                c_img, c_txt = st.columns([0.5, 4])
                with c_img:
                     if os.path.exists(f"assets/seals/{w['Image']}"): 
                         st.image(f"assets/seals/{w['Image']}", width=40)
                with c_txt:
                    st.markdown(
                        f"<div style='{hl} padding: 8px; border-radius: 5px; margin-bottom: 5px;'>"
                        f"<b style='color:#d4af37'>調性 {w['Tone']}：{w['Question']}</b><br>"
                        f"<span style='font-size:14px;'>KIN {w['KIN']} {w['Name']}</span>"
                        f"</div>", 
                        unsafe_allow_html=True
                    )

elif mode == "對等印記查詢":
    st.title("🔄 對等印記查詢")
    d, _ = render_date_selector("eq")
    if st.button("查詢"):
        k, _ = calculate_kin_v2(d)
        if not k: k = calculate_kin_math(d)
        from kin_utils import calculate_equivalent_kin
        res = calculate_equivalent_kin(k)
        if res:
            st.success(f"TFI: {res['TFI']} -> 對等 KIN {res['Eq_Kin']}")
            show_basic_result(res['Eq_Kin'], res['Eq_Info'])

# 5. 高階功能
elif mode == "全腦調頻":
    st.title("🧠 全腦調頻")
    data = get_whole_brain_tuning()
    if data:
        for item in data:
            with st.expander(f"{item['Part']}"): st.write(item['Text'])
    else: st.warning("無資料")

elif mode == "國王棋盤":
    st.title("👑 國王預言棋盤")
    d, _ = render_date_selector("king")
    if st.button("讀取"):
        k, _ = calculate_kin_v2(d)
        if not k: k = calculate_kin_math(d)
        maya = get_maya_calendar_info(d)
        tk = get_telektonon_info(k, maya)
        c1, c2 = st.columns(2)
        with c1: st.info(f"水晶: {tk['Crystal_Battery']}\n\n立方: {tk['Warrior_Cube']}")
        with c2: st.success(f"🐢 {tk['Turtle_Color']} | {tk['Turtle_Day']}\n\n{tk.get('Turtle_Desc','')}")

# 6. 人員管理
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
                r = df[df['姓名']==sel].iloc[0]
                nn = st.text_input("新姓名", value=sel)
                nd = st.date_input("新生日", value=datetime.datetime.strptime(r['生日'],"%Y-%m-%d").date())
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
                    dd = datetime.date(int(r['出生年']), int(r['出生月']), int(r['出生日']))
                    kk, _ = calculate_kin_v2(dd)
                    save_user_data(r['姓名'], dd.strftime('%Y-%m-%d'), kk, get_main_sign_text(kk))
                st.success("匯入完成")
            except: st.error("格式錯誤")

# 7. 合盤
elif mode == "通訊錄/合盤":
    st.title("❤️ 關係合盤")
    pn1 = user_selector("夥伴 A", "p1")
    pn2 = user_selector("夥伴 B", "p2")
    if st.button("計算"):
        if pn1 and pn2:
            us = get_user_list()
            k1, _ = get_user_kin(pn1, us)
            k2, _ = get_user_kin(pn2, us)
            if k1 and k2:
                ck = calculate_composite(k1, k2)
                ci = get_full_kin_data(ck)
                st.success(f"🎉 {pn1} & {pn2} 合盤 KIN {ck}：{ci.get('主印記','')}")
                show_basic_result(ck, ci)

# 8. 八度音階
elif mode == "八度音階查詢":
    st.title("🎵 八度音階")
    note = st.selectbox("音符", ['Do','Re','Mi','Fa','Sol','La','Si',"Do'"])
    if st.button("查詢"):
        st.dataframe(pd.DataFrame(get_octave_positions(note)))

# 9. 系統檢查
elif mode == "系統檢查員":
    st.title("🔍 系統檢查")
    if os.path.exists("13moon.db"):
        conn = sqlite3.connect("13moon.db")
        st.success("資料庫連線正常")
        st.write("表格清單:", pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn))
        conn.close()
    else: st.error("資料庫遺失")


