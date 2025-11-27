import sqlite3
import datetime
import math
import base64
import os

DB_PATH = "13moon.db"

# --- 圖片檔名設定 (根據您上傳的檔案) ---
SEAL_FILES = {
    1: "01紅龍.jpg", 2: "02白風.jpg", 3: "03藍夜.jpg", 4: "04黃種子.jpg", 5: "05紅蛇.jpg",
    6: "06白世界橋.jpg", 7: "07藍手.jpg", 8: "08黃星星.jpg", 9: "09紅月.jpg", 10: "10白狗.jpg",
    11: "11藍猴.jpg", 12: "12黃人.jpg", 13: "13紅天行者.jpg", 14: "14白巫師.jpg", 15: "15藍鷹.jpg",
    16: "16黃戰士.jpg", 17: "17紅地球.jpg", 18: "18白鏡.jpg", 19: "19藍風暴.jpg", 20: "20黃太陽.jpg"
}

# 調性 1 (34) ~ 調性 13 (46)
TONE_FILES = { i: f"瑪雅曆法圖騰-{i+33}.png" for i in range(1, 14) }

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_img_b64(path):
    """將圖片轉 Base64 以便在 HTML 顯示"""
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

def calculate_kin(date_obj):
    """計算 KIN (基礎版)"""
    base_date = datetime.date(2023, 7, 26)
    base_kin = 1
    delta = (date_obj - base_date).days
    kin = (base_kin + delta) % 260
    return 260 if kin == 0 else kin

def get_full_kin_data(kin):
    """取得 KIN 的所有詳細資料 (含矩陣、易經)"""
    conn = get_db()
    data = {}
    
    # 1. 基礎資料
    try:
        row = conn.execute("SELECT * FROM Kin_Data WHERE KIN = ?", (kin,)).fetchone()
        if row: data.update(dict(row))
    except: pass

    # 2. 矩陣資料 (嘗試從 Matrix_Data 撈)
    try:
        # 搜尋邏輯：在 Matrix_Data 找 '時間矩陣_KIN' 等於 kin 的資料
        m_row = conn.execute("SELECT * FROM Matrix_Data WHERE 時間矩陣_KIN = ?", (kin,)).fetchone()
        if m_row:
            data['Matrix_Time'] = m_row.get('時間矩陣_矩陣位置', '-')
            data['Matrix_Space'] = m_row.get('空間矩陣_矩陣位置', '-')
            data['Matrix_Sync'] = m_row.get('共時矩陣_矩陣位置', '-')
            data['Matrix_BMU'] = m_row.get('基本母體矩陣_BMU', '-')
    except: 
        data['Matrix_Time'] = "N/A"

    # 3. 易經
    if '對應卦象' in data:
        try:
            gua = data['對應卦象']
            i_row = conn.execute("SELECT * FROM IChing WHERE 卦象 = ?", (gua,)).fetchone()
            if i_row:
                data['IChing_Meaning'] = i_row.get('意涵', '')
                data['IChing_Story'] = i_row.get('說明', '')
        except: pass

    # 4. 圖片與波符
    s_num = data.get('圖騰數字', 1)
    t_num = data.get('調性數字', 1)
    data['seal_img'] = SEAL_FILES.get(s_num, "01紅龍.jpg")
    data['tone_img'] = TONE_FILES.get(t_num, "瑪雅曆法圖騰-34.png")
    
    wave_id = math.ceil(kin / 13)
    data['wave_name'] = data.get('波符', '未知')
    # 波符圖片補零 (瑪雅曆20波符-08.png)
    data['wave_img'] = f"瑪雅曆20波符-{str(wave_id).zfill(2)}.png"

    conn.close()
    return data

def get_oracle(kin):
    """計算五大神諭 (簡單版)"""
    data = get_full_kin_data(kin)
    seal = int(data.get('圖騰數字', 1))
    tone = int(data.get('調性數字', 1))
    
    def fix_s(s): return 20 if s==0 else (s+20 if s<1 else (s-20 if s>20 else s))
    def fix_t(t): return 13 if t==0 else (t+13 if t<1 else (t-13 if t>13 else t))

    return {
        "destiny": {"s": seal, "t": tone},
        "analog":  {"s": fix_s(19-seal), "t": tone},
        "antipode":{"s": fix_s(seal+10), "t": tone},
        "occult":  {"s": fix_s(21-seal), "t": fix_t(14-tone)},
        "guide":   {"s": seal, "t": tone} # 暫用主印記
    }

def calculate_life_castle(birth_date):
    """計算 52 流年"""
    base_kin = calculate_kin(birth_date)
    path = []
    
    for age in range(105): # 算兩輪
        year = birth_date.year + age
        # 流年公式: KIN + 105 * age
        curr_kin = (base_kin + age * 105) % 260
        if curr_kin == 0: curr_kin = 260
        
        info = get_full_kin_data(curr_kin)
        
        # 城堡顏色
        cycle = age % 52
        if cycle < 13: col = "#fff0f0" # 紅
        elif cycle < 26: col = "#f8f8f8" # 白
        elif cycle < 39: col = "#f0f8ff" # 藍
        else: col = "#fffff0" # 黃
        
        path.append({
            "Age": age, "Year": year, "KIN": curr_kin,
            "Info": info, "Color": col
        })
    return path
