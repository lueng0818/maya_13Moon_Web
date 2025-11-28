import sqlite3
import datetime
import math
import base64
import os
import pandas as pd

DB_PATH = "13moon.db"

# --- 1. 靜態資源設定 ---
SEALS_NAMES = ["","紅龍","白風","藍夜","黃種子","紅蛇","白世界橋","藍手","黃星星","紅月","白狗","藍猴","黃人","紅天行者","白巫師","藍鷹","黃戰士","紅地球","白鏡","藍風暴","黃太陽"]

# 圖片檔名對照 (修正為 .png)
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

def get_year_range():
    """獲取資料庫中的年份範圍，用於日期選擇器"""
    default_min, default_max = 1900, 2100
    try:
        conn = get_db()
        res = conn.execute("SELECT MIN(年份), MAX(年份) FROM Kin_Start").fetchone()
        if res and res[0]:
            return int(res[0]), int(res[1])
    except: pass
    finally:
        try: conn.close()
        except: pass
    return default_min, default_max

# --- 3. KIN 計算邏輯 (查表法) ---
def calculate_kin_v2(date_obj):
    """邏輯：(年起始 KIN + 月累積天數 + 日期) % 260"""
    conn = get_db()
    try:
        res_year = conn.execute(f"SELECT 起始KIN FROM Kin_Start WHERE 年份 = {date_obj.year}").fetchone()
        if not res_year: return None, f"無 {date_obj.year} 年起始KIN資料"
        start_kin = res_year['起始KIN']
        
        res_month = conn.execute(f"SELECT 累積天數 FROM Month_Accum WHERE 月份 = {date_obj.month}").fetchone()
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
    """數學備案"""
    base = datetime.date(2023, 7, 26)
    delta = (date_obj - base).days
    kin = (1 + delta) % 260
    return 260 if kin == 0 else kin

# --- 4. 資料獲取核心 (整合) ---
def get_base_matrix_data(kin_num):
    """查詢基礎矩陣資訊"""
    conn = get_db()
    result = {}
    try:
        row = conn.execute("SELECT * FROM Base_Matrix_441 WHERE KIN = ?", (kin_num,)).fetchone()
        if row:
            result = {
                "BMU_Position": row.get('矩陣位置', '-'),
                "BMU_Note": row.get('八度音符', '-'),
                "BMU_Brain": row.get('對應腦部', '-')
            }
    except: pass
    finally: conn.close()
    return result

def get_full_kin_data(kin):
    conn = get_db()
    data = {}
    
    # 1. Kin_Basic (基礎資訊)
    try:
        row = conn.execute("SELECT * FROM Kin_Basic WHERE KIN = ?", (kin,)).fetchone()
        if row: data.update(dict(row))
    except: pass
    
    # 2. Kin_Data (進階星際資訊)
    try:
        row_data = conn.execute("SELECT * FROM Kin_Data WHERE KIN = ?", (kin,)).fetchone()
        if row_data:
            for k, v in dict(row_data).items():
                if k not in data or k in ['諧波', '密碼子', '星際原型', 'BMU', '行星', '流', '電路', '說明', '家族', '對應脈輪', '電路說明']:
                    data[k] = v
    except: pass
    
    # 3. Matrix_Data (矩陣座標)
    try:
        m = conn.execute("SELECT * FROM Matrix_Data WHERE 時間矩陣_KIN = ?", (kin,)).fetchone()
        if m:
            data['Matrix_Time'] = m.get('時間矩陣_矩陣位置')
            data['Matrix_Space'] = m.get('空間矩陣_矩陣位置')
            data['Matrix_Sync'] = m.get('共時矩陣_矩陣位置')
            data['Matrix_BMU'] = m.get('基本母體矩陣_BMU')
    except: pass
    
    conn.close()

    # 4. 補充 Base Matrix
    bmu_data = get_base_matrix_data(kin)
    data.update(bmu_data)

    # 5. 圖片與名稱
    s_num = int(data.get('圖騰數字', (kin - 1) % 20 + 1))
    t_num = int(data.get('調性數字', (kin - 1) % 13 + 1))
    
    data['seal_img'] = SEAL_FILES.get(s_num, "01紅龍.png")
    data['tone_img'] = TONE_FILES.get(t_num, "瑪雅曆法圖騰-34.png")
    
    if '調性' not in data: data['調性'] = TONE_NAMES[t_num]
    if '圖騰' not in data: data['圖騰'] = SEALS_NAMES[s_num]
    
    wid = math.ceil(kin / 13)
    # 優先使用 Kin_Basic 裡的波符，若無則標記未知
    data['wave_name'] = data.get('波符', '未知')
    data['wave_img'] = f"瑪雅曆20波符-{str(wid).zfill(2)}.png"

    return data

def get_main_sign_text(kin_num):
    """查詢主印記文字"""
    conn = get_db()
    try:
        row = conn.execute("SELECT 主印記 FROM Kin_Basic WHERE KIN = ?", (kin_num,)).fetchone()
        if row: return row['主印記']
    except: pass
    finally: conn.close()
    return "查無印記名稱"

