import streamlit as st
import datetime
import os
import sqlite3
from create_db_v2 import init_db
from kin_utils import (
    calculate_kin, get_full_kin_data, get_oracle, 
    calculate_life_castle, get_img_b64
)

# 自動初始化資料庫
if not os.path.exists("13moon.db"):
    init_db()

st.set_page_config(page_title="13 Moon Pro", layout="wide", page_icon="🔮")

# CSS
st.markdown("""
<style>
    .stApp { background-color: #111; color: #eee; }
    .kin-card {
        background: #222; border: 1px solid #444; 
        border-radius: 10px; padding: 10px; text-align: center;
    }
    .matrix-box {
        background: #000; color: #0f0; font-family: monospace;
        padding: 10px; border-radius: 5px; border: 1px solid #0f0;
        margin-top: 10px;
    }
    h1, h2, h3 { color: #d4af37 !important; }
</style>
""", unsafe_allow_html=True)

def show_card(label, seal, tone):
    # 構建圖片路徑
    s_path = f"assets/seals/{str(seal).zfill(2) if seal<10 else seal}{['','紅龍','白風','藍夜','黃種子','紅蛇','白世界橋','藍手','黃星星','紅月','白狗','藍猴','黃人','紅天行者','白巫師','藍鷹','黃戰士','紅地球','白鏡','藍風暴','黃太陽'][seal]}.jpg"
    # 注意：這裡圖檔名需要跟您 assets 裡的完全一致，若破圖請檢查 kin_utils 的 SEAL_FILES_FIXED
    # 這裡改用 kin_utils 的邏輯
    from kin_utils import SEAL_FILES_FIXED, TONE_FILES
    s_file = SEAL_FILES_FIXED.get(seal, "01紅龍.jpg")
    t_file = TONE_FILES.get(tone, "瑪雅曆法圖騰-34.png")
    
    with st.container():
        st.markdown(f"<div class='kin-card'>", unsafe_allow_html=True)
        st.image(f"assets/tones/{t_file}", width=30)
        st.image(f"assets/seals/{s_file}", width=70)
        st.caption(label)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 主程式 ---
st.sidebar.title("🌌 13月亮曆高階版")
mode = st.sidebar.radio("功能", ["個人星系解碼", "52流年城堡", "矩陣數據查詢"])

if mode == "個人星系解碼":
    st.title("🔮 個人星系印記解碼")
    d = st.date_input("生日", datetime.date.today())
    
    if st.button("解碼"):
        kin = calculate_kin(d)
        data = get_full_kin_data(kin)
        oracle = get_oracle(kin)
        
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.image(f"assets/seals/{data['seal_img']}", width=150)
            st.markdown(f"## KIN {kin}")
            st.markdown(f"### {data.get('調性','')}{data.get('圖騰','')}")
            
            # 顯示高階資料：矩陣
            st.markdown("#### 🧬 441 矩陣數據")
            st.markdown(f"""
            <div class='matrix-box'>
            時間矩陣: {data.get('Matrix_Time', 'N/A')}<br>
            空間矩陣: {data.get('Matrix_Space', 'N/A')}<br>
            共時矩陣: {data.get('Matrix_Sync', 'N/A')}<br>
            BMU: {data.get('Matrix_BMU', 'N/A')}
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.subheader("📜 祈禱文 & 易經")
            st.info(data.get('祈禱文', '無祈禱文資料'))
            
            if '對應卦象' in data:
                st.success(f"**易經卦象**：{data['對應卦象']}\n\n{data.get('IChing_Desc','')}")
            
            st.subheader("五大神諭")
            cols = st.columns(5)
            # 依序顯示
            with cols[0]: show_card("引導", oracle['guide']['seal'], oracle['guide']['tone'])
            with cols[1]: show_card("擴展", oracle['antipode']['seal'], oracle['antipode']['tone'])
            with cols[2]: show_card("主印記", oracle['destiny']['seal'], oracle['destiny']['tone'])
            with cols[3]: show_card("支持", oracle['analog']['seal'], oracle['analog']['tone'])
            with cols[4]: show_card("推動", oracle['occult']['seal'], oracle['occult']['tone'])

elif mode == "52流年城堡":
    st.title("🏰 52年生命城堡")
    d = st.date_input("生日", datetime.date(1990,1,1))
    
    if st.button("計算流年"):
        path = calculate_life_castle(d)
        
        # 顯示 0-51 歲
        cols = st.columns(4)
        for i, year_data in enumerate(path[:52]):
            c = cols[i % 4]
            with c:
                info = year_data['Info']
                seal_path = f"assets/seals/{info['seal_img']}"
                img_b64 = get_img_b64(seal_path)
                
                st.markdown(f"""
                <div style="background:{year_data['Color']}; padding:5px; border-radius:5px; margin-bottom:5px; color:black; text-align:center;">
                    <small>{year_data['Age']}歲 ({year_data['Year']})</small><br>
                    <b>KIN {year_data['KIN']}</b><br>
                    <img src="data:image/jpg;base64,{img_b64}" width="40"><br>
                    <small>{info.get('調性','')}{info.get('圖騰','')}</small>
                </div>
                """, unsafe_allow_html=True)

elif mode == "矩陣數據查詢":
    st.title("🧬 全腦調頻矩陣資料庫")
    conn = sqlite3.connect("13moon.db")
    try:
        df = pd.read_sql("SELECT * FROM Matrix_Data", conn)
        st.dataframe(df)
    except:
        st.error("矩陣資料尚未建立，請檢查 create_db_v2.py")
    conn.close()
