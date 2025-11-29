import streamlit as st
import pandas as pd
import datetime
import re
import os
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. 系統設定與常數
# ==========================================
st.set_page_config(
    page_title="13 Moon Synchronotron Master",
    page_icon="🌌",
    layout="wide"
)

TONES_NAME = ["", "磁性", "月亮", "電力", "自我存在", "超頻", "韻律", "共鳴", "銀河星系", "太陽", "行星", "光譜", "水晶", "宇宙"]
SEALS_NAME = ["", "紅龍", "白風", "藍夜", "黃種子", "紅蛇", "白世界橋", "藍手", "黃星星", "紅月", "白狗", "藍猴", "黃人", "紅天行者", "白巫師", "藍鷹", "黃戰士", "紅地球", "白鏡", "藍風暴", "黃太陽"]
SEAL_COLORS = {
    1: 'red', 2: 'white', 3: 'blue', 4: 'yellow',
    5: 'red', 6: 'white', 7: 'blue', 8: 'yellow',
    9: 'red', 10: 'white', 11: 'blue', 12: 'yellow',
    13: 'red', 14: 'white', 15: 'blue', 16: 'yellow',
    17: 'red', 18: 'white', 19: 'blue', 20: 'yellow'
}

MOON_NAMES = ["", "磁性之月", "月亮之月", "電力之月", "自我存在之月", "超頻之月", "韻律之月", "共鳴之月", "銀河星系之月", "太陽之月", "行星之月", "光譜之月", "水晶之月", "宇宙之月"]

TONE_QUESTIONS = {
    "磁性": "我的目的是什麼？", "月亮": "我的挑戰是什麼？", "電力": "我如何給予最佳的服務？",
    "自我存在": "我該以什麼形式來服務他人？", "超頻": "我如何能讓自己獲得最佳的力量？",
    "韻律": "我如何與他人擴大平等？", "共鳴": "我如何使我的服務與他人協調融合？",
    "銀河星系": "我是否活出我所相信的？", "太陽": "我如何完成我的目的？",
    "行星": "我如何完美我所做的？", "光譜": "我該如何釋放與放下？",
    "水晶": "我如何全心的奉獻予所有的生命？", "宇宙": "我如何活在當下？"
}

CASTLES_INFO = {
    "紅色東方啟動城堡": {"range": "Kin 1-52", "color_bg": "#FFCCCB", "court": "出生之庭", "theme": "啟動與開創", "desc": "適合發起新事物的起始開創課題。", "img": "assets/tokens/pyramid_red.png"},
    "白色北方跨越城堡": {"range": "Kin 53-104", "color_bg": "#F0F3F4", "court": "死亡之庭", "theme": "跨越與淨化", "desc": "透過淨化與斷捨離，跨越舊有。", "img": "assets/tokens/pyramid_white.png"},
    "藍色西方蛻變城堡": {"range": "Kin 105-156", "color_bg": "#D6EAF8", "court": "魔法之庭", "theme": "改變與轉化", "desc": "轉化能量，經歷如同蛇蛻皮般的重生。", "img": "assets/tokens/pyramid_blue.png"},
    "黃色南方給予城堡": {"range": "Kin 157-208", "color_bg": "#FCF3CF", "court": "智能之庭", "theme": "收穫與給予", "desc": "享受成果，分享智慧。", "img": "assets/tokens/pyramid_yellow.png"},
    "綠色中央魔法城堡": {"range": "Kin 209-260", "color_bg": "#D5F5E3", "court": "共時之庭", "theme": "共時與魔法", "desc": "協調人類與銀河意識。", "img": "assets/tokens/pyramid_green.png"}
}

