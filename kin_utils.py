import sqlite3
import datetime
import math
import base64
import os
import pandas as pd

DB_PATH = "13moon.db"

# 靜態資源設定
SEALS_NAMES = ["","紅龍","白風","藍夜","黃種子","紅蛇","白世界橋","藍手","黃星星","紅月","白狗","藍猴","黃人","紅天行者","白巫師","藍鷹","黃戰士","紅地球","白鏡","藍風暴","黃太陽"]
SEAL_FILES = { i: f"{str(i).zfill(2)}{name}.png" for i, name in enumerate(SEALS_NAMES) if i > 0 }
TONE_FILES = { i: f"瑪雅曆法圖騰-{i+33}.png" for i in range(1, 14) }
TONE_NAMES = ["","磁性","月亮","電力","自我存在","超頻","韻律","共振","銀河星系","太陽","行星","光譜","水晶","宇宙"]

TONE_QUESTIONS = {
    1: "我的目的是什麼？", 2: "我的挑戰是什麼？", 3: "我如何提供最好的服務？",
    4: "我採取什麼形式？", 5: "我如何被授權？", 6: "我如何組織平等？",
    7: "我如何歸於中心？", 8: "我是否活出所信？", 9: "我如何完成目的？",
    10: "我如何完美顯化？", 11: "我如何釋放與放下？", 12: "我如何奉獻自己？",
    13: "我如何活在當下？"
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_img_b64(path):
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return ""

def get_year_range():
    try:
        conn = get_db()
        res = conn.execute("SELECT MIN(年份), MAX(年份) FROM Kin_Start").fetchone()
        conn.close()
        if res and res[0]: return int(res[0]), int(res[1])
    except: pass
    return 1900, 2100

# --- KIN 計算 ---
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

# --- 資料獲取 ---
def get_base_matrix_data(kin_num):
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
    try:
        # Kin_Basic
        row = conn.execute("SELECT * FROM Kin_Basic WHERE KIN = ?", (kin,)).fetchone()
        if row: data.update(dict(row))
        
        # Kin_Data (補充資料)
        row_data = conn.execute("SELECT * FROM Kin_Data WHERE KIN = ?", (kin,)).fetchone()
        if row_data:
            for k, v in dict(row_data).items():
                if k not in data or k in ['諧波', '密碼子', '星際原型', 'BMU', '行星', '流', '電路', '說明', '家族', '對應脈輪']:
                    data[k] = v

        # Matrix_Data
        m = conn.execute("SELECT * FROM Matrix_Data WHERE 時間矩陣_KIN = ?", (kin,)).fetchone()
        if m:
            data['Matrix_Time'] = m.get('時間矩陣_矩陣位置')
            data['Matrix_Space'] = m.get('空間矩陣_矩陣位置')
            data['Matrix_Sync'] = m.get('共時矩陣_矩陣位置')
            data['Matrix_BMU'] = m.get('基本母體矩陣_BMU')
    except: pass
    
    conn.close()
    
    bmu_data = get_base_matrix_data(kin)
    data.update(bmu_data)

    s_num = int(data.get('圖騰數字', (kin-1)%20+1))
    t_num = int(data.get('調性數字', (kin-1)%13+1))
    data['seal_img'] = SEAL_FILES.get(s_num, "01紅龍.png")
    data['tone_img'] = TONE_FILES.get(t_num, "瑪雅曆法圖騰-34.png")
    if '調性' not in data: data['調性'] = TONE_NAMES[t_num]
    if '圖騰' not in data: data['圖騰'] = SEALS_NAMES[s_num]
    
    wid = math.ceil(kin / 13)
    data['wave_name'] = data.get('波符', '未知') 
    data['wave_img'] = f"瑪雅曆20波符-{str(wid).zfill(2)}.png"
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
    s = (kin-1)%20+1; t = (kin-1)%13+1
    return { 
        "destiny": {"s":s, "t":t}, 
        "analog": {"s": (19-s if 19-s>0 else 19-s+20), "t":t}, 
        "antipode": {"s": (s+10 if s+10<=20 else s-10), "t":t}, 
        "occult": {"s": 21-s, "t": (14-t if 14-t>0 else 14-t+13)}, 
        "guide": {"s":s, "t":t} 
    }

def get_psi_kin(date_obj):
    conn = get_db()
    res = {}
    try:
        q_dates = [date_obj.strftime("%m月%d日"), f"{date_obj.month}月{date_obj.day}日"]
        for q in q_dates:
            row = conn.execute("SELECT * FROM PSI_Bank WHERE 月日 = ?", (q,)).fetchone()
            if row:
                p_kin = int(row['PSI印記'])
                res = {"KIN": p_kin, "Info": get_full_kin_data(p_kin), "Matrix": row.get('矩陣位置','-')}
                break
    except: pass
    finally: conn.close()
    return res

def get_goddess_kin(kin):
    o = get_oracle(kin)
    occ_kin = (o['occult']['s'] + (o['occult']['t']-1)*20 -1)%260 + 1
    g_kin = (occ_kin + 130) % 260
    if g_kin == 0: g_kin = 260
    return {"KIN": g_kin, "Info": get_full_kin_data(g_kin), "Base_KIN": occ_kin}

def get_wavespell_data(kin):
    wave_data = []
    curr_tone = (kin - 1) % 13 + 1
    start_kin = kin - (curr_tone - 1)
    if start_kin <= 0: start_kin += 260
    
    for i in range(13):
        curr = start_kin + i
        if curr > 260: curr -= 260
        info = get_full_kin_data(curr)
        wave_data.append({
            "Tone": i+1, "KIN": curr, "Question": TONE_QUESTIONS[i+1],
            "Seal": info.get('圖騰'), "Name": info.get('主印記'), "Image": info.get('seal_img')
        })
    return wave_data

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

def get_maya_calendar_info(date_obj):
    conn = get_db()
    res = {"Maya_Date": "-", "Maya_Month": "-", "Maya_Week": "-", "Heptad_Path": "-", "Plasma": "-", "Status": "查無資料"}
    try:
        q_dates = [date_obj.strftime('%m月%d日'), f"{date_obj.month}月{date_obj.day}日", date_obj.strftime('%Y-%m-%d')]
        for q in q_dates:
            row = conn.execute("SELECT * FROM Calendar_Converter WHERE 國曆生日 = ?", (q,)).fetchone()
            if row:
                res.update({
                    'Maya_Date': row.get('瑪雅生日', '-'), 'Maya_Month': row.get('瑪雅月', '-'),
                    'Maya_Week': row.get('瑪雅週', '-'), 'Heptad_Path': row.get('七價路徑', '-'),
                    'Plasma': row.get('等離子日', '-'), 'Status': "查詢成功"
                })
                y = date_obj.year - 1 if (date_obj.month<7 or (date_obj.month==7 and date_obj.day<26)) else date_obj.year
                res['Solar_Year'] = f"NS 1.{y-1987+30}"
                break
    except: pass
    finally: conn.close()
    return res

def get_week_key_sentence(week_name):
    conn = get_db()
    res = None
    try:
        if week_name:
            row = conn.execute(f"SELECT 關鍵句 FROM Maya_Week_Key WHERE 瑪雅週 LIKE '%{week_name}%'").fetchone()
            if row: res = row['關鍵句']
    except: pass
    finally: conn.close()
    return res

def get_heptad_prayer(path_name):
    conn = get_db()
    res = None
    try:
        if path_name:
            clean = path_name.split('\n')[0]
            row = conn.execute(f"SELECT 祈禱文 FROM Heptad_Prayer WHERE 七價路徑 LIKE '%{clean}%'").fetchone()
            if row: res = row['祈禱文']
    except: pass
    finally: conn.close()
    return res

def get_octave_positions(note):
    conn = get_db()
    res = []
    try:
        rows = conn.execute("SELECT * FROM Octave_Scale WHERE 八度音符 = ?", (note,)).fetchall()
        for r in rows: res.append(dict(r))
    except: pass
    finally: conn.close()
    return res

def save_user_data(name, dob_str, kin, main_sign):
    conn = get_db()
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS Users (id INTEGER PRIMARY KEY, 姓名 TEXT, 生日 TEXT, KIN INTEGER, 主印記 TEXT)")
        if conn.execute("SELECT COUNT(*) FROM Users WHERE 姓名=?", (name,)).fetchone()[0] == 0:
            conn.execute("INSERT INTO Users (姓名, 生日, KIN, 主印記) VALUES (?, ?, ?, ?)", (name, dob_str, kin, main_sign))
            conn.commit(); return True, "成功"
        return False, "已存在"
    except Exception as e: return False, str(e)
    finally: conn.close()

def get_user_list():
    conn = get_db()
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS Users (id INTEGER PRIMARY KEY, 姓名 TEXT, 生日 TEXT, KIN INTEGER, 主印記 TEXT)")
        return pd.read_sql("SELECT 姓名, 生日, KIN FROM Users", conn)
    except: return pd.DataFrame()
    finally: conn.close()

def get_user_kin(name, df):
    row = df[df['姓名'] == name]
    if not row.empty: return int(row.iloc[0]['KIN']), row.iloc[0]['生日']
    return None, None

def calculate_composite(k1, k2):
    r = (k1+k2)%260
    return 260 if r==0 else r
