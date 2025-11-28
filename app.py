import streamlit as st
import datetime
import os
import pandas as pd
import sqlite3
import base64
from create_db import init_db
from kin_utils import *
import math

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="13 Moon Pro", layout="wide", page_icon="🔮")

# 初始化檢查
if not os.path.exists("13moon.db"):
    with st.spinner("系統初始化中..."):
        st.cache_data.clear()
        init_db()
    st.success("完成！")

MIN_YEAR, MAX_YEAR = get_year_range()
if MIN_YEAR > 1800: MIN_YEAR = 1800
if MAX_YEAR < 2100: MAX_YEAR = 2100
SAFE_DATE = datetime.date(1990, 1, 1)

# --- 2. CSS 樣式 (終極修復版) ---
st.markdown("""
<style>
    /* ==================================
       1. 全域與基礎設定
       ================================== */
    .stApp { background-color: #0e1117; color: #ffffff; font-size: 18px; }
    section[data-testid="stSidebar"] { background-color: #262730; color: #ffffff; }
    h1, h2, h3 { color: #d4af37 !important; font-family: "Microsoft JhengHei"; }

    /* ==================================
       2. 🚨 52流年 Grid 容器 (完全擺脫 st.columns) 🚨
       ================================== */
    .castle-grid-container {
        display: grid;
        /* 強制 4 等份的欄位寬度 */
        grid-template-columns: repeat(4, 1fr); 
        gap: 15px 10px; /* 增加間距 */
        padding: 10px 0;
        width: 100%;
    }
    .castle-card-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 10px 5px;
        border-radius: 10px;
        min-height: 160px;
    }
    /* 🚨 終極文字顏色修正：確保淺色背景卡片上的文字是黑色 🚨 */
    .castle-card-content * {
        color: inherit !important; /* 讓內層文字繼承父層顏色，防止被全局白色覆蓋 */
    }


    /* ==================================
       3. 其他樣式 (維持不變)
       ================================== */
    .kin-card-grid {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        background: #262730; border: 1px solid #444; border-radius: 12px;
        padding: 15px 5px; width: 100%; min-height: 180px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .oracle-grid-container {
        display: grid; grid-template-columns: 130px 130px 130px; grid-template-rows: auto auto auto; gap: 15px; justify-content: center; align-items: center; padding: 10px;
    }
    /* ... (其他卡片樣式維持不變) ... */
</style>
""", unsafe_allow_html=True)

# --- 3. 側邊欄導航 ---
st.sidebar.title("🌌 13 Moon System")
mode = st.sidebar.radio("功能導航", [
    "個人星系解碼", "個人流年查詢", "52流年城堡", 
    "PSI查詢", "女神印記查詢", "對等印記查詢", "全腦調頻", "國王棋盤",
    "人員生日管理", "通訊錄/合盤", "八度音階查詢", "系統檢查員"
])

# --- 4. 共用函式 (省略，但代碼中會使用) ---
# ... (這裡省略了 get_card_html, user_selector, render_date_selector, show_basic_result 等，但它們必須在 app.py 裡定義) ...