TELEKTONON_MAP = {
    1: {"planet": "海王星 (Neptune)", "flow": "GK (銀河業力-吸入)", "circuit": "C2 記憶-本能", "pos": "左邊 (Left) - 軌道2"},
    2: {"planet": "天王星 (Uranus)", "flow": "GK (銀河業力-吸入)", "circuit": "C3 生物心電感應", "pos": "左邊 (Left) - 軌道3"},
    3: {"planet": "土星 (Saturn)", "flow": "GK (銀河業力-吸入)", "circuit": "C4 吸收智能", "pos": "左邊 (Left) - 軌道4"},
    4: {"planet": "木星 (Jupiter)", "flow": "GK (銀河業力-吸入)", "circuit": "C5 內在原子", "pos": "左邊 (Left) - 軌道5"},
    5: {"planet": "馬爾代克 (Maldek)", "flow": "GK (銀河業力-吸入)", "circuit": "C5 內在原子", "pos": "左邊 (Left) - 軌道5 (內)"},
    6: {"planet": "火星 (Mars)", "flow": "GK (銀河業力-吸入)", "circuit": "C4 吸收智能", "pos": "左邊 (Left) - 軌道4 (內)"},
    7: {"planet": "地球 (Earth)", "flow": "GK (銀河業力-吸入)", "circuit": "C3 生物心電感應", "pos": "左邊 (Left) - 軌道3 (內)"},
    8: {"planet": "金星 (Venus)", "flow": "GK (銀河業力-吸入)", "circuit": "C2 記憶-本能", "pos": "左邊 (Left) - 軌道2 (內)"},
    9: {"planet": "水星 (Mercury)", "flow": "GK (銀河業力-吸入)", "circuit": "C1 Alpha-Omega", "pos": "左邊 (Left) - 軌道1 (內)"},
    10: {"planet": "水星", "flow": "SP (太陽預言-呼出)", "circuit": "C1 Alpha-Omega", "pos": "右邊 (Right) - 軌道1 (內)"},
    11: {"planet": "金星 (Venus)", "flow": "SP (太陽預言-呼出)", "circuit": "C2 記憶-本能", "pos": "右邊 (Right) - 軌道2 (內)"},
    12: {"planet": "地球 (Earth)", "flow": "SP (太陽預言-呼出)", "circuit": "C3 生物心電感應", "pos": "右邊 (Right) - 軌道3 (內)"},
    13: {"planet": "火星 (Mars)", "flow": "SP (太陽預言-呼出)", "circuit": "C4 吸收智能", "pos": "右邊 (Right) - 軌道4 (內)"},
    14: {"planet": "馬爾代克 (Maldek)", "flow": "SP (太陽預言-呼出)", "circuit": "C5 內在原子", "pos": "右邊 (Right) - 軌道5 (內)"},
    15: {"planet": "木星 (Jupiter)", "flow": "SP (太陽預言-呼出)", "circuit": "C5 內在原子", "pos": "右邊 (Right) - 軌道5"},
    16: {"planet": "土星 (Saturn)", "flow": "SP (太陽預言-呼出)", "circuit": "C4 吸收智能", "pos": "右邊 (Right) - 軌道4"},
    17: {"planet": "天王星 (Uranus)", "flow": "SP (太陽預言-呼出)", "circuit": "C3 生物心電感應", "pos": "右邊 (Right) - 軌道3"},
    18: {"planet": "海王星 (Neptune)", "flow": "SP (太陽預言-呼出)", "circuit": "C2 記憶-本能", "pos": "右邊 (Right) - 軌道2"},
    19: {"planet": "冥王星 (Pluto)", "flow": "SP (太陽預言-呼出)", "circuit": "C1 Alpha-Omega", "pos": "右邊 (Right) - 軌道1"},
    20: {"planet": "冥王星 (Pluto)", "flow": "GK (銀河業力-吸入)", "circuit": "C1 Alpha-Omega", "pos": "左邊 (Left) - 軌道1 (0/20)"}
}

WARRIOR_JOURNEY = {
    7: "神性之源 (意志)", 8: "靈性 (呼吸)", 9: "豐盛 (夢想)", 10: "開花 (覺察)",
    11: "生命力 (本能)", 12: "死亡 (機會)", 13: "完成 (療癒)", 14: "藝術 (美麗)",
    15: "淨化 (也就是)", 16: "愛 (忠誠)", 17: "魔法 (遊戲)", 18: "自由意志 (智慧)",
    19: "預言 (覺醒)", 20: "永恆 (接受)", 21: "自生 (能量)", 22: "開悟 (宇宙之火)"
}

EARTH_JOURNEY = {
    1: "建立銀河業力流 (GK) - 實踐之塔底部", 2: "建立銀河業力流 (GK) - 實踐之塔中部", 3: "建立銀河業力流 (GK) - 實踐之塔頂部",
    4: "建立太陽預言流 (SP) - 智慧之塔底部", 5: "建立太陽預言流 (SP) - 智慧之塔中部", 6: "建立太陽預言流 (SP) - 智慧之塔頂部"
}

HEAVEN_JOURNEY = {
    23: "情人重聚日 - 國王與皇后相遇",
    24: "拆除太陽預言流 (SP) - 智慧之塔頂部", 25: "拆除太陽預言流 (SP) - 智慧之塔中部", 26: "拆除太陽預言流 (SP) - 智慧之塔底部",
    27: "拆除銀河業力流 (GK) - 實踐之塔頂部", 28: "拆除銀河業力流 (GK) - 實踐之塔中部"
}

