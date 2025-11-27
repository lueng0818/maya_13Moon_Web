import streamlit as st
import pandas as pd
import datetime
import os
from create_db import init_db
# 自動檢查：如果資料庫不存在，就自動建立
if not os.path.exists("13moon.db"):
    init_db()
import sqlite3
from kin_utils import (
    get_kin_info, calculate_kin_from_date, get_oracle_system, 
    calculate_life_path, get_composite_kin, get_img_as_base64,
    SEAL_FILES, TONE_FILES
)

# ---------------------------------------------------------
# 1. 頁面設定與 CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="13 Moon Galactic Compass",
    page_icon="🌟",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    h1, h2, h3 { color: #d4af37 !important; font-family: "Microsoft JhengHei"; }
    
    /* 卡片樣式 */
    .kin-card {
        background-color: #262730;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        border: 1px solid #444;
        margin-bottom: 10px;
    }
    .kin-card img { border-radius: 5px; }
    .big-kin { font-size: 24px; font-weight: bold; color: #d4af37; margin: 10px 0; }
    
    /* 52流年卡片 */
    .castle-card {
        transition: transform 0.2s;
        border-radius: 8px;
        padding: 8px;
        text-align: center;
        color: #333; 
        height: 100%;
    }
    .castle-card:hover { transform: scale(1.05); }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 輔助函數：顯示單張 KIN 卡片
# ---------------------------------------------------------
def render_kin_card(role, seal_num, tone_num, is_main=False):
    """在 Streamlit 畫出一張印記卡片"""
    seal_file = SEAL_FILES.get(seal_num, "01紅龍.jpg")
    tone_file = TONE_FILES.get(tone_num, "瑪雅曆法圖騰-34.png")
    
    path_seal = os.path.join("assets/seals", seal_file)
    path_tone = os.path.join("assets/tones", tone_file)
    
    with st.container():
        st.markdown(f"<div class='kin-card' style='border-color: {'#d4af37' if is_main else '#444'}'>", unsafe_allow_html=True)
        # 顯示圖片
        if os.path.exists(path_tone): st.image(path_tone, width=40 if not is_main else 60)
        if os.path.exists(path_seal): st.image(path_seal, width=80 if not is_main else 110)
        st.caption(role)
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. 側邊欄與導航
# ---------------------------------------------------------
st.sidebar.title("🌌 13月亮曆導航")
app_mode = st.sidebar.radio("功能選單", ["星系印記解碼", "52流年城堡", "關係合盤計算"])

# ---------------------------------------------------------
# 4. [頁面] 星系印記解碼 (主頁)
# ---------------------------------------------------------
if app_mode == "星系印記解碼":
    st.title("Galactic Compass 星系羅盤")
    st.write("輸入日期，解碼當日的宇宙能量、五大神諭與波符旅程。")

    col1, col2 = st.columns([1, 2])
    with col1:
        input_date = st.date_input("選擇出生日期或流日", datetime.date.today())
        if st.button("🚀 開始解碼", type="primary"):
            st.session_state['current_kin'] = calculate_kin_from_date(input_date)

    if 'current_kin' in st.session_state:
        kin = st.session_state['current_kin']
        info = get_kin_info(kin)
        oracle = get_oracle_system(kin)

        st.divider()
        st.markdown(f"<div class='big-kin'>KIN {kin} {info['調性']}{info['圖騰']}</div>", unsafe_allow_html=True)
        
        # --- 版面：左邊神諭，右邊波符 ---
        c_left, c_right = st.columns([1.5, 1])
        
        with c_left:
            st.subheader("五大神諭 (Oracle)")
            # 上
            r1c1, r1c2, r1c3 = st.columns([1,1,1])
            with r1c2: render_kin_card("引導", oracle['guide']['seal'], oracle['guide']['tone'])
            
            # 中
            r2c1, r2c2, r2c3 = st.columns([1,1,1])
            with r2c1: render_kin_card("擴展", oracle['antipode']['seal'], oracle['antipode']['tone'])
            with r2c2: render_kin_card("主印記", oracle['destiny']['seal'], oracle['destiny']['tone'], is_main=True)
            with r2c3: render_kin_card("支持", oracle['analog']['seal'], oracle['analog']['tone'])
            
            # 下
            r3c1, r3c2, r3c3 = st.columns([1,1,1])
            with r3c2: render_kin_card("推動", oracle['occult']['seal'], oracle['occult']['tone'])

            # 祈禱文
            if '祈禱文' in info:
                st.info(f"📜 **祈禱文**：\n{info['祈禱文']}")

        with c_right:
            st.subheader("波符旅程")
            st.write(f"屬於 **{info['wave_name']}** 波符")
            wave_path = os.path.join("assets/wavespells", info['wave_img'])
            if os.path.exists(wave_path):
                st.image(wave_path, use_column_width=True)
            else:
                st.warning("波符圖片未找到")

# ---------------------------------------------------------
# 5. [頁面] 52流年城堡
# ---------------------------------------------------------
elif app_mode == "52流年城堡":
    st.title("🏰 生命城堡流年 (Life Castle)")
    
    col_input, col_info = st.columns([1, 2])
    with col_input:
        birth_date = st.date_input("請輸入出生日期", datetime.date(1990, 1, 1))
        
    if birth_date:
        # 計算實歲
        today = datetime.date.today()
        current_age = today.year - birth_date.year
        
        # 計算流年路徑 (算到 104 歲)
        path_data = calculate_life_path(birth_date, view_age_limit=105)
        
        # 顯示當前資訊
        if current_age < len(path_data):
            curr = path_data[current_age]
            with col_info:
                st.success(f"""
                ### 🎂 目前 {current_age} 歲
                - 處於第 **{curr['Cycle_Round']}** 生命週期
                - 對應 52 年循環中的 **{curr['Cycle_Age']} 歲** 位置
                - 今年的流年印記： **KIN {curr['KIN']} {curr['Label']}**
                """)
        
        st.divider()

        # 視覺化顯示 4 個城堡
        stages = [
            ("🔴 燃燒之城 (建立自我)", 0, 13),
            ("⚪ 淨化之城 (磨練洗禮)", 13, 26),
            ("🔵 蛻變之城 (轉化改變)", 26, 39),
            ("🟡 收穫之城 (成熟給予)", 39, 52)
        ]
        
        base_cycle = path_data[:52]
        user_cycle_idx = current_age % 52

        for title, start, end in stages:
            with st.expander(title, expanded=True):
                cols = st.columns(4) # 4欄排版
                subset = base_cycle[start:end]
                
                for i, data in enumerate(subset):
                    col = cols[i % 4]
                    is_current = (data['Age'] == user_cycle_idx)
                    
                    # 樣式邏輯
                    border = "3px solid #FF4B4B" if is_current else f"1px solid {data['Border_Color']}"
                    shadow = "0 0 10px rgba(255,0,0,0.5)" if is_current else "none"
                    bg_col = "#ffecec" if is_current else data['BG_Color']
                    
                    # 準備圖片 Base64
                    img_path = os.path.join("assets/seals", data['Seal_Img'])
                    img_b64 = get_img_as_base64(img_path)
                    
                    # 顯示歲數 (包含多週期)
                    age_text = f"{data['Age']} / {data['Age']+52}"
                    
                    with col:
                        st.markdown(f"""
                        <div class="castle-card" style="background-color: {bg_col}; border: {border}; box-shadow: {shadow};">
                            <div style="font-size:12px; color:#888;">{age_text} 歲</div>
                            <div style="font-weight:bold; font-size:18px; color:#b8860b;">KIN {data['KIN']}</div>
                            <img src="data:image/jpeg;base64,{img_b64}" style="width:40px; border-radius:50%; margin:5px;">
                            <div style="font-size:14px; font-weight:bold;">{data['Label']}</div>
                            <div style="font-size:11px; color:#666;">{data['Wave']}波</div>
                        </div>
                        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. [頁面] 關係合盤計算
# ---------------------------------------------------------
elif app_mode == "關係合盤計算":
    st.title("🤝 關係合盤能量 (Composite)")
    
    conn = sqlite3.connect("13moon.db")
    try:
        df_users = pd.read_sql("SELECT * FROM Users", conn)
    except:
        df_users = pd.DataFrame()
    conn.close()

    col1, col2, col3 = st.columns([1, 0.2, 1])

    # 準備選單
    user_options = ["手動輸入"]
    if not df_users.empty:
        # 格式: 名字 (KIN 123)
        user_list = df_users.apply(lambda x: f"{x['名字']} (KIN {int(x['KIN'])})", axis=1).tolist()
        user_options.extend(user_list)

    # --- 選擇 A ---
    with col1:
        st.subheader("👤 夥伴 A")
        sel_a = st.selectbox("選擇成員", user_options, key="pa")
        if sel_a == "手動輸入":
            kin_a = st.number_input("輸入 KIN", 1, 260, 1, key="ka")
            name_a = "自訂 A"
        else:
            name_a = sel_a.split(" (")[0]
            kin_a = int(sel_a.split("KIN ")[1].replace(")", ""))
        
        info_a = get_kin_info(kin_a)
        st.info(f"KIN {kin_a} {info_a['調性']}{info_a['圖騰']}")

    with col2:
        st.markdown("<br><br><h2 style='text-align:center'>+</h2>", unsafe_allow_html=True)

    # --- 選擇 B ---
    with col3:
        st.subheader("👤 夥伴 B")
        sel_b = st.selectbox("選擇成員", user_options, key="pb")
        if sel_b == "手動輸入":
            kin_b = st.number_input("輸入 KIN", 1, 260, 1, key="kb")
            name_b = "自訂 B"
        else:
            name_b = sel_b.split(" (")[0]
            kin_b = int(sel_b.split("KIN ")[1].replace(")", ""))
            
        info_b = get_kin_info(kin_b)
        st.info(f"KIN {kin_b} {info_b['調性']}{info_b['圖騰']}")

    if st.button("🔮 計算合盤", type="primary", use_container_width=True):
        comp_kin = get_composite_kin(kin_a, kin_b)
        comp_info = get_kin_info(comp_kin)
        
        st.divider()
        st.success(f"✨ {name_a} 與 {name_b} 的合盤結果： **KIN {comp_kin}**")
        
        # 顯示結果
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown(f"### {comp_info['調性']}{comp_info['圖騰']}")
            st.write(f"**波符**：{comp_info['wave_name']} 波符")
            if '祈禱文' in comp_info:
                st.write(f"**核心主題**：{comp_info['祈禱文'].split('。')[0]}")
            
            # 顯示合盤的主印記卡
            render_kin_card("合盤主印記", comp_info['圖騰數字'], comp_info['調性數字'], is_main=True)

        with c2:
            st.write(f"**合盤波符旅程**")
            w_path = os.path.join("assets/wavespells", comp_info['wave_img'])
            if os.path.exists(w_path):

                st.image(w_path)
