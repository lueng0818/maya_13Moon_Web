import os
import calendar
import datetime
from PIL import Image
import pandas as pd
import streamlit as st

# ────────────── Path Setup ──────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMG_DIR  = os.path.join(BASE_DIR, "images")

# 確保資料夾存在
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)

# ────────────── Page Config & CSS ──────────────
st.set_page_config(page_title="Maya 生命印記解碼", layout="wide", page_icon="🔮")
st.markdown(
    """<style>
    .hero {padding:4rem 2rem; text-align:center; background:#f0f5f9; border-radius: 10px; margin-bottom: 2rem;}
    .hero h1 {font-size:3rem; font-weight:700; margin-bottom:0.5rem; color: #1d4ed8;}
    .hero p  {font-size:1.25rem; margin-bottom:1.5rem; color: #4b5563;}
    .btn-primary {background:#1d4ed8; color:white; padding:0.75rem 1.5rem; border-radius:0.375rem; text-decoration:none;}
    .features, .example, .testimonials, .faq {padding:2rem; background: white; border-radius: 8px; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);}
    .footer {position:fixed; bottom:0; left:0; width:100%; background:#1f2937; color:white; text-align:center; padding:1rem; z-index:999;}
    .footer a {color:#60a5fa; text-decoration:none; margin:0 0.5rem;}
    /* 隱藏 Streamlit 預設 footer */
    footer {visibility: hidden;}
    </style>""",
    unsafe_allow_html=True,
)

# ────────────── Logic & Data Generation ──────────────
# 為了讓程式能獨立運作，這裡內建了計算邏輯與資料生成
# 如果您有真實的 CSV，它會優先讀取 CSV

def generate_kin_data():
    """生成 1-260 KIN 的基本資料 (如果沒有 CSV)"""
    seals = ["紅龍","白風","藍夜","黃種子","紅蛇","白世界橋","藍手","黃星星","紅月","白狗",
             "藍猴","黃人","紅天行者","白巫師","藍鷹","黃戰士","紅地球","白鏡","藍風暴","黃太陽"]
    tones = ["磁性","月亮","電力","自我存在","超頻","韻律","共振","銀河星系","太陽","行星","光譜","水晶","宇宙"]
    
    data = []
    for k in range(1, 261):
        s_idx = (k - 1) % 20
        t_idx = (k - 1) % 13
        totem = seals[s_idx]
        tone = tones[t_idx]
        data.append({
            "KIN": k,
            "主印記": f"{tone}{totem}",
            "圖騰": totem,
            "調性": tone
        })
    return pd.DataFrame(data)

def generate_interpretation_data():
    """生成圖騰解釋範本 (如果沒有 CSV)"""
    seals = ["紅龍","白風","藍夜","黃種子","紅蛇","白世界橋","藍手","黃星星","紅月","白狗",
             "藍猴","黃人","紅天行者","白巫師","藍鷹","黃戰士","紅地球","白鏡","藍風暴","黃太陽"]
    
    data = []
    for s in seals:
        data.append({
            "圖騰": s,
            "你是誰": f"你是【{s}】，擁有獨特的能量頻率。",
            "最常遇到的瓶頸": f"作為{s}，有時會感到能量流動受阻或過度。",
            "建議": f"試著連結{s}的原型力量，保持覺知。",
            "擁有什麼樣的禮物": f"你的天賦在於展現{s}的高頻特質。"
        })
    return pd.DataFrame(data)

def calculate_kin_from_date(y, m, d):
    """標準 13 月亮曆算法 (Reference: 2023/7/26 = KIN 1)"""
    ref_date = datetime.date(2023, 7, 26)
    target_date = datetime.date(y, m, d)
    delta = (target_date - ref_date).days
    kin = (1 + delta) % 260
    return 260 if kin == 0 else kin

