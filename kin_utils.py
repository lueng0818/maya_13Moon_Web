import sqlite3
import datetime
import math
import base64
import os
import pandas as pd

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

def calculate_kin_v2(date_obj):
    """查表計算 KIN"""
    conn = get_db()
    try:
        q_year = f"SELECT 起始KIN FROM Kin_Start WHERE 年份 = {date_obj.year}"
        res_year = conn.execute(q_year).fetchone()
        if not res_year: return None, f"無 {date_obj.year} 年起始KIN資料"
        start_kin = res_year['起始KIN']
        
        q_month = f"SELECT 累積天數 FROM Month_Accum WHERE 月份 = {date_obj.month}"
        res_month = conn.execute(q_month).fetchone()
        if not res_month: return None, f"無 {date_obj.month} 月累積天數資料"
        month_accum = res_month['累積天數']
        
        total = start_kin + month_accum + date_obj.day
        kin = total % 260
        return (260 if kin == 0 else kin), None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()

def calculate_kin_math(date_obj):
    base = datetime.date(2023, 7, 26)
    delta = (date_obj - base).days
    kin = (1 + delta) % 260
    return 260 if kin == 0 else kin

def get_full_kin_data(kin):
    conn = get_db()
    data = {}
    
    # 1. 【核心】從 Kin_Basic 撈取波符 (E 欄位) 和城堡等資訊
    try:
        row = conn.execute("SELECT * FROM Kin_Basic WHERE KIN = ?", (kin,)).fetchone()
        if row: data.update(dict(row))
    except: pass
    
    # 2. 補充矩陣資料
    try:
        m = conn.execute("SELECT * FROM Matrix_Data WHERE 時間矩陣_KIN = ?", (kin,)).fetchone()
        if m:
            data['Matrix_Time'] = m.get('時間矩陣_矩陣位置')
            data['Matrix_Space'] = m.get('空間矩陣_矩陣位置')
            data['Matrix_Sync'] = m.get('共時矩陣_矩陣位置')
            data['Matrix_BMU'] = m.get('基本母體矩陣_BMU')
    except: pass

    # 3. 圖片與名稱 (用數學推算 ID)
    s_num = (kin - 1) % 20 + 1
    t_num = (kin - 1) % 13 + 1
    
    data['seal_img'] = SEAL_FILES.get(s_num, "01紅龍.png")
    data['tone_img'] = TONE_FILES.get(t_num, "瑪雅曆法圖騰-34.png")
    
    # 【關鍵】確保波符名稱使用 Kin_Basic 中的欄位 (波符 / 城堡)
    data['波符'] = data.get('波符', '未知') # Column E
    data['城堡'] = data.get('城堡', '未知')
    
    if '調性' not in data: data['調性'] = TONE_NAMES[t_num]
    if '圖騰' not in data: data['圖騰'] = SEALS_NAMES[s_num]
    
    wid = math.ceil(kin / 13)
    data['wave_name'] = data.get('波符', '未知') # 這裡使用 data['波符'] 裡的內容
    data['wave_img'] = f"瑪雅曆20波符-{str(wid).zfill(2)}.png"

    conn.close()
    return data

def get_psi_kin(date_obj):
    conn = get_db()
    psi_data = {}
    try:
        q_date = f"{date_obj.month}月{date_obj.day}日"
        row = conn.execute("SELECT * FROM PSI_Bank WHERE 月日 = ?", (q_date,)).fetchone()
        if row:
            p_kin = int(row['PSI印記'])
            p_info = get_full_kin_data(p_kin)
            psi_data = {"KIN": p_kin, "Info": p_info, "Matrix": row.get('矩陣位置','-')}
    except: pass
    conn.close()
    return psi_data

def get_oracle(kin):
    s = (kin - 1) % 20 + 1
    t = (kin - 1) % 13 + 1
    
    ana = 19 - s; ana += 20 if ana <= 0 else 0
    antipode = (s + 10) % 20; antipode = 20 if antipode == 0 else antipode
    occult_s = 21 - s
    occult_t = 14 - t
    guide = s
    
    return {
        "destiny": {"s":s, "t":t},
        "analog": {"s":ana, "t":t},
        "antipode": {"s":antipode, "t":t},
        "occult": {"s":occult_s, "t":occult_t},
        "guide": {"s":guide, "t":t}
    }

def calculate_life_castle(birth_date):
    bk, _ = calculate_kin_v2(birth_date)
    if not bk: bk = calculate_kin_math(birth_date)
    path = []
    for age in range(105):
        ck = (bk + age*105)%260
        if ck==0: ck=260
        info = get_full_kin_data(ck)
        c_age = age%52
        col = "#fff0f0" if c_age<13 else ("#f8f8f8" if c_age<26 else ("#f0f8ff" if c_age<39 else "#fffff0"))
        path.append({"Age":age, "Year":birth_date.year+age, "KIN":ck, "Info":info, "Color":col})
    return path