# ==========================================
# 2. 資料載入層 (Data Layer)
# ==========================================
@st.cache_data
def load_data():
    data = {}
    files = {
        'start_year': "data/kin_start_year.csv",
        'month_accum': "data/month_day_accum.csv",
        'kin_info': "data/kin_basic_info.csv",
        'psi': "data/PSI印記對照表.csv",
        'plasma': "data/Heptad_Gate_Path.csv",
        'white_turtle': "data/White_Turtle_Day.csv",
        'week_keyword': "data/瑪亞週關鍵句.csv",
        'date_to_matrix': "data/瑪雅生日對時間矩陣對照表.csv",
        'base_matrix': "data/Base_Matrix_441.csv",
        'tzolkin_matrix': "data/Tzolkin_Matrix.csv",
        'iching': "data/銀河易經編碼.csv",
        'time_matrix': "data/Time_Matrix.csv",
        'space_matrix': "data/Space_Matrix.csv",
        'synchronic_matrix': "data/Synchronic_Matrix.csv"
    }
    for key, filename in files.items():
        try:
            if os.path.exists(filename):
                df = pd.read_csv(filename)
                if len(df.columns) > 0 and ("Unnamed" in str(df.columns[0]) or "Unnamed" in str(df.columns[1])):
                     df = pd.read_csv(filename, header=1)
                df.columns = [str(c).strip() for c in df.columns]
                data[key] = df
            else: data[key] = None
        except: data[key] = None

    if data['start_year'] is not None:
        data['start_year_dict'] = dict(zip(data['start_year']['年份'], data['start_year']['起始KIN']))
    if data['month_accum'] is not None:
        data['month_accum_dict'] = dict(zip(data['month_accum']['月份'], data['month_accum']['累積天數']))
    
    data['harmonic_map'] = {}
    if data['iching'] is not None:
        for _, row in data['iching'].iterrows():
            try:
                match = re.search(r'諧波(\d+)', str(row.get('諧波', '')))
                if match: data['harmonic_map'][int(match.group(1))] = row.to_dict()
            except: continue
    return data

# --- Google Sheets 資料庫 ---
def load_contacts_db():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df = conn.read(worksheet="contacts", ttl=0)
        return conn, df
    except:
        return conn, pd.DataFrame(columns=["姓名", "生日", "KIN"])

def save_contact(conn, df, name, birth_date, kin_num):
    new_data = pd.DataFrame([{"姓名": name, "生日": str(birth_date), "KIN": int(kin_num)}])
    updated_df = pd.concat([df, new_data], ignore_index=True)
    conn.update(worksheet="contacts", data=updated_df)
    return updated_df

DB = load_data()

# ==========================================
# 3. 邏輯核心層
# ==========================================

def find_kin_num(tone, seal):
    for k in range(1, 261):
        if (k-1)%13+1 == tone and (k-1)%20+1 == seal: return k
    return 0

def calculate_kin_num(year, month, day, db):
    if db['start_year'] is None: return None
    start_kin = db['start_year_dict'].get(year)
    if not start_kin: return None
    accum = db['month_accum_dict'].get(month, 0)
    total = start_kin + accum + day
    kin = total % 260
    return 260 if kin == 0 else kin

def get_kin_details(kin_num, db):
    if not kin_num or db['kin_info'] is None: return {}
    row = db['kin_info'][db['kin_info']['KIN'] == kin_num]
    if not row.empty: return row.iloc[0].to_dict()
    t = (kin_num - 1) % 13 + 1
    s = (kin_num - 1) % 20 + 1
    return {'KIN': kin_num, '主印記': f"{TONES_NAME[t]}{SEALS_NAME[s]}", '圖騰': SEALS_NAME[s], '波符': '', '城堡': ''}

def calculate_oracle(kin_num, db):
    if not kin_num: return None
    t = (kin_num - 1) % 13 + 1
    s = (kin_num - 1) % 20 + 1
    s_ana = (19 - s); 
    if s_ana <= 0: s_ana += 20
    s_anti = (s + 10) % 20
    if s_anti == 0: s_anti = 20
    s_occ = (21 - s)
    if s_occ <= 0: s_occ += 20
    t_occ = 14 - t
    s_guide = s
    if t in [2,7,12]: s_guide = (s + 12) % 20
    elif t in [3,8,13]: s_guide = (s + 4) % 20
    elif t in [4,9]: s_guide = (s - 4)
    elif t in [5,10]: s_guide = (s + 8) % 20
    if s_guide <= 0: s_guide += 20
    if s_guide == 0: s_guide = 20
    return {
        'main': get_kin_details(kin_num, db),
        'analog': get_kin_details(find_kin_num(t, s_ana), db),
        'antipode': get_kin_details(find_kin_num(t, s_anti), db),
        'occult': get_kin_details(find_kin_num(t_occ, s_occ), db),
        'guide': get_kin_details(find_kin_num(t, s_guide), db)
    }