# ────────────── Load Data ──────────────
# 嘗試讀取 CSV，失敗則使用內建生成函數
try:
    # 這裡我們稍微調整邏輯：不讀取 start_year 和 month_accum，直接用 datetime 算 KIN
    # 但保留 kin_basic 和 self_df 的結構
    
    path_kin = os.path.join(DATA_DIR, "kin_basic_info.csv")
    path_interp = os.path.join(DATA_DIR, "totem_interpretation_new.csv")
    
    if os.path.exists(path_kin):
        kin_basic = pd.read_csv(path_kin)
    else:
        kin_basic = generate_kin_data()
        
    if os.path.exists(path_interp):
        self_df = pd.read_csv(path_interp)
    else:
        self_df = generate_interpretation_data()

except Exception as e:
    st.error(f"❌ 資料初始化失敗：{e}")
    st.stop()

# ────────────── Hero Section ──────────────
st.markdown(
    """
    <section class="hero">
      <h1>立即解碼你的 Maya 生命印記，喚醒宇宙支持能量</h1>
      <p>只要輸入出生日期，一鍵探索你的專屬靈性密碼，並獲得實踐建議──無需下載、馬上操作。</p>
      <p><em>請從左側面板輸入你的西元生日，即可立即查看。</em></p>
    </section>
    """,
    unsafe_allow_html=True,
)

# ────────────── Sidebar Input ──────────────
st.sidebar.header("📅 查詢你的 Maya 印記")
# 年份範圍設定
years = list(range(1920, 2031))
year = st.sidebar.selectbox("西元年", years, index=years.index(1990))
month = st.sidebar.selectbox("月份", list(range(1,13)), index=0)

# 動態計算該月最大天數
try:
    max_day = calendar.monthrange(year, month)[1]
except:
    max_day = 31 
day = st.sidebar.slider("日期", 1, max_day, 1)

# ────────────── KIN 計算 ──────────────
# 使用 Datetime 核心算法取代查表法，更精準
try:
    kin = calculate_kin_from_date(year, month, day)
except Exception as e:
    st.sidebar.error(f"日期無效: {e}")
    st.stop()

# ────────────── 顯示基本 KIN 與圖騰 ──────────────
subset = kin_basic[kin_basic["KIN"] == kin]

if subset.empty:
    st.error(f"❓ 找不到 KIN {kin} 資料，請檢查 kin_basic_info.csv")
    st.stop()

info = subset.iloc[0]
totem = info["圖騰"]
tone = info["調性"]
full_name = info["主印記"]

col1, col2 = st.columns([1, 2])

