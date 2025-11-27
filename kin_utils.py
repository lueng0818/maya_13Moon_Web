import sqlite3
import datetime
import math
import base64
import os
import pandas as pd

DB_PATH = "13moon.db"

# --- 1. 靜態資源設定 (確保與您的 assets 資料夾和 Kin_Basic 表格一致) ---
SEALS_NAMES = ["","紅龍","白風","藍夜","黃種子","紅蛇","白世界橋","藍手","黃星星","紅月","白狗","藍猴","黃人","紅天行者","白巫師","藍鷹","黃戰士","紅地球","白鏡","藍風暴","黃太陽"]
SEAL_FILES = { i: f"{str(i).zfill(2)}{name}.png" for i, name in enumerate(SEALS_NAMES) if i > 0 }
TONE_FILES = { i: f"瑪雅曆法圖騰-{i+33}.png" for i in range(1, 14) }
TONE_NAMES = ["","磁性","月亮","電力","自我存在","超頻","韻律","共振","銀河星系","太陽","行星","光譜","水晶","宇宙"]

# --- 2. 輔助函數 ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_img_b64(path):
    """將圖片轉為 Base64 字串"""
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return ""

# --- 3. KIN 計算邏輯 (查表法) ---
def calculate_kin_v2(date_obj):
    """
    邏輯：(年起始 KIN + 月累積天數 + 日期) % 260
    """
    conn = get_db()
    try:
        # 1. 查年份 (Kin_Start)
        res_year = conn.execute(f"SELECT 起始KIN FROM Kin_Start WHERE 年份 = {date_obj.year}").fetchone()
        if not res_year: return None, f"無 {date_obj.year} 年起始KIN資料"
        start_kin = res_year['起始KIN']
        
        # 2. 查月份 (Month_Accum)
        res_month = conn.execute(f"SELECT 累積天數 FROM Month_Accum WHERE 月份 = {date_obj.month}").fetchone()
        if not res_month: return None, f"無 {date_obj.month} 月累積天數資料"
        month_accum = res_month['累積天數']
        
        # 3. 計算公式: (年起始 + 月累積 + 日) % 260
        total = start_kin + month_accum + date_obj.day
        kin = total % 260
        return (260 if kin == 0 else kin), None
        
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()

# 數學備案 (萬一查不到表時使用)
def calculate_kin_math(date_obj):
    base = datetime.date(2023, 7, 26)
    delta = (date_obj - base).days
    kin = (1 + delta) % 260
    return 260 if kin == 0 else kin

# --- 4. 資料獲取核心 (優先從 Kin_Basic 撈取文字) ---
def get_full_kin_data(kin):
    conn = get_db()
    data = {}
    
    # 1. 從 Kin_Basic 讀取基礎資料
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

    # 3. 補充圖片路徑與名稱 ID
    s_num = (kin - 1) % 20 + 1
    t_num = (kin - 1) % 13 + 1
    
    data['seal_img'] = SEAL_FILES.get(s_num, "01紅龍.png")
    data['tone_img'] = TONE_FILES.get(t_num, "瑪雅曆法圖騰-34.png")
    
    # 補充中文名稱
    if '調性' not in data: data['調性'] = TONE_NAMES[t_num]
    if '圖騰' not in data: data['圖騰'] = SEALS_NAMES[s_num]
    
    wid = math.ceil(kin / 13)
    data['wave_name'] = data.get('波符', '未知')
    data['wave_img'] = f"瑪雅曆20波符-{str(wid).zfill(2)}.png"

    conn.close()
    return data

# --- 5. PSI 與 女神計算 ---
def get_psi_kin(date_obj):
    """查詢 PSI 印記 (查表)"""
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

def get_goddess_kin(kin):
    """計算女神印記 (Occult Kin + 130)"""
    oracle = get_oracle(kin) 
    occult_s = oracle['occult']['s']
    occult_t = oracle['occult']['t']
    occult_kin = (occult_s + (occult_t - 1) * 20 - 1) % 260 + 1 # 算出隱藏印記 KIN
    
    goddess_kin = (occult_kin + 130) % 260
    if goddess_kin == 0: goddess_kin = 260
    
    goddess_info = get_full_kin_data(goddess_kin)
    
    return {
        "KIN": goddess_kin,
        "Info": goddess_info,
        "Base_KIN": occult_kin
    }

# --- 6. 五大神諭計算 ---
def get_oracle(kin):
    """計算五大神諭的 (圖騰ID, 調性ID)"""
    s = (kin - 1) % 20 + 1
    t = (kin - 1) % 13 + 1
    
    ana = 19 - s; ana += 20 if ana <= 0 else 0
    anti = (s + 10) % 20; anti = 20 if anti == 0 else anti
    occ_s = 21 - s
    occ_t = 14 - t
    guide = s
    
    return {
        "destiny": {"s":s, "t":t},
        "analog": {"s":ana, "t":t},
        "antipode": {"s":anti, "t":t},
        "occult": {"s":occ_s, "t":occ_t},
        "guide": {"s":guide, "t":t}
    }

# --- 7. 52 流年計算 ---
def calculate_life_castle(birth_date):
    """計算 52 流年路徑"""
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
