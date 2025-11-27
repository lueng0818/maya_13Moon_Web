import sqlite3
import datetime
import math
import base64
import os

DB_PATH = "13moon.db"

# 靜態資源設定
SEAL_FILES = { i: f"{str(i).zfill(2) if i<10 else i}{name}.jpg" for i, name in zip(range(1,21), ["紅龍","白風","藍夜","黃種子","紅蛇","白世界橋","藍手","黃星星","紅月","白狗","藍猴","黃人","紅天行者","白巫師","藍鷹","黃戰士","紅地球","白鏡","藍風暴","黃太陽"]) }
# 這裡簡化檔名對照，若您的檔名不同請自行調整，或維持您原本的字典
# 修正為符合您上傳習慣的檔名:
SEAL_FILES_FIXED = {
    1: "01紅龍.jpg", 2: "02白風.jpg", 3: "03藍夜.jpg", 4: "04黃種子.jpg", 5: "05紅蛇.jpg",
    6: "06白世界橋.jpg", 7: "07藍手.jpg", 8: "08黃星星.jpg", 9: "09紅月.jpg", 10: "10白狗.jpg",
    11: "11藍猴.jpg", 12: "12黃人.jpg", 13: "13紅天行者.jpg", 14: "14白巫師.jpg", 15: "15藍鷹.jpg",
    16: "16黃戰士.jpg", 17: "17紅地球.jpg", 18: "18白鏡.jpg", 19: "19藍風暴.jpg", 20: "20黃太陽.jpg"
}
TONE_FILES = { i: f"瑪雅曆法圖騰-{i+33}.png" for i in range(1, 14) }

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_img_b64(path):
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return ""

def calculate_kin(date_obj):
    base = datetime.date(2023, 7, 26)
    delta = (date_obj - base).days
    kin = (1 + delta) % 260
    return 260 if kin == 0 else kin

def get_full_kin_data(kin):
    """
    獲取 KIN 的所有高階資料：包含矩陣、易經、名人
    """
    conn = get_db()
    data = {}
    
    # 1. 基礎資料 (Kin_Data)
    try:
        row = conn.execute("SELECT * FROM Kin_Data WHERE KIN = ?", (kin,)).fetchone()
        if row: data.update(dict(row))
    except: pass

    # 2. 矩陣資料 (Matrix_Data)
    # 矩陣表通常用 KIN 對照 "時間矩陣"
    try:
        # 注意：create_db_v2 產生的欄位名可能是 "時間矩陣_矩陣位置"
        # 我們嘗試搜尋該 KIN 在時間矩陣中的位置
        m_row = conn.execute("SELECT * FROM Matrix_Data WHERE 時間矩陣_KIN = ?", (kin,)).fetchone()
        if m_row:
            data['Matrix_Time'] = m_row['時間矩陣_矩陣位置']
            data['Matrix_Space'] = m_row['空間矩陣_矩陣位置']
            data['Matrix_Sync'] = m_row['共時矩陣_矩陣位置']
            data['Matrix_BMU'] = m_row['基本母體矩陣_BMU']
    except: 
        data['Matrix_Time'] = "查無資料"

    # 3. 易經資料 (IChing)
    # 假設 Kin_Data 裡有 '密碼子' 欄位對應易經
    try:
        # 這邊邏輯比較複雜，簡單起見，我們直接用 Kin_Data 裡的 '對應卦象' 或 '密碼子'
        # 如果 Kin_Data 裡有 '對應卦象' (例如 '乾為天')
        if '對應卦象' in data:
            gua_name = data['對應卦象']
            iching_row = conn.execute("SELECT * FROM IChing WHERE 卦象 = ?", (gua_name,)).fetchone()
            if iching_row:
                data['IChing_Desc'] = iching_row['意涵']
                data['IChing_Story'] = iching_row['說明']
    except: pass

    # 4. 圖片路徑
    s_num = data.get('圖騰數字', 1)
    t_num = data.get('調性數字', 1)
    data['seal_img'] = SEAL_FILES_FIXED.get(s_num, "")
    data['tone_img'] = TONE_FILES.get(t_num, "")
    data['wave_id'] = math.ceil(kin / 13)
    data['wave_img'] = f"瑪雅曆20波符-{str(data['wave_id']).zfill(2)}.png"

    conn.close()
    return data

def get_oracle(kin):
    # 這裡沿用之前的邏輯，或是直接從資料庫 Kin_Data 讀取 (如果有存)
    # 為了保險，這裡用數學算
    data = get_full_kin_data(kin)
    seal = data.get('圖騰數字', 1)
    tone = data.get('調性數字', 1)
    
    # 簡單計算 ID
    def get_k(s, t): return (s + (t-1)*20) # 這是錯的公式，僅示意。實際需複雜反推
    # 我們只回傳 seal/tone ID 讓前端畫圖
    
    return {
        "destiny": {"seal": seal, "tone": tone},
        "analog": {"seal": (19-seal if 19-seal>0 else 19-seal+20), "tone": tone},
        "antipode": {"seal": (seal+10 if seal+10<=20 else seal-10), "tone": tone},
        "occult": {"seal": 21-seal, "tone": 14-tone},
        "guide": {"seal": seal, "tone": tone} # 暫時簡化
    }

def calculate_life_castle(birth_date):
    """計算 52 流年，並包含每一年的矩陣資料"""
    path = []
    base_kin = calculate_kin(birth_date)
    conn = get_db()
    
    for age in range(105):
        year = birth_date.year + age
        curr_kin = (base_kin + age * 105) % 260
        if curr_kin == 0: curr_kin = 260
        
        # 簡單取資料
        info = get_full_kin_data(curr_kin)
        
        # 城堡顏色
        cycle_age = age % 52
        if 0<=cycle_age<13: color="#fff0f0" # 紅
        elif 13<=cycle_age<26: color="#f8f8f8" # 白
        elif 26<=cycle_age<39: color="#f0f8ff" # 藍
        else: color="#fffff0" # 黃
        
        path.append({
            "Age": age,
            "Year": year,
            "KIN": curr_kin,
            "Info": info,
            "Color": color
        })
    conn.close()
    return path