def get_psi_kin(date_obj, main_kin_num, db):
    m, d = date_obj.month, date_obj.day
    if m == 7 and d == 25: return main_kin_num, "無時間日"
    query = f"{m}月{d}日"
    if db['psi'] is not None:
        row = db['psi'][db['psi']['月日'] == query]
        if row.empty:
            query2 = f"{m:02d}月{d:02d}日"
            row = db['psi'][db['psi']['國曆生日'] == query2]
        if not row.empty:
            try: return int(row.iloc[0]['PSI印記']), "PSI資料庫"
            except: pass
    return None, "未知"

def calculate_goddess_force(oracle_data, db):
    if not oracle_data: return None
    kins = [oracle_data[k]['KIN'] for k in ['main', 'analog', 'antipode', 'occult', 'guide']]
    tones = [(k - 1) % 13 + 1 for k in kins]
    seals = [(k - 1) % 20 + 1 for k in kins]
    final_tone = (sum(tones) - 1) % 13 + 1
    final_seal = (sum(seals) - 1) % 20 + 1
    return get_kin_details(find_kin_num(final_tone, final_seal), db)

def get_13moon_date(date_obj):
    year = date_obj.year
    start_date = datetime.date(year, 7, 26)
    if date_obj < start_date: start_date = datetime.date(year - 1, 7, 26)
    delta = (date_obj - start_date).days
    if delta == 364: return "Day Out of Time", 0, 0, 0
    moon = (delta // 28) + 1
    day = (delta % 28) + 1
    heptad_week = (delta // 7) + 1
    return f"{moon}.{day}", moon, day, heptad_week

def calculate_flow_year_kin(birth_date, db):
    today = datetime.date.today()
    this_year_bday = datetime.date(today.year, birth_date.month, birth_date.day)
    target_year = today.year if today >= this_year_bday else today.year - 1
    flow_kin_num = calculate_kin_num(target_year, birth_date.month, birth_date.day, db)
    return target_year, get_kin_details(flow_kin_num, db)

def get_daily_energy(moon, day, db):
    info = {}
    if db['plasma'] is not None:
        row = db['plasma'][db['plasma']['第幾天'] == day]
        if not row.empty: info['plasma'] = row.iloc[0].to_dict()
    if db['week_keyword'] is not None:
        week_idx = (day - 1) // 7
        weeks = ['紅色啟動之週', '白色淨化之週', '藍色蛻變之週', '黃色收穫之週']
        if 0 <= week_idx < 4:
            w_name = weeks[week_idx]
            row = db['week_keyword'][db['week_keyword']['瑪雅週'] == w_name]
            if not row.empty: info['week'] = row.iloc[0].to_dict()
    return info

def calculate_today_kin(db):
    today = datetime.date.today()
    kin = calculate_kin_num(today.year, today.month, today.day, db)
    return today, get_kin_details(kin, db)

def calculate_relationship(kin1, kin2, db):
    if not kin1 or not kin2: return None
    combined_kin_num = (kin1 + kin2 - 1) % 260 + 1
    t1 = (kin1 - 1) % 13 + 1; s1 = (kin1 - 1) % 20 + 1
    t2 = (kin2 - 1) % 13 + 1; s2 = (kin2 - 1) % 20 + 1
    combined_tone = (t1 + t2 - 1) % 13 + 1
    combined_seal = (s1 + s2 - 1) % 20 + 1
    return {'KIN': combined_kin_num, 'info': get_kin_details(combined_kin_num, db), 'tone_sum': combined_tone, 'seal_sum': combined_seal}

def get_journey_earth_heaven(day):
    if 1 <= day <= 6:
        step = EARTH_JOURNEY.get(day, "建立基地")
        return f"🌍 地球之旅 (Day {day})", step, ["assets/tokens/turtle_yellow.png", "assets/tokens/turtle_white.png"], "黃上白下 (頭右)"
    elif 7 <= day <= 22:
        return f"🛤️ 分道揚鑣 (Day {day})", "黃烏龜：繼續前進 / 白烏龜：Day 6 原地等待", ["assets/tokens/turtle_yellow.png", "assets/tokens/turtle_white.png"], "分開行動"
    elif 23 <= day <= 28:
        heaven_step = HEAVEN_JOURNEY.get(day, "返回天堂")
        return f"☁️ 天堂之旅 (Day {day})", heaven_step, ["assets/tokens/turtle_yellow.png", "assets/tokens/turtle_white.png"], "肩並肩 (黃左白右, 頭左)"
    return "無時間日", "自由", [], ""

def get_journey_warrior(day):
    if 7 <= day <= 22:
        warrior_step = WARRIOR_JOURNEY.get(day, "奪回力量")
        return f"⚔️ 戰士立方體之旅 (Day {day})", warrior_step, "assets/tokens/turtle_green.png"
    return None, None, None

def get_telektonon_info(seal_idx):
    return TELEKTONON_MAP.get(seal_idx, {})

def calculate_synchronotron_data(date_obj, main_kin, db):
    logs = []
    m, d = date_obj.month, date_obj.day
    q = f"{m:02d}/{d:02d}"
    pos_1 = None
    if db['date_to_matrix'] is not None:
        row = db['date_to_matrix'][db['date_to_matrix']['月日'] == q]
        if not row.empty: pos_1 = row.iloc[0]['時間矩陣位置']
        elif m==7 and d==25: pos_1 = "V11:H11"
    if not pos_1: return None, ["無法定位生辰座標"]

    def get_val(key, pos):
        if db[key] is None or not pos: return 0
        df = db[key]
        try: 
            r = df[df['矩陣位置'].astype(str).str.strip() == str(pos).strip()]
            if not r.empty: return int(r.iloc[0]['KIN'])
        except: pass
        return 0
    
    def get_pos(key, k):
        if db[key] is None: return None
        df = db[key]
        try:
            r = df[df['KIN'] == k]
            if not r.empty: return r.iloc[0]['矩陣位置']
        except: pass
        return None

    v_t1 = get_val('time_matrix', pos_1)
    v_s1 = get_val('space_matrix', pos_1)
    v_sy1 = get_val('synchronic_matrix', pos_1)
    sum_1 = v_t1 + v_s1 + v_sy1
    logs.append(f"1. 時間矩陣座標 {pos_1} → {v_t1} + {v_s1} + {v_sy1} = {sum_1}")
    
    pos_2 = get_pos('space_matrix', main_kin)
    v_t2 = get_val('time_matrix', pos_2)
    v_s2 = main_kin
    v_sy2 = get_val('synchronic_matrix', pos_2)
    sum_2 = v_t2 + v_s2 + v_sy2
    logs.append(f"2. 空間矩陣座標 {pos_2} → {v_t2} + {v_s2} + {v_sy2} = {sum_2}")
    
    pos_3 = get_pos('tzolkin_matrix', main_kin)
    v_t3 = get_val('time_matrix', pos_3)
    v_s3 = get_val('space_matrix', pos_3)
    v_sy3 = main_kin
    sum_3 = v_t3 + v_s3 + v_sy3
    logs.append(f"3. 共時矩陣座標 {pos_3} → {v_t3} + {v_s3} + {v_sy3} = {sum_3}")
    
    mcf = sum_1 + sum_2 + sum_3
    bmu = (mcf - 1) % 441 + 1
    kin_equiv = (mcf - 1) % 260 + 1
    return {'MCF': mcf, 'BMU': bmu, 'KIN_EQUIV': get_kin_details(kin_equiv, db), 'logs': logs}

# --- 輔助：圖片顯示 ---
def render_kin_card(title, kin_num, kin_info, bg_color="#FFFFFF"):
    with st.container():
        st.markdown(f"**{title}**")
        seal_idx = (kin_num - 1) % 20 + 1
        tone_idx = (kin_num - 1) % 13 + 1
        seal_path = f"assets/seals/{seal_idx:02d}.jpg" 
        tone_path = f"assets/tones/tone-{tone_idx}.png"
        col_imgs, col_txt = st.columns([2, 2])
        with col_imgs:
            c1, c2 = st.columns(2)
            with c1:
                if os.path.exists(tone_path): st.image(tone_path, width=50)
                else: st.caption(f"Tone {tone_idx}")
            with c2:
                if os.path.exists(seal_path): st.image(seal_path, width=60)
                else: st.caption(f"Seal {seal_idx}")
        with col_txt:
            st.markdown(f"""
            <div style="background-color:{bg_color}; padding:10px; border-radius:5px; border:1px solid #ddd; height:100%;">
                <div style="font-size:18px; font-weight:bold;">KIN {kin_num}</div>
                <div style="font-size:14px;">{kin_info.get('圖騰', '')}</div>
                <div style="font-size:12px; color:#666;">{kin_info.get('主印記', '')}</div>
            </div>
            """, unsafe_allow_html=True)

def render_large_kin(kin_num, kin_info):
    seal_idx = (kin_num - 1) % 20 + 1
    tone_idx = (kin_num - 1) % 13 + 1
    seal_path = f"assets/seals/{seal_idx:02d}.jpg"
    tone_path = f"assets/tones/tone-{tone_idx}.png"
    c1, c2 = st.columns([1, 2])
    with c1:
        if os.path.exists(tone_path): st.image(tone_path, width=80)
        if os.path.exists(seal_path): st.image(seal_path, width=250, caption=kin_info.get('主印記'))
        else: st.markdown(f"### KIN {kin_num} {kin_info.get('主印記')}")
    return c2

def get_pyramid_path(kin_num, is_main=False):
    if not kin_num: return None
    if is_main: return "assets/tokens/pyramid_green.png"
    seal_idx = (kin_num - 1) % 20 + 1
    color = SEAL_COLORS.get(seal_idx, 'green')
    return f"assets/tokens/pyramid_{color}.png"

def render_oracle_pyramid(title, kin_num, kin_info):
    with st.container():
        st.markdown(f"**{title}**")
        st.caption(f"KIN {kin_num} {kin_info.get('圖騰')}")
        is_destiny = ("命運" in title)
        pyr_path = get_pyramid_path(kin_num, is_destiny)
        if os.path.exists(pyr_path): st.image(pyr_path, width=80)
        else: st.markdown("⚠️") 
        s_idx = (kin_num - 1) % 20 + 1
        t_data = get_telektonon_info(s_idx)
        st.markdown(f"""<div style="font-size:12px; line-height:1.2;">🪐 {t_data.get('planet')}<br>⚡ {t_data.get('circuit')}<br>🌊 {t_data.get('flow')}</div>""", unsafe_allow_html=True)

# ==========================================
# 4. 前端展示層
# ==========================================

if DB is None: st.stop()

# --- Sidebar ---
st.sidebar.header("🌌 使用者資料")

# 資料庫載入與選單
conn, contacts_df = load_contacts_db()
selected_contact = "-- 請選擇 --"
if not contacts_df.empty:
    contact_list = contacts_df['姓名'].tolist()
    selected_contact = st.sidebar.selectbox("從通訊錄選擇", ["-- 請選擇 --"] + contact_list)

if selected_contact != "-- 請選擇 --":
    row = contacts_df[contacts_df['姓名'] == selected_contact].iloc[0]
    saved_birth = datetime.datetime.strptime(row['生日'], "%Y-%m-%d").date()
    birth_date = st.sidebar.date_input("生日", value=saved_birth)
else:
    birth_date = st.sidebar.date_input("請輸入生日", value=datetime.date(1985, 10, 24))

# 核心計算
kin_A = calculate_kin_num(birth_date.year, birth_date.month, birth_date.day, DB)
info_A = get_kin_details(kin_A, DB)

# 儲存按鈕
st.sidebar.markdown("---")
with st.sidebar.expander("儲存到通訊錄"):
    new_name = st.text_input("輸入名字")
    if st.button("儲存"):
        if new_name:
            save_contact(conn, contacts_df, new_name, birth_date, kin_A)
            st.success(f"已儲存 {new_name}")
            st.rerun()

# 執行其他計算
oracle_A = calculate_oracle(kin_A, DB)
psi_num, _ = get_psi_kin(birth_date, kin_A, DB)
psi_info = get_kin_details(psi_num, DB)
goddess_info = calculate_goddess_force(oracle_A, DB)
sync_data = calculate_synchronotron_data(birth_date, kin_A, DB)
flow_year_val, flow_year_info = calculate_flow_year_kin(birth_date, DB)
today_date, today_kin_info = calculate_today_kin(DB)
moon_str, moon_num, day_num, heptad_week = get_13moon_date(today_date)
daily_energy = get_daily_energy(moon_num, day_num, DB)
today_oracle = calculate_oracle(today_kin_info['KIN'], DB)

st.title("🌌 13 Moon Synchronotron Master System")
st.markdown(f"**歡迎來到時間法則的中心** | 今日: {today_date} | KIN {today_kin_info['KIN']}")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔮 靈魂藍圖", "🏰 時間地圖", "🌊 流年與運勢", "💞 關係合盤", "👑 國王棋盤", "🧠 441 共時化科學"
])