def get_card_html(label, kin_num, s_id, t_id, is_main=False):
    s_f = SEAL_FILES.get(s_id, f"{str(s_id).zfill(2)}.png")
    t_f = TONE_FILES.get(t_id, f"tone-{t_id}.png")
    
    img_s = get_img_b64(f"assets/seals/{s_f}")
    img_t = get_img_b64(f"assets/tones/{t_f}")
    
    html_s = f'<img src="data:image/png;base64,{img_s}" style="width:70px; margin-bottom:5px;">' if img_s else '<div style="font-size:40px;">🔮</div>'
    html_t = f'<img src="data:image/png;base64,{img_t}" style="width:30px; filter:invert(1); margin:0 auto 5px auto;">' if img_t else '<div style="font-size:20px;">🎵</div>'

    txt = get_main_sign_text(kin_num)
    if "查無" in txt: txt = f"{TONE_NAMES[t_id]} {SEALS_NAMES[s_id]}"
    
    border = "2px solid gold" if is_main else "1px solid #555"
    return f"""<div class="kin-card-grid" style="border:{border};">{html_t}{html_s}<div style="font-size:12px; color:#ddd; line-height:1.2;">{txt}</div><div style="font-size:10px; color:#888;">KIN {kin_num}</div></div>"""

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
    img_b64 = get_img_b64(f"assets/seals/{data.get('seal_img','')}")
    if img_b64:
        st.markdown(f'<img src="data:image/png;base64,{img_b64}" width="150">', unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:80px;">🔮</div>', unsafe_allow_html=True)
        
    st.markdown(f"## KIN {kin}")
    st.markdown(f"### {data.get('主印記','')}")
    st.info(f"🌊 **波符**：{data.get('wave_name','')} 波符")

# --- 5. 各功能模組 ---

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
                
                if psi and psi['KIN']: 
                    st.markdown(f"<div class='psi-box'><h4>🧬 PSI</h4>KIN {psi['KIN']} {psi['Info'].get('主印記','')}<br><small>矩陣: {psi.get('Matrix','-')}</small></div>", unsafe_allow_html=True)
                
                with st.expander("✨ 進階星際密碼 (圖騰能量)", expanded=True):
                    st.markdown(f"""
                    | 屬性 | 內容 |
                    | :--- | :--- |
                    | **星際原型** | {data.get('星際原型','-')} |
                    | **家族** | {data.get('家族','-')} |
                    | **行星** | {data.get('行星','-')} |
                    | **BMU** | {data.get('BMU','-')} |
                    | **電路** | {data.get('電路','-')} |
                    | **流** | {data.get('流','-')} |
                    **📜 說明：** {data.get('說明','-')}
                    """, unsafe_allow_html=True)
            
            with tc2:
                st.subheader("五大神諭盤")
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
                    hl = "border: 2px solid #d4af37; background: #333;" if w['KIN'] == kin else "1px solid #444;"
                    img_data = get_img_b64(f"assets/seals/{w['Image']}")
                    img_tag = f'<img src="data:image/png;base64,{img_data}" width="40">' if img_data else '🔮'
                    c_img, c_txt = st.columns([0.5, 4])
                    with c_img: st.markdown(img_tag, unsafe_allow_html=True)
                    with c_txt:
                        st.markdown(f"<div style='{hl} padding: 8px; border-radius: 5px; margin-bottom: 5px;'><b style='color:#d4af37'>調性 {w['Tone']}：{w['Question']}</b><br><span style='font-size:14px;'>KIN {w['KIN']} {w['Name']}</span></div>", unsafe_allow_html=True)

        with t2:
            st.markdown("<div class='concept-text'><b>13:28 時間循環：</b>13個月x28天+無時間日，與自然韻律同步。</div>", unsafe_allow_html=True)
            lc1, lc2 = st.columns(2)
            with lc1:
                st.markdown(f"""
                <div class='lunar-bg'>
                    <h3>{maya['Solar_Year']}</h3>
                    <h2>{maya['Maya_Date']}</h2>
                    <p><b>月</b>：{maya['Maya_Month']}<br>
                    <b>週</b>：{maya['Maya_Week']}</p>
                    <hr style='margin: 10px 0; border-color: rgba(255,255,255,0.2);'>
                    <p style='font-size: 14px; color: #ffd700;'><b>🌟 Vinal 肯定句：</b><br>{maya['Vinal']}</p>
                </div>
                """, unsafe_allow_html=True)
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
        
        st.success(f"{u or '此人'} {ty} 年 ( {age} 歲 ) -> 流年 KIN {fk}")
        fd = get_full_kin_data(fk)
        
        c1, c2 = st.columns([1, 1.6])
        with c1: show_basic_result(fk, fd)
        with c2:
            st.subheader("流年五大神諭")
            fo = get_oracle(fk)
            def gk(s, t): return ((t - s) * 40 + s - 1) % 260 + 1
            
            k_destiny = fk
            k_guide = gk(fo['guide']['s'], fo['guide']['t'])
            k_analog = gk(fo['analog']['s'], fo['analog']['t'])
            k_antipode = gk(fo['antipode']['s'], fo['antipode']['t'])
            k_occult = gk(fo['occult']['s'], fo['occult']['t'])
            
            st.markdown(f"""<div class="oracle-grid-container">
                    <div></div> <div>{get_card_html("引導", k_guide, fo['guide']['s'], fo['guide']['t'])}</div> <div></div>
                    <div>{get_card_html("擴展", k_anti, fo['antipode']['s'], fo['antipode']['t'])}</div> 
                    <div>{get_card_html("流年", k_destiny, fo['destiny']['s'], fo['destiny']['t'], True)}</div> 
                    <div>{get_card_html("支持", k_analog, fo['analog']['s'], fo['analog']['t'])}</div>
                    <div></div> <div>{get_card_html("推動", k_occ, fo['occult']['s'], fo['occult']['t'])}</div> <div></div>
            </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader(f"🌊 {fd.get('wave_name','')} 波符旅程")
        wz = get_wavespell_data(fk)
        with st.expander(f"📜 查看 KIN {fk} 的完整 13 天旅程", expanded=True):
             for w in wz:
                hl = "border: 2px solid #d4af37; background: #333;" if w['KIN'] == fk else "1px solid #444;"
                img_data = get_img_b64(f"assets/seals/{w['Image']}")
                img_tag = f'<img src="data:image/png;base64,{img_data}" width="40">' if img_data else '🔮'
                c_img, c_txt = st.columns([0.5, 4])
                with c_img: st.markdown(img_tag, unsafe_allow_html=True)
                with c_txt: st.markdown(f"<div style='{hl} padding: 8px; border-radius: 5px; margin-bottom: 5px;'><b style='color:#d4af37'>調性 {w['Tone']}：{w['Question']}</b><br><span style='font-size:14px;'>KIN {w['KIN']} {w['Name']}</span></div>", unsafe_allow_html=True)

# 3. 52流年 (四色城堡 + 家族輪替 + Radio修復版)
elif mode == "52流年城堡":
    st.title("🏰 52 年生命城堡")
    
    col_d, col_y = st.columns([1.5, 1.5])
    with col_d: d, u = render_date_selector("castle")
    with col_y: sy = st.number_input("起始年份 (通常為出生年)", 1900, 2100, d.year)
    
    if st.button("計算生命城堡"):
        start_date = datetime.date(sy, d.month, d.day)
        bk, _ = calculate_kin_v2(start_date)
        if not bk: bk = calculate_kin_math(start_date)
        
        birth_info = get_full_kin_data(bk)
        family_name = birth_info.get('家族', '未知')
        
        family_map = {
            "極性家族": "family_polar.jpg", "基本家族": "family_cardinal.jpg", 
            "主要家族": "family_cardinal.jpg", "核心家族": "family_core.jpg",
            "信號家族": "family_signal.jpg", "通道家族": "family_gateway.jpg"
        }
        img_name = family_map.get(family_name)
        
        st.subheader(f"週期起始：{sy} 年")
        if img_name and os.path.exists(f"assets/{img_name}"):
            with st.expander(f"🖼️ 查看您的家族圖騰表：{family_name}", expanded=False):
                st.image(f"assets/{img_name}", caption=f"{u or '此人'} 屬於 {family_name}", use_container_width=True)
        else:
            st.info(f"您的星際家族為：**{family_name}**")

        path = calculate_life_castle(start_date)
        current_year = datetime.date.today().year
        current_age = current_year - sy
        
        # 3. 定義渲染單一城堡 (13年) - 最終顏色與結構修復版
        def render_13_year_castle(data_subset):
            # 這是新的 Grid Layout，取代 st.columns()
            html_content = '<div class="castle-grid-container">'
            
            for i in range(len(data_subset)):
                r = data_subset[i]
                inf = r['Info']
                is_current = (r['Year'] == current_year)
                
                # 樣式與顏色邏輯
                if is_current:
                    border = "2px solid #d4af37"
                    bg = "#333333" 
                    txt_col = "#ffffff"
                    box_shadow = "0 0 15px #d4af37"
                else:
                    border = "1px solid #999"
                    bg = r['Color']
                    txt_col = "#000000" # <-- 強制黑色
                    box_shadow = "0 2px 5px rgba(0,0,0,0.1)"
                
                # 圖片處理
                img_filename = inf.get("seal_img", "")
                b64_data = get_img_b64(f"assets/seals/{img_filename}")
                img_html = f'<img src="data:image/png;base64,{b64_data}" width="45" style="margin: 8px 0;">' if b64_data else '<div style="font-size:30px; margin: 8px 0;">🔮</div>'

                # 🚨 關鍵：使用 <span> 標籤鎖定顏色 (解決白字隱形)
                card_html = f"""
                <div class="castle-card-content" style='background:{bg}; border:{border}; box-shadow:{box_shadow};'>
                    <span style='font-size:14px; font-weight:bold; color:{txt_col}; display:block; margin-bottom:2px;'>
                        {r['Age']}歲
                    </span>
                    <span style='font-size:12px; color:{txt_col}; opacity:0.9; display:block; margin-bottom:5px;'>
                        {r['Year']}
                    </span>
                    {img_html}
                    <span style='font-size:13px; font-weight:bold; color:{txt_col}; display:block; margin-top:2px;'>
                        KIN {r['KIN']}
                    </span>
                    <span style='font-size:12px; color:{txt_col}; display:block;'>
                        {inf.get('調性').replace('性','')} {inf.get('圖騰')}
                    </span>
                </div>
                """
                html_content += card_html

            html_content += '</div>'
            st.markdown(html_content, unsafe_allow_html=True)


        target_data = path[:52]
        base_age_offset = 0
        
        if current_age > 51:
            st.info(f"🎂 您目前 {current_age} 歲，已進入生命的第二個 52 年螺旋。")
            cycle_choice = st.radio("請選擇要查看的生命週期：", ["🧬 第二生命荷包 (52-103歲)", "🔄 回顧：第一生命荷包 (0-51歲)"], horizontal=True)
            if "第二" in cycle_choice:
                target_data = path[52:104]
                base_age_offset = 52
            else:
                target_data = path[:52]
                base_age_offset = 0
        
        st.markdown("---")
        with st.container(): # 使用 container 包裹 tabs
            c_tabs = st.tabs(["🔴 紅色東方城堡", "⚪ 白色北方城堡", "🔵 藍色西方城堡", "🟡 黃色南方城堡"])
            
            with c_tabs[0]:
                st.caption(f"🚀 **啟動之庭** | 歲數：{base_age_offset}~{base_age_offset+12} 歲")
                render_13_year_castle(target_data[0:13])
            with c_tabs[1]:
                st.caption(f"⚔️ **淨化之庭** | 歲數：{base_age_offset+13}~{base_age_offset+25} 歲")
                render_13_year_castle(target_data[13:26])
            with c_tabs[2]:
                st.caption(f"🦋 **蛻變之庭** | 歲數：{base_age_offset+26}~{base_age_offset+38} 歲")
                render_13_year_castle(target_data[26:39])
            with c_tabs[3]:
                st.caption(f"☀️ **收成之庭** | 歲數：{base_age_offset+39}~{base_age_offset+51} 歲")
                render_13_year_castle(target_data[39:52])

# 4. PSI (含神諭波符)
elif mode == "PSI查詢":
    st.title("🧬 PSI 查詢")
    d, _ = render_date_selector("psi")
    if st.button("查詢"):
        res = get_psi_kin(d)
        if res and res['KIN']:
            pk = res['KIN']
            p_info = res['Info']
            maya_date = res.get('Maya_Date', '-')
            matrix_loc = res.get('Matrix', '-')
            st.success(f"PSI: KIN {pk} ( 13:28 座標: {maya_date} | 矩陣: {matrix_loc} )")
            
            c1, c2 = st.columns([1, 1.6])
            with c1: show_basic_result(pk, p_info)
            with c2:
                st.subheader("PSI 五大神諭")
                po = get_oracle(pk)
                def gk(s, t): return ((t - s) * 40 + s - 1) % 260 + 1
                
                k_destiny = pk
                k_guide = gk(po['guide']['s'], po['guide']['t'])
                k_analog = gk(po['analog']['s'], po['analog']['t'])
                k_antipode = gk(po['antipode']['s'], po['antipode']['t'])
                k_occult = gk(po['occult']['s'], po['occult']['t'])
                
                st.markdown(f"""<div class="oracle-grid-container">
                        <div></div> <div>{get_card_html("引導", k_guide, po['guide']['s'], po['guide']['t'])}</div> <div></div>
                        <div>{get_card_html("擴展", k_antipode, po['antipode']['s'], po['antipode']['t'])}</div> 
                        <div>{get_card_html("PSI", k_destiny, po['destiny']['s'], po['destiny']['t'], True)}</div> 
                        <div>{get_card_html("支持", k_analog, po['analog']['s'], po['analog']['t'])}</div>
                        <div></div> <div>{get_card_html("推動", k_occult, po['occult']['s'], po['occult']['t'])}</div> <div></div>
                </div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.subheader(f"🌊 {p_info.get('wave_name','')} 波符旅程")
            wz = get_wavespell_data(pk)
            with st.expander(f"📜 查看 KIN {pk} 的完整 13 天旅程", expanded=True):
                 for w in wz:
                    hl = "border: 2px solid #d4af37; background: #333;" if w['KIN'] == pk else "1px solid #444;"
                    img_data = get_img_b64(f"assets/seals/{w['Image']}")
                    img_tag = f'<img src="data:image/png;base64,{img_data}" width="40">' if img_data else '🔮'
                    c_img, c_txt = st.columns([0.5, 4])
                    with c_img: st.markdown(img_tag, unsafe_allow_html=True)
                    with c_txt: st.markdown(f"<div style='{hl} padding: 8px; border-radius: 5px; margin-bottom: 5px;'><b style='color:#d4af37'>調性 {w['Tone']}：{w['Question']}</b><br><span style='font-size:14px;'>KIN {w['KIN']} {w['Name']}</span></div>", unsafe_allow_html=True)
        else:
            st.warning("查無 PSI 資料，請確認日期是否正確或資料庫已更新。")

# 5. 女神查詢 (含神諭波符)
elif mode == "女神印記查詢":
    st.title("💖 女神查詢")
    d, _ = render_date_selector("god")
    
    if st.button("查詢"):
        k, _ = calculate_kin_v2(d)
        if not k: k = calculate_kin_math(d)
        res = get_goddess_kin(k)
        
        st.success(f"原本 KIN {k} -> 女神力量: KIN {res['KIN']}")
        c1, c2 = st.columns([1, 1.6])
        with c1: show_basic_result(res['KIN'], res['Info'])
        with c2:
            st.subheader("女神五大神諭")
            g_oracle = get_oracle(res['KIN'])
            def gk(s, t): return ((t - s) * 40 + s - 1) % 260 + 1
            k_destiny = res['KIN']
            k_guide = gk(g_oracle['guide']['s'], g_oracle['guide']['t'])
            k_analog = gk(g_oracle['analog']['s'], g_oracle['analog']['t'])
            k_antipode = gk(g_oracle['antipode']['s'], g_oracle['antipode']['t'])
            k_occult = gk(g_oracle['occult']['s'], g_oracle['occult']['t'])
            
            st.markdown(f"""<div class="oracle-grid-container">
                    <div></div> <div>{get_card_html("引導", k_guide, g_oracle['guide']['s'], g_oracle['guide']['t'])}</div> <div></div>
                    <div>{get_card_html("擴展", k_antipode, g_oracle['antipode']['s'], g_oracle['antipode']['t'])}</div> 
                    <div>{get_card_html("女神", k_destiny, g_oracle['destiny']['s'], g_oracle['destiny']['t'], True)}</div> 
                    <div>{get_card_html("支持", k_analog, g_oracle['analog']['s'], g_oracle['analog']['t'])}</div>
                    <div></div> <div>{get_card_html("推動", k_occult, g_oracle['occult']['s'], g_oracle['occult']['t'])}</div> <div></div>
            </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader(f"🌊 {res['Info'].get('wave_name','')} 波符旅程")
        wz = get_wavespell_data(res['KIN'])
        with st.expander(f"📜 查看 KIN {res['KIN']} 的完整 13 天旅程", expanded=True):
             for w in wz:
                hl = "border: 2px solid #d4af37; background: #333;" if w['KIN'] == res['KIN'] else "1px solid #444;"
                img_data = get_img_b64(f"assets/seals/{w['Image']}")
                img_tag = f'<img src="data:image/png;base64,{img_data}" width="40">' if img_data else '🔮'
                c_img, c_txt = st.columns([0.5, 4])
                with c_img: st.markdown(img_tag, unsafe_allow_html=True)
                with c_txt: st.markdown(f"<div style='{hl} padding: 8px; border-radius: 5px; margin-bottom: 5px;'><b style='color:#d4af37'>調性 {w['Tone']}：{w['Question']}</b><br><span style='font-size:14px;'>KIN {w['KIN']} {w['Name']}</span></div>", unsafe_allow_html=True)

# 6. 對等印記 (矩陣高階版 - 無地圖)
elif mode == "對等印記查詢":
    st.title("🔄 對等印記查詢 (矩陣高階版)")
    d, _ = render_date_selector("eq")
    
    if st.button("查詢"):
        k, _ = calculate_kin_v2(d)
        if not k: k = calculate_kin_math(d)
        maya_info = get_maya_calendar_info(d)
        maya_date = maya_info.get('Maya_Date', '1.1')
        
        from kin_utils import calculate_equivalent_kin_new
        res = calculate_equivalent_kin_new(k, maya_date)
        
        if "Error" in res:
            st.error(f"計算錯誤: {res['Error']}")
        else:
            eq_k = res['Eq_Kin']
            eq_info = res['Eq_Info']
            st.success(f"🎉 原始 KIN {k} (瑪雅生日 {maya_date}) ➜ 對等 KIN {eq_k}")
            
            with st.expander("🧮 查看詳細計算過程", expanded=True):
                for log in res['Logs']: st.write(log)
                st.markdown("---")
                st.markdown(f"**總和**：{res['Sums'][0]} + {res['Sums'][1]} + {res['Sums'][2]} = **{res['Total']}**")
                st.markdown(f"**對等印記**：{res['Total']} % 260 = **KIN {eq_k}**")

            c1, c2 = st.columns([1, 1.6])
            with c1: show_basic_result(eq_k, eq_info)
            with c2:
                st.subheader("對等印記五大神諭")
                eo = get_oracle(eq_k)
                def gk(s, t): return ((t - s) * 40 + s - 1) % 260 + 1
                k_destiny = eq_k
                k_guide = gk(eo['guide']['s'], eo['guide']['t'])
                k_analog = gk(eo['analog']['s'], eo['analog']['t'])
                k_antipode = gk(eo['antipode']['s'], eo['antipode']['t'])
                k_occult = gk(eo['occult']['s'], eo['occult']['t'])
                
                st.markdown(f"""<div class="oracle-grid-container">
                        <div></div> <div>{get_card_html("引導", k_guide, eo['guide']['s'], eo['guide']['t'])}</div> <div></div>
                        <div>{get_card_html("擴展", k_antipode, eo['antipode']['s'], eo['antipode']['t'])}</div> 
                        <div>{get_card_html("對等", k_destiny, eo['destiny']['s'], eo['destiny']['t'], True)}</div> 
                        <div>{get_card_html("支持", k_analog, eo['analog']['s'], eo['analog']['t'])}</div>
                        <div></div> <div>{get_card_html("推動", k_occult, eo['occult']['s'], eo['occult']['t'])}</div> <div></div>
                </div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.subheader(f"🌊 {eq_info.get('wave_name','')} 波符旅程")
            wz = get_wavespell_data(eq_k)
            with st.expander(f"📜 查看 KIN {eq_k} 的完整 13 天旅程", expanded=True):
                 for w in wz:
                    hl = "border: 2px solid #d4af37; background: #333;" if w['KIN'] == eq_k else "1px solid #444;"
                    img_data = get_img_b64(f"assets/seals/{w['Image']}")
                    img_tag = f'<img src="data:image/png;base64,{img_data}" width="40">' if img_data else '🔮'
                    c_img, c_txt = st.columns([0.5, 4])
                    with c_img: st.markdown(img_tag, unsafe_allow_html=True)
                    with c_txt: st.markdown(f"<div style='{hl} padding: 8px; border-radius: 5px; margin-bottom: 5px;'><b style='color:#d4af37'>調性 {w['Tone']}：{w['Question']}</b><br><span style='font-size:14px;'>KIN {w['KIN']} {w['Name']}</span></div>", unsafe_allow_html=True)

# 7. 全腦調頻
elif mode == "全腦調頻":
    st.title("🧠 全腦調頻")
    data = get_whole_brain_tuning()
    if data:
        for item in data:
            with st.expander(f"{item['Part']}"): st.write(item['Text'])
    else: st.warning("無資料")

# 8. 國王棋盤
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

# 9. 人員管理
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
                try:
                    def_date = datetime.datetime.strptime(r['生日'], "%Y-%m-%d").date()
                except:
                    def_date = SAFE_DATE
                nd = st.date_input("新生日", value=def_date)
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
                try:
                    d_in = pd.read_csv(up)
                except UnicodeDecodeError:
                    up.seek(0)
                    d_in = pd.read_csv(up, encoding='cp950')
                
                success_count = 0
                for _, r in d_in.iterrows():
                    dd = None
                    name = r.get('姓名', r.get('名字', '未命名'))
                    if '生日' in d_in.columns:
                        try:
                            d_str = str(r['生日']).strip().replace('/', '-').split(' ')[0]
                            parts = d_str.split('-')
                            if len(parts) == 3: dd = datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                        except: pass
                    elif '出生年' in d_in.columns:
                        try: dd = datetime.date(int(r['出生年']), int(r['出生月']), int(r['出生日']))
                        except: pass

                    if dd:
                        kk, _ = calculate_kin_v2(dd)
                        if not kk: kk = calculate_kin_math(dd)
                        save_user_data(name, dd.strftime('%Y-%m-%d'), kk, get_main_sign_text(kk))
                        success_count += 1
                
                if success_count > 0:
                    st.success(f"🎉 成功匯入 {success_count} 筆資料！")
                    st.rerun()
                else: st.warning("⚠️ 匯入失敗")
            except Exception as e: st.error(f"❌ 錯誤: {str(e)}")

# 10. 合盤 (多選 + 關係文案優化)
elif mode == "通訊錄/合盤":
    st.title("❤️ 關係/團隊合盤")
    df = get_user_list()
    
    if df.empty:
        st.warning("📭 通訊錄目前是空的，請先至「人員生日管理」新增資料。")
    else:
        options = df.apply(lambda x: f"{x['姓名']} (KIN {x['KIN']})", axis=1).tolist()
        selected = st.multiselect("請選擇成員 (可選擇 2 人或多人)", options)
        
        if st.button("計算合盤能量"):
            if len(selected) < 2:
                st.warning("⚠️ 請至少選擇 2 位成員才能計算合盤喔！")
            else:
                total_kin_sum = 0
                members_names = []
                for item in selected:
                    name = item.split(" (")[0]
                    k, _ = get_user_kin(name, df)
                    if k:
                        total_kin_sum += k
                        members_names.append(name)
                
                ck = total_kin_sum % 260
                if ck == 0: ck = 260
                ci = get_full_kin_data(ck)
                
                st.success(f"🎉 成員：{' + '.join(members_names)}\n\n✨ 共同合盤 KIN {ck}")
                c1, c2 = st.columns([1, 1.6])
                with c1:
                    show_basic_result(ck, ci)
                    st.info("💡 這個印記代表你們能量疊加後，共同顯化出的關係/團隊本質。")
                
                with c2:
                    st.subheader("關係五大神諭")
                    co = get_oracle(ck)
                    def gk(s, t): return ((t - s) * 40 + s - 1) % 260 + 1
                    k_destiny = ck
                    k_guide = gk(co['guide']['s'], co['guide']['t'])
                    k_analog = gk(co['analog']['s'], co['analog']['t'])
                    k_antipode = gk(co['antipode']['s'], co['antipode']['t'])
                    k_occult = gk(co['occult']['s'], co['occult']['t'])
                    
                    st.markdown(f"""<div class="oracle-grid-container">
                            <div></div> <div>{get_card_html("關係引導", k_guide, co['guide']['s'], co['guide']['t'])}</div> <div></div>
                            <div>{get_card_html("關係挑戰", k_antipode, co['antipode']['s'], co['antipode']['t'])}</div> 
                            <div>{get_card_html("關係合盤", k_destiny, co['destiny']['s'], co['destiny']['t'], True)}</div> 
                            <div>{get_card_html("關係支持", k_analog, co['analog']['s'], co['analog']['t'])}</div>
                            <div></div> <div>{get_card_html("關係推動", k_occult, co['occult']['s'], co['occult']['t'])}</div> <div></div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("---")
                st.subheader(f"🌊 關係波符旅程：{ci.get('wave_name','')} 波符")
                wz = get_wavespell_data(ck)
                with st.expander(f"📜 查看這段關係的完整 13 天旅程", expanded=True):
                     for w in wz:
                        hl = "border: 2px solid #d4af37; background: #333;" if w['KIN'] == ck else "1px solid #444;"
                        relation_question = w['Question'].replace("你", "你們").replace("我", "我們")
                        img_data = get_img_b64(f"assets/seals/{w['Image']}")
                        img_tag = f'<img src="data:image/png;base64,{img_data}" width="40">' if img_data else '🔮'
                        c_img, c_txt = st.columns([0.5, 4])
                        with c_img: st.markdown(img_tag, unsafe_allow_html=True)
                        with c_txt: st.markdown(f"<div style='{hl} padding: 8px; border-radius: 5px; margin-bottom: 5px;'><b style='color:#d4af37'>調性 {w['Tone']}：{relation_question}</b><br><span style='font-size:14px;'>KIN {w['KIN']} {w['Name']}</span></div>", unsafe_allow_html=True)

# 11. 八度音階
elif mode == "八度音階查詢":
    st.title("🎵 八度音階")
    note = st.selectbox("音符", ['Do','Re','Mi','Fa','Sol','La','Si',"Do'"])
    if st.button("查詢"):
        st.dataframe(pd.DataFrame(get_octave_positions(note)))

# 12. 系統檢查
elif mode == "系統檢查員":
    st.title("🔍 系統檢查")
    st.info("如果您上傳了新的 CSV 檔案，但查詢不到資料，請點擊下方按鈕重建資料庫。")
    
    if st.button("🔄 強制重建資料庫 (讀取新 CSV)", type="primary"):
        with st.spinner("正在重新讀取所有 CSV 檔案..."):
            init_db()
        st.success("✅ 資料庫重建完成！請重新載入網頁。")
        st.rerun()

    st.divider()
    if os.path.exists("13moon.db"):
        conn = sqlite3.connect("13moon.db")
        st.success("資料庫連線正常 (13moon.db)")
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
        st.write("📊 目前資料庫中的表格：")
        table_stats = []
        for t in tables['name']:
            count = pd.read_sql(f"SELECT COUNT(*) FROM {t}", conn).iloc[0,0]
            table_stats.append({"表格名稱": t, "資料筆數": count})
        st.table(pd.DataFrame(table_stats))
        conn.close()
    else:
        st.error("❌ 資料庫遺失")
