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

# 1. 系統初始化
st.set_page_config(page_title="13 Moon Pro", layout="wide", page_icon="🔮")

if not os.path.exists("13moon.db"):
    with st.spinner("系統初始化中 (建立資料庫)..."):
        st.cache_data.clear()
        init_db()
    st.success("初始化完成！")

# 設置用戶要求的範圍
MIN_USER_YEAR = 1800
MAX_USER_YEAR = 2100
SAFE_DEFAULT_DATE = datetime.date(1990, 1, 1)

# 全域 CSS 樣式
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fff; }
    h1, h2, h3 { color: #d4af37 !important; font-family: "Microsoft JhengHei"; }
    
    /* 五大神諭卡片通用樣式 */
    .kin-card-grid {
        display: flex; flex-direction: column; align-items: center; justify-content: flex-start; 
        background: #262730; border: 1px solid #444; border-radius: 8px;
        padding: 5px; width: 100%; height: 100%; box-shadow: 0 2px 5px rgba(0,0,0,0.5);
        text-align: center; gap: 0; 
    }
    
    /* 修正後的網格高度 (解決文字遮擋) */
    .oracle-grid-container {
        display: grid; 
        grid-template-columns: 100px 100px 100px;
        grid-template-rows: 100px 140px 100px; /* 中央行增加到 140px */
        gap: 12px; 
        justify-content: center;
        align-items: center;
    }

    .psi-box { background: linear-gradient(135deg, #2b1055, #7597de); padding: 15px; border-radius: 10px; color: white; margin-top: 20px; }
    .goddess-box { background: linear-gradient(135deg, #7c244c, #d5739c); padding: 15px; border-radius: 10px; color: white; margin-top: 15px; }
    .matrix-data {
        font-family: monospace; color: #00ff00; background: #000;
        padding: 10px; border-radius: 5px; margin-top: 10px; border: 1px solid #004400;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🌌 13 Moon System")
mode = st.sidebar.radio("功能導航", ["個人星系解碼", "52流年城堡", "人員生日管理", "通訊錄/合盤", "系統檢查員"])

# --- 輔助顯示卡片 ---
def get_card_html(label, kin_num, s_id, t_id, is_main=False):
    s_f = SEAL_FILES.get(s_id, f"{str(s_id).zfill(2)}.png")
    t_f = TONE_FILES.get(t_id, f"tone-{t_id}.png")
    
    img_s_b64 = get_img_b64(f"assets/seals/{s_f}")
    img_t_b64 = get_img_b64(f"assets/tones/{t_f}")
    
    # 關鍵修正：透過 KIN 數字查詢精準的主印記名稱
    display_text = get_main_sign_text(kin_num)
    
    if "查無印記名稱" in display_text:
        seal_name = SEALS_NAMES[s_id] if 0 < s_id < 21 else "未知"
        tone_name = TONE_NAMES[t_id] if 0 < t_id < 14 else "未知"
        display_text = f"{tone_name} {seal_name}"

    border_style = "2px solid gold" if is_main else "1px solid #555"

    return f"""
    <div class="kin-card-grid" style="border:{border_style};">
        <img src="data:image/png;base64,{img_t_b64}" style="width:30px; filter:invert(1); margin: 0 auto 5px auto;">
        <img src="data:image/jpeg;base64,{img_s_b64}" style="width:70px; margin-bottom: 5px;">
        <div style="font-size:12px; color:#ddd; line-height:1.2;">{display_text}</div>
        <div style="font-size:10px; color:#888;">KIN {kin_num}</div>
    </div>
    """

# ==========================================
# 頁面 1: 個人星系解碼 (包含雙核心分頁)
# ==========================================
if mode == "個人星系解碼":
    st.title("🔮 個人星系印記解碼")
    
    col_d, col_b = st.columns([2, 1])
    with col_d:
        st.subheader("📅 查詢日期")
        date_in = st.date_input(
            "選擇生日", 
            value=SAFE_DEFAULT_DATE,
            min_value=datetime.date(MIN_USER_YEAR, 1, 1), 
            max_value=datetime.date(MAX_USER_YEAR, 12, 31)
        )
    with col_b:
        st.write("")
        st.write("")
        st.write("") 
        start_btn = st.button("🚀 開始解碼", type="primary")

    if start_btn or st.session_state.get('run_decode'):
        st.session_state['run_decode'] = True
        
        # 1. 計算所有數據
        kin, err = calculate_kin_v2(date_in)
        if kin is None:
            st.error(f"⚠️ KIN計算失敗: {err} (切換為數學備案)")
            kin = calculate_kin_math(date_in)
            
        data = get_full_kin_data(kin)
        oracle_info = get_oracle(kin)
        psi_data = get_psi_kin(date_in)
        goddess_data = get_goddess_kin(kin)
        maya_cal_info = get_maya_calendar_info(date_in)
        week_key_sentence = get_week_key_sentence(maya_cal_info.get('瑪雅週', ''))
        heptad_prayer = get_heptad_prayer(maya_cal_info.get('Heptad_Path', ''))
        
        st.divider()
        
        # 輔助計算周邊印記的 KIN 數字 (用於顯示)
        def get_kin_from_ids(s_id, t_id):
            raw_kin = s_id + (t_id - 1) * 20
            return (raw_kin - 1) % 260 + 1

        guide_kin = get_kin_from_ids(oracle_info['guide']['s'], oracle_info['guide']['t'])
        analog_kin = get_kin_from_ids(oracle_info['analog']['s'], oracle_info['analog']['t'])
        antipode_kin = get_kin_from_ids(oracle_info['antipode']['s'], oracle_info['antipode']['t'])
        occult_kin = get_kin_from_ids(oracle_info['occult']['s'], oracle_info['occult']['t'])
        
        tab_20, tab_28 = st.tabs(["1️⃣3️⃣ : 2️⃣0️⃣ 共時編碼 (Tzolkin)", "1️⃣3️⃣ : 2️⃣8️⃣ 時間循環 (Solar-Lunar)"])
        
        # === TAB 1: 13:20 共時編碼 (KIN & Oracle) ===
        with tab_20:
            
            t_col1, t_col2 = st.columns([1, 1.6])
            
            # --- 左側：主資訊 ---
            with t_col1:
                seal_img = data.get('seal_img','')
                s_path = f"assets/seals/{seal_img}"
                if os.path.exists(s_path): st.image(s_path, width=180)
                
                st.markdown(f"## KIN {kin}")
                st.markdown(f"### {data.get('主印記','')}")
                
                st.info(f"🌊 **波符**：{data.get('波符','未知')} 波符")
                st.caption(f"🏰 **城堡**：{data.get('城堡','未知')}")
                
                # PSI & 女神區塊
                if psi_data and psi_data['KIN'] != 0:
                    p_info = psi_data['Info']
                    st.markdown(f"""
                    <div class="psi-box">
                        <h4 style="margin:0">🧬 PSI 行星記憶庫</h4>
                        <h3 style="margin:5px 0 0 0; color:#ffd700">KIN {psi_data['KIN']}</h3>
                        <div style="font-size:14px">{p_info.get('主印記','')}</div>
                    </div>
                    """, unsafe_allow_html=True)

                if goddess_data and goddess_data['KIN'] != 0:
                    g_info = goddess_data['Info']
                    st.markdown(f"""
                    <div class="goddess-box">
                        <h4 style="margin:0; color:#fbcfe8;">💖 女神力量 (Goddess Seal)</h4>
                        <h3 style="margin:5px 0 0 0; color:#ffd700">KIN {goddess_data['KIN']}</h3>
                        <div style="font-size:14px">{g_info.get('主印記','')}</div>
                        <div style="font-size:12px; margin-top:5px; color:#ddd">隱藏力量: KIN {goddess_data['Base_KIN']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with st.expander("🧬 441 矩陣數據"):
                    st.markdown(f"""<div class="matrix-data">
                    時間: {data.get('Matrix_Time','-')}<br>
                    空間: {data.get('Matrix_Space','-')}<br>
                    共時: {data.get('Matrix_Sync','-')}<br>
                    BMU : {data.get('Matrix_BMU','-')}
                    </div>""", unsafe_allow_html=True)

            # --- 右側：五大神諭盤 ---
            with t_col2:
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

                st.markdown("---")
                if 'IChing_Meaning' in data:
                    st.success(f"**☯️ 易經：{data.get('對應卦象','')}**\n\n{data.get('IChing_Meaning','')}")
                if '祈禱文' in data:
                    with st.expander("📜 祈禱文"):
                        st.write(data['祈禱文'])

        # === TAB 2: 13:28 時間循環 (Solar-Lunar) ===
        with tab_28:
            
            t_col1, t_col2 = st.columns(2)
            
            with t_col1:
                st.subheader("🗓️ 瑪雅曆法對照")
                if maya_cal_info['Status'] == "查詢成功":
                    st.markdown(f"**國曆日期**：<span style='color:#ffd700'>{date_in.strftime('%Y-%m-%d')}</span>", unsafe_allow_html=True)
                    st.markdown(f"**瑪雅日期**：<span style='color:#ffd700'>{maya_cal_info['Maya_Date']}</span>")
                    st.markdown(f"**瑪雅月 (13月相)**：{maya_cal_info['Maya_Month']}")
                    st.markdown(f"**瑪雅週 (4色循環)**：{maya_cal_info['Maya_Week']}")
                    
                    if week_key_sentence:
                        st.markdown("---")
                        st.success(f"🔑 **本週主題金句**：{week_key_sentence}")
                else:
                    st.error(f"⚠️ {maya_cal_info['Status']}，請檢查 Calendar_Converter 表格範圍。")
            
            with t_col2:
                st.subheader("🛣️ 七價路徑與調頻")
                st.markdown(f"**等離子日 (7天循環)**：<span style='color:#00ff00'>{maya_cal_info['Plasma']}</span>", unsafe_allow_html=True)
                st.markdown(f"**七價路徑**：{maya_cal_info['Heptad_Path']}")
                
                if heptad_prayer:
                    st.info(f"**🙏 祈禱文**：{heptad_prayer}")
                else:
                    st.caption("查無對應的七價路徑祈禱文。")

# ==========================================
# 頁面 2: 52 流年城堡 (遇年改年)
# ==========================================
elif mode == "52流年城堡":
    st.title("🏰 52 年生命城堡")
    
    col_d, col_start_year, col_b = st.columns([1.5, 1.5, 1])
    
    with col_d:
        d = st.date_input("出生日期", datetime.date(1990, 1, 1))
    
    with col_start_year:
         st.subheader("🔁 循環起始年")
         # 設置起始年為可選範圍
         start_year = st.number_input("計算起始西元年", min_value=1800, max_value=2100, value=d.year)
         
    with col_b:
        st.write("")
        st.write("")
        start_btn = st.button("計算流年路徑", type="primary")

    if start_btn:
        start_dob = datetime.date(start_year, d.month, d.day)
        path = calculate_life_castle(start_dob)
        
        st.subheader(f"週期起始：{start_year} 年 (0-51歲)")
        
        cols = st.columns(4)
        for i, row in enumerate(path[:52]):
            with cols[i % 4]:
                info = row['Info']
                s_p = f"assets/seals/{info.get('seal_img','')}"
                img_html = f'<img src="data:image/png;base64,{get_img_b64(s_p)}" width="40" style="border-radius:50%">' if os.path.exists(s_p) else ""
                
                # 顯示 波符名稱 | 主印記名稱
                display_name = f"{info.get('波符', '未知')} | {info.get('主印記', '')}"
                
                st.markdown(f"""
                <div style="background:{row['Color']}; padding:5px; border-radius:5px; margin-bottom:5px; color:#333; text-align:center; font-size:12px;">
                    <b>{row['Age']}歲</b> ({row['Year']})<br>
                    <span style="color:#b8860b">KIN {row['KIN']}</span><br>
                    {img_html}<br>
                    {display_name}
                </div>
                """, unsafe_allow_html=True)

# ==========================================
# 頁面 3: 人員生日管理
# ==========================================
elif mode == "人員生日管理":
    st.title("👤 人員生日管理 (建檔)")
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("姓名", max_chars=50)
    with col2:
        dob = st.date_input("生日", datetime.date(1990, 1, 1))
    
    if st.button("💾 建檔 (儲存人員資料)", type="primary"):
        if name and dob:
            kin, err = calculate_kin_v2(dob)
            if kin is None:
                st.error(f"❌ 查表失敗，無法建檔。錯誤：{err}")
                st.stop()
            
            main_sign = get_main_sign_text(kin)
            success, msg = save_user_data(name, dob.strftime('%Y-%m-%d'), kin, main_sign)
            if success:
                st.success(f"✅ {name} 的資料已成功建檔！{msg}")
            else:
                st.error(f"❌ 建檔失敗：{msg}")
        else:
            st.warning("請輸入姓名與生日！")
            
    st.markdown("---")
    st.subheader("👤 已建檔人員列表")
    df_users = get_user_list()
    st.dataframe(df_users)


# ==========================================
# 頁面 4: 通訊錄/合盤 (整合功能)
# ==========================================
elif mode == "通訊錄/合盤":
    st.title("❤️ 關係合盤計算")
    df_users = get_user_list()
    
    if df_users.empty:
        st.warning("請先在「人員生日管理」頁面建檔。")
        
    names = df_users['姓名'].tolist() if not df_users.empty else []
    
    tab_select, tab_manual = st.tabs(["👥 選取建檔人員", "✍️ 手動輸入 KIN"])

    with tab_select:
        col1, col2 = st.columns(2)
        p1_name = col1.selectbox("夥伴 A (建檔)", [""] + names, key="comp_p1")
        p2_name = col2.selectbox("夥伴 B (建檔)", [""] + names, key="comp_p2")
        
        if p1_name and p2_name and st.button("計算建檔合盤"):
            kin_a, dob_a = get_user_kin(p1_name, df_users)
            kin_b, dob_b = get_user_kin(p2_name, df_users)
            
            if kin_a is not None and kin_b is not None:
                comp_kin = calculate_composite(kin_a, kin_b)
                comp_data = get_full_kin_data(comp_kin)
                st.success(f"🎉 {p1_name} 與 {p2_name} 的關係能量是：KIN {comp_kin}")
                st.markdown(f"**印記**：{comp_data.get('主印記', '')}")
                st.markdown(f"**波符**：{comp_data.get('波符', '')}")
                st.image(f"assets/seals/{comp_data.get('seal_img','')}", width=80)
            else:
                st.error("查無人員 KIN 數據。")

    with tab_manual:
        col3, col4 = st.columns(2)
        kin_a_m = col3.number_input("輸入 KIN A (1-260)", min_value=1, max_value=260, value=100)
        kin_b_m = col4.number_input("輸入 KIN B (1-260)", min_value=1, max_value=260, value=100)
        
        if st.button("計算手動合盤"):
            comp_kin = calculate_composite(kin_a_m, kin_b_m)
            comp_data = get_full_kin_data(comp_kin)
            st.success(f"🎉 合盤結果：KIN {comp_kin}")
            st.markdown(f"**印記**：{comp_data.get('主印記', '')}")
            st.markdown(f"**波符**：{comp_data.get('波符', '')}")
            st.image(f"assets/seals/{comp_data.get('seal_img','')}", width=80)

# ==========================================
# 頁面 5: 系統檢查員 (除錯)
# ==========================================
elif mode == "系統檢查員":
    st.title("🔍 系統檢查")
    if os.path.exists("13moon.db"):
        conn = sqlite3.connect("13moon.db")
        try:
            st.success("資料庫連接成功")
            st.subheader("PSI/KIN 計算表狀態")
            for table in ['Kin_Start', 'Month_Accum', 'Kin_Basic', 'PSI_Bank']:
                try:
                    df = pd.read_sql(f"SELECT * FROM {table} LIMIT 1", conn)
                    st.write(f"✅ {table}：載入成功 (欄位: {df.columns.tolist()})")
                except: st.error(f"❌ {table} 表格缺失或欄位錯誤")
            
        except Exception as e: st.error(f"錯誤: {e}")
        conn.close()
    else:
        st.error("資料庫未建立")