with col1:
    # 嘗試顯示圖片，若無則顯示替代文字
    # 圖片命名邏輯：假設圖片名為 "紅龍.png"
    img_file = os.path.join(IMG_DIR, f"{totem}.png")
    # 如果找不到 png，嘗試 jpg
    if not os.path.exists(img_file):
        img_file = os.path.join(IMG_DIR, f"{totem}.jpg")
        
    if os.path.exists(img_file):
        st.image(Image.open(img_file), width=150)
    else:
        # 如果沒有圖片，顯示一個帶顏色的圓圈
        st.markdown(f"""
        <div style="width:120px; height:120px; background:#eee; border-radius:50%; 
        display:flex; align-items:center; justify-content:center; border: 4px solid #d4af37;">
            <span style="font-size:24px;">{totem[0]}</span>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown(f"## 🔢 KIN {kin}")
    st.markdown(f"<h3 style='color:#d4af37;'>{full_name}</h3>", unsafe_allow_html=True)
    st.markdown(f"**圖騰：** {totem} ｜ **調性：** {tone}")

# ────────────── 功能說明 ──────────────
with st.expander("🔍 點擊查看功能說明", expanded=False):
    st.markdown("""
    1. **輸入你的生日**：選擇西元年／月／日，精準算出你的 Maya 能量頻率（KIN）。
    2. **一鍵生成印記**：系統自動計算並對應 20 種圖騰。
    3. **深入能量解讀**：解鎖你的天賦、挑戰與角色定位。
    4. **分享與回饋**：將你的專屬印記分享給朋友。
    """)

# ────────────── caption mapping ──────────────
descriptions = {
  "你是誰": "← 描述你的個性或能量特質…",
  "最常遇到的瓶頸": "← 代表你比較容易卡關的地方…",
  "建議": "← 提供簡單可行的日常提醒…",
  "擁有什麼樣的禮物": "← 你天生擁有的天賦與力量…",
}

def render_section(df_row, items, edu_pts):
    # 顯示教育提示
    for pt in edu_pts:
        st.info(pt)
    
    st.markdown("---")
    
    # 使用 2x2 grid 排版
    cols = st.columns(2)
    
    for idx, (col_key, label) in enumerate(items):
        if col_key not in df_row: continue
        
        with cols[idx % 2]:
            st.markdown(f"#### {label}")
            cap = descriptions.get(col_key)
            if cap: st.caption(cap)
            
            content = df_row[col_key]
            # 美化輸出框
            st.markdown(
                f"""<div style="background:#f8f9fa; padding:15px; border-radius:5px; border-left:4px solid #1d4ed8; margin-bottom:20px;">
                {content}
                </div>""", 
                unsafe_allow_html=True
            )

# ────────────── 深度解讀：自我探索 ──────────────
st.markdown("### 🔮 深度解讀：自我探索")

# 篩選對應圖騰的解釋
interp_subset = self_df[self_df["圖騰"] == totem]

if not interp_subset.empty:
    row = interp_subset.iloc[0]
    render_section(
        row,
        [("你是誰","🙋 你是誰"),
         ("最常遇到的瓶頸","🚧 最常遇到的瓶頸"),
         ("建議","🪄 建議"),
         ("擁有什麼樣的禮物","🎁 擁有什麼樣的禮物")],
        [f"「{totem}」是你的角色原型，幫助你看見優勢與盲點。", "內化這份能量，成為更完整的自己。"]
    )
else:
    st.warning(f"目前資料庫中尚未建立「{totem}」的詳細解讀資料。")

# ────────────── 深度解讀範例 (固定顯示) ──────────────
st.markdown('<div class="example">', unsafe_allow_html=True)
st.markdown("### 📖 深度解讀範例 (參考)")
st.markdown("""
- **圖騰：** 白狗  
- **核心能量：** 護佑、守護、內在安定  
- **建議實踐：** 每日冥想前，點蠟燭並呼吸三分鐘，想像溫暖的火焰保障你的安全。  
- **背後故事：** 白狗象徵夜晚的守護神，牠引領靈魂穿越黑暗，回到自我中心。
""")
st.markdown('</div>', unsafe_allow_html=True)

# ────────────── 案例分享 ──────────────
st.markdown('<div class="testimonials">', unsafe_allow_html=True)
st.markdown("### ❤️ 使用者案例分享")
st.markdown("""
> **小芸，35 歲｜自由工作者** > “第一次查到『藍鷹』印記，就驚覺自己其實一直渴望自由翱翔。照著建議練習後，一個月內順利接下夢想案子！”
""")
st.markdown('</div>', unsafe_allow_html=True)

# ────────────── 常見問題 ──────────────
st.markdown('<div class="faq">', unsafe_allow_html=True)
st.markdown("### ❓ 常見問題")
st.markdown("""
- **為什麼查不到我的印記？** 請確認輸入格式（西元），或確認您的生日是否正確。  

- **一天可以查幾次？** 本系統無限制，但建議每次查詢後給自己一點時間消化訊息，穩定能量頻率。  
""")
st.markdown('</div>', unsafe_allow_html=True)

# 為了防止 footer 遮擋內容，加一點底部空間
st.markdown("<br><br><br>", unsafe_allow_html=True)

# ────────────── 固定 Footer ──────────────
st.markdown(
    """
    <footer class="footer">
      <a href="https://www.facebook.com/soulclean1413/" target="_blank">👉 加入粉專</a> 
      <a href="https://www.instagram.com/tilandky/" target="_blank">👉 追蹤IG</a>
      <a href="https://line.me/R/ti/p/%40690ZLAGN" target="_blank">👉 加入社群</a>
    </footer>
    """,
    unsafe_allow_html=True
)
