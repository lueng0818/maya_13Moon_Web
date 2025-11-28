import sqlite3
import datetime
import math
import base64
import os
import pandas as pd

DB_PATH = "13moon.db"

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

# KIN 計算 (查表)
def calculate_kin_v2(date_obj):
    conn = get_db()
    try:
        yr = conn.execute(f"SELECT 起始KIN FROM Kin_Start WHERE 年份 = {date_obj.year}").fetchone()
        if not yr: return None, f"無 {date_obj.year} 年資料"
        
        mn = conn.execute(f"SELECT 累積天數 FROM Month_Accum WHERE 月份 = {date_obj.month}").fetchone()
        if not mn: return None, f"無 {date_obj.month} 月資料"
        
        kin = (yr['起始KIN'] + mn['累積天數'] + date_obj.day) % 260
        return (260 if kin == 0 else kin), None
    except Exception as e: return None, str(e)
    finally: conn.close()

def calculate_kin_math(date_obj):
    base = datetime.date(2023, 7, 26)
    delta = (date_obj - base).days
    kin = (1 + delta) % 260
    return 260 if kin == 0 else kin

# 資料獲取
def get_full_kin_data(kin):
    conn = get_db()
    data = {}
    try:
        row = conn.execute("SELECT * FROM Kin_Basic WHERE KIN = ?", (kin,)).fetchone()
        if row: data.update(dict(row))
        
        m = conn.execute("SELECT * FROM Matrix_Data WHERE 時間矩陣_KIN = ?", (kin,)).fetchone()
        if m:
            data['Matrix_Time'] = m.get('時間矩陣_矩陣位置')
            data['Matrix_Space'] = m.get('空間矩陣_矩陣位置')
            data['Matrix_Sync'] = m.get('共時矩陣_矩陣位置')
            data['Matrix_BMU'] = m.get('基本母體矩陣_BMU')
    except: pass

    s_num = (kin - 1) % 20 + 1
    t_num = (kin - 1) % 13 + 1
    data['seal_img'] = SEAL_FILES.get(s_num, "01紅龍.png")
    data['tone_img'] = TONE_FILES.get(t_num, "瑪雅曆法圖騰-34.png")
    if '調性' not in data: data['調性'] = TONE_NAMES[t_num]
    if '圖騰' not in data: data['圖騰'] = SEALS_NAMES[s_num]
    
    wid = math.ceil(kin / 13)
    data['wave_name'] = data.get('波符', '未知') 
    data['wave_img'] = f"瑪雅曆20波符-{str(wid).zfill(2)}.png"
    conn.close()
    return data

def get_main_sign_text(kin_num):
    conn = get_db()
    try:
        row = conn.execute("SELECT 主印記 FROM Kin_Basic WHERE KIN = ?", (kin_num,)).fetchone()
        if row: return row['主印記']
    except: pass
    finally: conn.close()
    return "查無印記名稱"

def get_oracle(kin):
    s = (kin - 1) % 20 + 1
    t = (kin - 1) % 13 + 1
    ana = 19 - s; ana += 20 if ana <= 0 else 0
    anti = (s + 10) % 20; anti = 20 if anti == 0 else anti
    occ_s = 21 - s
    occ_t = 14 - t
    guide = s
    return { "destiny": {"s":s, "t":t}, "analog": {"s":ana, "t":t}, "antipode": {"s":anti, "t":t}, "occult": {"s":occ_s, "t":occ_t}, "guide": {"s":guide, "t":t} }

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

def get_goddess_kin(kin):
    oracle = get_oracle(kin) 
    occult_s = oracle['occult']['s']
    occult_t = oracle['occult']['t']
    occult_kin = (occult_s + (occult_t - 1) * 20 - 1) % 260 + 1
    goddess_kin = (occult_kin + 130) % 260
    if goddess_kin == 0: goddess_kin = 260
    goddess_info = get_full_kin_data(goddess_kin)
    return {"KIN": goddess_kin, "Info": goddess_info, "Base_KIN": occult_kin}

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

# --- 曆法查詢 ---
def get_maya_calendar_info(date_obj):
    conn = get_db()
    result = {"Maya_Date": "-", "Maya_Month": "-", "Maya_Week": "-", "Heptad_Path": "-", "Plasma": "-", "Status": "查無資料"}
    try:
        q_date = date_obj.strftime('%Y-%m-%d')
        row = conn.execute("SELECT * FROM Calendar_Converter WHERE 國曆生日 = ?", (q_date,)).fetchone()
        if row:
            result['Maya_Date'] = row.get('瑪雅生日', '-')
            result['Maya_Month'] = row.get('瑪雅月', '-')
            result['Maya_Week'] = row.get('瑪雅週', '-')
            result['Heptad_Path'] = row.get('七價路徑', '-')
            result['Plasma'] = row.get('等離子日', '-')
            result['Status'] = "查詢成功"
    except: pass
    conn.close()
    return result

def get_week_key_sentence(week_name):
    conn = get_db()
    res = None
    try:
        row = conn.execute("SELECT 關鍵句 FROM Maya_Week_Key WHERE 瑪雅週 = ?", (week_name,)).fetchone()
        if row: res = row['關鍵句']
    except: pass
    conn.close()
    return res

def get_heptad_prayer(path_name):
    conn = get_db()
    res = None
    try:
        row = conn.execute("SELECT 祈禱文 FROM Heptad_Prayer WHERE 七價路徑 = ?", (path_name,)).fetchone()
        if row: res = row['祈禱文']
    except: pass
    conn.close()
    return res

# --- 用戶管理 (自動修復 Schema) ---
def ensure_users_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            姓名 TEXT NOT NULL,
            生日 TEXT NOT NULL,
            KIN INTEGER,
            主印記 TEXT
        )
    """)

def save_user_data(name, dob_str, kin, main_sign):
    conn = get_db()
    try:
        ensure_users_table(conn)
        exist = conn.execute("SELECT COUNT(*) FROM Users WHERE 姓名 = ?", (name,)).fetchone()[0]
        if exist == 0:
            conn.execute("INSERT INTO Users (姓名, 生日, KIN, 主印記) VALUES (?, ?, ?, ?)", (name, dob_str, kin, main_sign))
            conn.commit()
            return True, "建檔成功"
        else:
            return False, "此姓名已存在"
    except Exception as e:
        return False, f"存檔失敗: {e}"
    finally:
        conn.close()

def get_user_list():
    conn = get_db()
    try:
        ensure_users_table(conn)
        df = pd.read_sql("SELECT 姓名, 生日, KIN FROM Users", conn)
        return df
    except: return pd.DataFrame()
    finally: conn.close()

def get_user_kin(name, df_users):
    row = df_users[df_users['姓名'] == name]
    if not row.empty: return int(row.iloc[0]['KIN']), row.iloc[0]['生日']
    return None, None

def calculate_composite(kin_a, kin_b):
    total = kin_a + kin_b
    comp = total % 260
    return 260 if comp == 0 else comp
