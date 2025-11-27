import sqlite3
import datetime
import math
import base64
import os
import pandas as pd # 需要 pandas 讀取 SQL

DB_PATH = "13moon.db"

# 圖片與名稱設定
SEALS_NAMES = ["","紅龍","白風","藍夜","黃種子","紅蛇","白世界橋","藍手","黃星星","紅月","白狗","藍猴","黃人","紅天行者","白巫師","藍鷹","黃戰士","紅地球","白鏡","藍風暴","黃太陽"]
SEAL_FILES = { i: f"{str(i).zfill(2)}{name}.png" for i, name in enumerate(SEALS_NAMES) if i > 0 }
TONE_FILES = { i: f"瑪雅曆法圖騰-{i+33}.png" for i in range(1, 14) }
TONE_NAMES = ["","磁性","月亮","電力","自我存在","超頻","韻律","共振","銀河星系","太陽","行星","光譜","水晶","宇宙"]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_img_b64(path):
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return ""

# 【核心更新】新的 KIN 計算邏輯 (查表法)
def calculate_kin_v2(date_obj):
    """
    使用 Kin_Start 和 Month_Accum 資料表進行計算
    """
    conn = get_db()
    try:
        # 1. 讀取年份起始 KIN
        query_year = f"SELECT 起始KIN FROM Kin_Start WHERE 年份 = {date_obj.year}"
        df_year = pd.read_sql(query_year, conn)
        
        # 2. 讀取月份累積天數
        query_month = f"SELECT 累積天數 FROM Month_Accum WHERE 月份 = {date_obj.month}"
        df_month = pd.read_sql(query_month, conn)
        
        if df_year.empty: return None, "資料庫無此年份資料"
        if df_month.empty: return None, "資料庫無此月份資料"
        
        start_kin = df_year.iloc[0,0]
        month_accum = df_month.iloc[0,0]
        
        # 3. 計算公式
        raw = start_kin + month_accum + date_obj.day
        kin = raw % 260
        if kin == 0: kin = 260
        
        return kin, None
        
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()

# 舊的數學計算法 (作為備用)
def calculate_kin_math(date_obj):
    base = datetime.date(2023, 7, 26)
    delta = (date_obj - base).days
    kin = (1 + delta) % 260
    return 260 if kin == 0 else kin

def get_full_kin_data(kin):
    conn = get_db()
    data = {}
    
    # 優先讀取 Kin_Data (資料最全)
    try:
        row = conn.execute("SELECT * FROM Kin_Data WHERE KIN = ?", (kin,)).fetchone()
        if row: data.update(dict(row))
    except: pass
    
    # 矩陣資料
    try:
        m = conn.execute("SELECT * FROM Matrix_Data WHERE 時間矩陣_KIN = ?", (kin,)).fetchone()
        if m:
            data['Matrix_Time'] = m.get('時間矩陣_矩陣位置')
            data['Matrix_Space'] = m.get('空間矩陣_矩陣位置')
            data['Matrix_Sync'] = m.get('共時矩陣_矩陣位置')
            data['Matrix_BMU'] = m.get('基本母體矩陣_BMU')
    except: pass

    # 圖片與波符
    s_num = int(data.get('圖騰數字', (kin-1)%20 + 1))
    t_num = int(data.get('調性數字', (kin-1)%13 + 1))
    
    data['seal_img'] = SEAL_FILES.get(s_num, "01紅龍.png")
    data['tone_img'] = TONE_FILES.get(t_num, "瑪雅曆法圖騰-34.png")
    data['調性'] = data.get('調性', TONE_NAMES[t_num])
    data['圖騰'] = data.get('圖騰', SEALS_NAMES[s_num])
    
    wid = math.ceil(kin / 13)
    data['wave_name'] = data.get('波符', '未知')
    data['wave_img'] = f"瑪雅曆20波符-{str(wid).zfill(2)}.png"

    conn.close()
    return data

def get_oracle(kin):
    # 這裡的邏輯不變，省略以節省篇幅
    seal = (kin - 1) % 20 + 1
    tone = (kin - 1) % 13 + 1
    
    analog = 19 - seal
    if analog <= 0: analog += 20
    antipode = (seal + 10) % 20
    if antipode == 0: antipode = 20
    occult_s = 21 - seal
    occult_t = 14 - tone
    guide = seal 

    return {
        "destiny": {"s": seal, "t": tone},
        "analog":  {"s": analog, "t": tone},
        "antipode":{"s": antipode, "t": tone},
        "occult":  {"s": occult_s, "t": occult_t},
        "guide":   {"s": guide, "t": tone}
    }

def calculate_life_castle(birth_date):
    # 使用新版計算邏輯
    base_kin, err = calculate_kin_v2(birth_date)
    if not base_kin: base_kin = calculate_kin_math(birth_date) # 降級備案
    
    path = []
    for age in range(105):
        year = birth_date.year + age
        curr_kin = (base_kin + age * 105) % 260
        if curr_kin == 0: curr_kin = 260
        
        info = get_full_kin_data(curr_kin)
        
        cycle = age % 52
        if cycle < 13: col = "#fff0f0"
        elif cycle < 26: col = "#f8f8f8"
        elif cycle < 39: col = "#f0f8ff"
        else: col = "#fffff0"
        
        path.append({"Age":age, "Year":year, "KIN":curr_kin, "Info":info, "Color":col})
    return path
