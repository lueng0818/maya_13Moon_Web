import sqlite3
import datetime
import math
import base64
import os

DB_PATH = "13moon.db"

# --- 圖片檔名對照 (根據您上傳的檔名) ---
SEALS_NAMES = ["","紅龍","白風","藍夜","黃種子","紅蛇","白世界橋","藍手","黃星星","紅月","白狗","藍猴","黃人","紅天行者","白巫師","藍鷹","黃戰士","紅地球","白鏡","藍風暴","黃太陽"]

# 產生檔名對照表: 1 -> "01紅龍.jpg"
SEAL_FILES = { i: f"{str(i).zfill(2)}{name}.jpg" for i, name in enumerate(SEALS_NAMES) if i > 0 }

# 調性檔名: 1 -> "瑪雅曆法圖騰-34.png"
TONE_FILES = { i: f"瑪雅曆法圖騰-{i+33}.png" for i in range(1, 14) }

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_img_b64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

def calculate_kin(date_obj):
    """日期轉 KIN"""
    base = datetime.date(2023, 7, 26)
    delta = (date_obj - base).days
    kin = (1 + delta) % 260
    return 260 if kin == 0 else kin

def get_full_kin_data(kin):
    """從資料庫撈取文字資料"""
    conn = get_db()
    data = {}
    
    # 1. 基礎資料
    try:
        row = conn.execute("SELECT * FROM Kin_Data WHERE KIN = ?", (kin,)).fetchone()
        if row: data.update(dict(row))
    except: pass

    # 2. 矩陣
    try:
        m = conn.execute("SELECT * FROM Matrix_Data WHERE 時間矩陣_KIN = ?", (kin,)).fetchone()
        if m:
            data['Matrix_Time'] = m.get('時間矩陣_矩陣位置')
            data['Matrix_Space'] = m.get('空間矩陣_矩陣位置')
            data['Matrix_Sync'] = m.get('共時矩陣_矩陣位置')
            data['Matrix_BMU'] = m.get('基本母體矩陣_BMU')
    except: pass

    # 3. 圖片路徑
    s_num = data.get('圖騰數字', 1)
    t_num = data.get('調性數字', 1)
    data['seal_img'] = SEAL_FILES.get(s_num, "01紅龍.jpg")
    data['tone_img'] = TONE_FILES.get(t_num, "瑪雅曆法圖騰-34.png")
    
    # 波符
    wid = math.ceil(kin / 13)
    data['wave_name'] = data.get('波符', '未知')
    data['wave_img'] = f"瑪雅曆20波符-{str(wid).zfill(2)}.png"

    conn.close()
    return data

def get_oracle(kin):
    """
    數學計算五大神諭 (解決日期沒對應到的問題)
    回傳: 各位置的 (圖騰ID, 調性ID)
    """
    # 1. 主印記
    seal = kin % 20; seal = 20 if seal==0 else seal
    tone = kin % 13; tone = 13 if tone==0 else tone
    
    # 2. 支持 (19-seal)
    analog = 19 - seal
    if analog <= 0: analog += 20
    
    # 3. 擴展 (seal+10)
    antipode = (seal + 10) % 20
    if antipode == 0: antipode = 20
    
    # 4. 推動 (21-seal, 14-tone)
    occult_s = 21 - seal
    occult_t = 14 - tone
    
    # 5. 引導 (簡易版：同主印記)
    guide = seal 

    return {
        "destiny": {"s": seal, "t": tone},
        "analog":  {"s": analog, "t": tone},
        "antipode":{"s": antipode, "t": tone},
        "occult":  {"s": occult_s, "t": occult_t},
        "guide":   {"s": guide, "t": tone}
    }

def calculate_life_castle(birth_date):
    """52 流年計算"""
    base_kin = calculate_kin(birth_date)
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