# --- Tab 1 ---
with tab1:
    col_text = render_large_kin(kin_A, info_A)
    with col_text:
        st.subheader("核心印記資訊")
        st.write(f"**PSI 印記**：KIN {psi_num} {psi_info.get('主印記')}")
        st.write(f"**女神印記**：KIN {goddess_info['KIN']} {goddess_info.get('主印記')}")
        st.write(f"**波符**：{info_A.get('波符')}")
        st.info("調性 (Bar-Dot) 代表頻率，圖騰 (Seal) 代表原型能量。")
    st.markdown("---")
    st.subheader("🧩 五大神諭佈陣")
    cols = st.columns(5)
    keys = ['guide', 'analog', 'main', 'antipode', 'occult']
    colors = ["#F4F6F6", "#F4F6F6", "#FCF3CF", "#F4F6F6", "#F4F6F6"]
    labels = ["指引", "支持", "命運", "挑戰", "隱藏"]
    for i, col in enumerate(cols):
        with col:
            k = oracle_A[keys[i]]
            render_kin_card(labels[i], k['KIN'], k, colors[i])

# --- Tab 2 ---
with tab2:
    castle_name = info_A.get('城堡', '')
    castle_data = None
    for c_key, c_val in CASTLES_INFO.items():
        if c_key in castle_name: castle_data = c_val
    st.subheader("🏰 生命城堡 (52 天週期)")
    if castle_data:
        c1, c2 = st.columns([1, 3])
        with c1:
            if os.path.exists(castle_data['img']):
                st.image(castle_data['img'], width=100)
        with c2:
            st.markdown(f"""
            <div style="background-color:{castle_data['color_bg']}; padding:15px; border-radius:10px; border:1px solid #ddd;">
                <h3 style="margin:0;">{castle_name}</h3>
                <p><strong>{castle_data['court']}</strong></p>
                <p><strong>{castle_data['theme']}</strong> ({castle_data['range']})</p>
                <p>{castle_data['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("🌊 波符生命道路 (13 天週期)")
    with st.expander(f"查看 {info_A.get('波符')} 的 13 個提問"):
        for t_name, q in TONE_QUESTIONS.items(): st.write(f"**{t_name}調性**：{q}")

# --- Tab 3 ---
with tab3:
    st.subheader(f"🌊 流年 ({flow_year_val})")
    c1, c2 = st.columns([1, 3])
    with c1:
        fk = flow_year_info['KIN']
        f_s_idx = (fk - 1) % 20 + 1
        f_t_idx = (fk - 1) % 13 + 1
        f_img = f"assets/seals/{f_s_idx:02d}.jpg"
        t_img = f"assets/tones/tone-{f_t_idx}.png"
        if os.path.exists(t_img): st.image(t_img, width=40)
        if os.path.exists(f_img): st.image(f_img, width=120)
        st.metric("流年 KIN", fk)
    with c2: 
        st.markdown(f"### {flow_year_info.get('主印記')}")
        st.write(f"**波符**：{flow_year_info.get('波符')}")

# --- Tab 4 ---
with tab4:
    st.header("💞 關係能量合盤")
    
    # 從資料庫選擇對象
    rel_contact = st.selectbox("選擇合盤對象", ["-- 自訂輸入 --"] + (contacts_df['姓名'].tolist() if not contacts_df.empty else []))
    
    if rel_contact != "-- 自訂輸入 --":
        row_b = contacts_df[contacts_df['姓名'] == rel_contact].iloc[0]
        b_date = datetime.datetime.strptime(row_b['生日'], "%Y-%m-%d").date()
        st.info(f"已載入：{rel_contact} ({b_date})")
    else:
        b_date = st.date_input("對方生日", value=datetime.date(1990, 1, 1))
        
    kin_B = calculate_kin_num(b_date.year, b_date.month, b_date.day, DB)
    combined = calculate_relationship(kin_A, kin_B, DB)
    
    if combined:
        cinfo = combined['info']
        ck = combined['KIN']
        c1, c2 = st.columns([1, 2])
        with c1:
            c_s_idx = (ck - 1) % 20 + 1
            c_t_idx = (ck - 1) % 13 + 1
            c_img = f"assets/seals/{c_s_idx:02d}.jpg"
            ct_img = f"assets/tones/tone-{c_t_idx}.png"
            if os.path.exists(ct_img): st.image(ct_img, width=50)
            if os.path.exists(c_img): st.image(c_img, width=150)
        with c2:
            st.markdown(f"### 合盤 KIN {ck} {cinfo.get('主印記')}")
            st.write(f"**波符**：{cinfo.get('波符')}")
            st.write(f"**城堡**：{cinfo.get('城堡')}")

# --- Tab 5: 國王棋盤 ---
with tab5:
    st.header("👑 Telektonon 預言棋盤")
    
    board_img = "assets/tokens/telektonon_board.jpg"
    if os.path.exists(board_img):
        st.image(board_img, caption="Telektonon 預言遊戲棋盤", use_column_width=True)
    
    if 1 <= day_num <= 6:
        path_img = "assets/tokens/yellow_white_path_1_6.jpg"
        if os.path.exists(path_img): st.image(path_img, caption="黃白烏龜地球之旅 (Day 1-6)", width=400)
    elif 23 <= day_num <= 28:
        path_img = "assets/tokens/heaven_reunion_path.jpg"
        if os.path.exists(path_img): st.image(path_img, caption="天堂之旅 (Day 23-28)", width=400)
    elif 7 <= day_num <= 22:
        warrior_img = "assets/tokens/warrior_yellow_white_path.jpg"
        if os.path.exists(warrior_img): st.image(warrior_img, caption="戰士期間分道揚鑣 (Day 7-22)", width=400)

    # 1. 13:20 羅盤
    st.markdown("---")
    st.subheader("🧭 13:20 羅盤每日校準")
    c_compass, c_inst = st.columns([1, 1])
    with c_compass:
        compass_img = "assets/tokens/compass_1320.jpg"
        if os.path.exists(compass_img): st.image(compass_img, width=300)
    with c_inst:
        t_idx = (today_kin_info['KIN'] - 1) % 13 + 1
        s_idx = (today_kin_info['KIN'] - 1) % 20 + 1
        st.success(f"**今日校準：KIN {today_kin_info['KIN']}**")
        c_w, c_b = st.columns(2)
        with c_w:
            st.image("assets/tokens/particle_white.png", width=50)
            st.write(f"**白粒子**：內圈 第 {t_idx} 格")
        with c_b:
            st.image("assets/tokens/particle_black.png", width=50)
            st.write(f"**黑粒子**：外圈 第 {s_idx} 格")

    # 2. 13:28 羅盤
    st.markdown("---")
    st.subheader("🗓️ 13:28 羅盤每日校準")
    c_comp2, c_inst2 = st.columns([1, 1])
    with c_comp2:
        compass2 = "assets/tokens/compass_1328.jpg"
        if os.path.exists(compass2): st.image(compass2, width=300)
    with c_inst2:
        st.success(f"**今日校準：{MOON_NAMES[moon_num]} 第 {day_num} 天**")
        c_w2, c_b2 = st.columns(2)
        with c_w2:
            st.image("assets/tokens/particle_white.png", width=50)
            st.write(f"**白粒子**：內圈 第 {moon_num} 格")
        with c_b2:
            st.image("assets/tokens/particle_black.png", width=50)
            st.write(f"**黑粒子**：外圈 第 {day_num} 格")

    # 3. 烏龜移動
    st.markdown("---")
    st.subheader("🐢 烏龜移動")
    
    eh_name, eh_desc, eh_imgs, eh_hint = get_journey_earth_heaven(day_num)
    st.write(f"**{eh_name}** — {eh_desc}")
    if eh_hint: st.caption(f"提示：{eh_hint}")
    if eh_imgs:
        c1, c2 = st.columns(2)
        with c1: st.image(eh_imgs[0], caption="黃烏龜 (國王)", width=80)
        with c2: st.image(eh_imgs[1], caption="白烏龜 (皇后)", width=80)
        
    warrior_name, warrior_desc, warrior_img = get_journey_warrior(day_num)
    if warrior_name:
        st.divider()
        st.info(f"**{warrior_name}** — {warrior_desc}")
        if os.path.exists(warrior_img):
            st.image(warrior_img, caption="綠烏龜 (戰士)", width=80)

    # 4. 水晶與金字塔
    st.markdown("---")
    st.subheader("🏛️ 神諭金字塔佈陣 (GK/SP 能量流)")
    flow_img = "assets/tokens/gk_sp_flow.jpg"
    if os.path.exists(flow_img):
        st.image(flow_img, caption="GK (左) / SP (右) 垂直能量流", use_column_width=True)
    
    cols = st.columns(5)
    keys = ['guide', 'analog', 'main', 'antipode', 'occult']
    labels = ["指引", "支持", "命運", "挑戰", "隱藏"]
    for i, col in enumerate(cols):
        k_info = today_oracle[keys[i]]
        with col:
            render_oracle_pyramid(labels[i], k_info['KIN'], k_info)
    
    st.markdown("---")
    c_cry1, c_cry2 = st.columns([1, 3])
    with c_cry1:
        if os.path.exists("assets/tokens/crystal.png"):
            st.image("assets/tokens/crystal.png", width=80)
    with c_cry2:
        if os.path.exists("assets/tokens/crystal_battery.jpg"):
            st.image("assets/tokens/crystal_battery.jpg", width=200)
        st.info(f"將水晶移至今日圖騰：**{today_kin_info.get('圖騰')}**")

# --- Tab 6 ---
with tab6:
    st.header("🧠 441 Synchronotron")
    c_h, c_res = st.columns([1, 1])
    with c_h:
        st.markdown("#### 52 七價路徑")
        if moon_str == "Day Out of Time":
            st.success("✨ 無時間日：Hunab Ku 21 的核心通道")
        else:
            st.metric("年度路徑", f"Week {heptad_week}")
            st.info(f"當前位於年度第 {heptad_week} 條路徑，連接 Hunab Ku 21。")
    if sync_data:
        mcf = sync_data['MCF']
        bmu = sync_data['BMU']
        keq = sync_data['KIN_EQUIV']
        with c_res:
            st.markdown("#### 核心頻率數據")
            st.markdown(f"""
            <div style="background-color:#E8F8F5; padding:20px; border-radius:10px; border:2px solid #1ABC9C;">
                <h2>MCF: {mcf}</h2>
                <small>Master Coordinating Frequency</small>
                <hr>
                <h3>BMU: {bmu}</h3>
                <small>Base Matrix Unit</small>
                <hr>
                <h3>對等: KIN {keq['KIN']}</h3>
            </div>
            """, unsafe_allow_html=True)
        with st.expander("查看 TFI 加總細節"):
            for log in sync_data['logs']:
                st.code(log, language="text")