# --- 5. 高階印記計算 (PSI, 女神) ---
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
    finally: conn.close()
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

# --- 6. 五大神諭 ---
def get_oracle(kin):
    s = (kin - 1) % 20 + 1
    t = (kin - 1) % 13 + 1
    
    ana = 19 - s; ana += 20 if ana <= 0 else 0
    anti = (s + 10) % 20; anti = 20 if anti == 0 else anti
    occ_s = 21 - s
    occ_t = 14 - t
    guide = s
    
    return {
        "destiny": {"s":s, "t":t}, "analog": {"s":ana, "t":t}, "antipode": {"s":anti, "t":t},
        "occult": {"s":occ_s, "t":occ_t}, "guide": {"s":guide, "t":t}
    }

# --- 7. 瑪雅曆法與調頻 ---
def get_maya_calendar_info(date_obj):
    conn = get_db()
    result = {"Maya_Date": "-", "Maya_Month": "-", "Maya_Week": "-", "Heptad_Path": "-", "Plasma": "-", "Solar_Year": "-", "Status": "查無資料"}
    try:
        q_date = date_obj.strftime('%Y-%m-%d')
        row = conn.execute("SELECT * FROM Calendar_Converter WHERE 國曆生日 = ?", (q_date,)).fetchone()
        if row:
            result.update({
                'Maya_Date': row.get('瑪雅生日', '-'),
                'Maya_Month': row.get('瑪雅月', '-'),
                'Maya_Week': row.get('瑪雅週', '-'),
                'Heptad_Path': row.get('七價路徑', '-'),
                'Plasma': row.get('等離子日', '-'),
                'Status': "查詢成功"
            })
            # 簡易星際年推算
            y = date_obj.year - 1 if (date_obj.month<7 or (date_obj.month==7 and date_obj.day<26)) else date_obj.year
            result['Solar_Year'] = f"NS 1.{y-1987+30}"
    except Exception as e: result['Status'] = f"Error: {e}"
    finally: conn.close()
    return result

def get_week_key_sentence(week_name):
    conn = get_db()
    res = None
    try:
        row = conn.execute("SELECT 關鍵句 FROM Maya_Week_Key WHERE 瑪雅週 = ?", (week_name,)).fetchone()
        if row: res = row['關鍵句']
    except: pass
    finally: conn.close()
    return res

def get_heptad_prayer(path_name):
    conn = get_db()
    res = None
    try:
        row = conn.execute("SELECT 祈禱文 FROM Heptad_Prayer WHERE 七價路徑 = ?", (path_name,)).fetchone()
        if row: res = row['祈禱文']
    except: pass
    finally: conn.close()
    return res

def get_octave_positions(note):
    conn = get_db()
    results = []
    try:
        rows = conn.execute("SELECT 矩陣位置, 行, 列 FROM Octave_Scale WHERE 八度音符 = ?", (note,)).fetchall()
        for r in rows:
            results.append({"Position": r['矩陣位置'], "Row": r['行'], "Col": r['列']})
    except: pass
    finally: conn.close()
    return results

# --- 8. 流年與用戶管理 ---
def calculate_life_castle(birth_date):
    bk, _ = calculate_kin_v2(birth_date)
    if not bk: bk = calculate_kin_math(birth_date)
    path = []
    for age in range(105):
        ck = (bk + age*105)%260
        if ck==0: ck=260
        info = get_full_kin_data(ck)
        c = age%52
        col = "#fff0f0" if c<13 else ("#f8f8f8" if c<26 else ("#f0f8ff" if c<39 else "#fffff0"))
        path.append({"Age":age, "Year":birth_date.year+age, "KIN":ck, "Info":info, "Color":col})
    return path

def ensure_users_table(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS Users (id INTEGER PRIMARY KEY AUTOINCREMENT, 姓名 TEXT NOT NULL, 生日 TEXT NOT NULL, KIN INTEGER, 主印記 TEXT)""")

def save_user_data(name, dob_str, kin, main_sign):
    conn = get_db()
    try:
        ensure_users_table(conn)
        if conn.execute("SELECT COUNT(*) FROM Users WHERE 姓名 = ?", (name,)).fetchone()[0] == 0:
            conn.execute("INSERT INTO Users (姓名, 生日, KIN, 主印記) VALUES (?, ?, ?, ?)", (name, dob_str, kin, main_sign))
            conn.commit()
            return True, "建檔成功"
        return False, "姓名已存在"
    except Exception as e: return False, str(e)
    finally: conn.close()

def get_user_list():
    conn = get_db()
    try:
        ensure_users_table(conn)
        return pd.read_sql("SELECT 姓名, 生日, KIN FROM Users", conn)
    except: return pd.DataFrame()
    finally: conn.close()

def get_user_kin(name, df_users):
    r = df_users[df_users['姓名'] == name]
    if not r.empty: return int(r.iloc[0]['KIN']), r.iloc[0]['生日']
    return None, None

def calculate_composite(k1, k2):
    res = (k1 + k2) % 260
    return 260 if res == 0 else res
