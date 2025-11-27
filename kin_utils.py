import sqlite3
import datetime
import math
import base64
import os
import pandas as pd

DB_PATH = "13moon.db"

# --- 1. 靜態資源設定 (解決 Import Error 的關鍵) ---
SEALS_NAMES = ["","紅龍","白風","藍夜","黃種子","紅蛇","白世界橋","藍手","黃星星","紅月","白狗","藍猴","黃人","紅天行者","白巫師","藍鷹","黃戰士","紅地球","白鏡","藍風暴","黃太陽"]

# 產生圖片檔名對照 (修正為 .png)
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
    
    # 1. 從 Kin_Basic 讀取基礎資料 (優先使用該表提供的波符、城堡等資訊)
    try:
        row = conn.execute("SELECT * FROM Kin_Basic WHERE KIN = ?", (kin,)).fetchone()
        if row: data.update(dict(row))
    except: pass
    
    # 2. 補充矩陣資料 (若 Matrix_Data 存在)
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
    
    # 支援 (Analog)
    ana = 19 - s; ana += 20 if ana <= 0 else 0
    # 擴展 (Antipode)
    anti = (s + 10) % 20; anti = 20 if anti == 0 else anti
    # 推動 (Occult)
    occ_s = 21 - s
    occ_t = 14 - t
    # 引導 (Guide) - 簡化為數學對應
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

# --- 8. 專門查詢主印記文字的函數 ---
def get_main_sign_text(kin_num):
    """從資料庫查詢主印記名稱 (使用 Kin_Basic 表)"""
    conn = get_db()
    try:
        query = "SELECT 主印記 FROM Kin_Basic WHERE KIN = ?"
        row = conn.execute(query, (kin_num,)).fetchone()
        if row:
            return row['主印記']
    except:
        pass
    finally:
        conn.close()
        
    return "查無印記名稱"

# --- 9. 瑪雅曆法日期查詢 ---
def get_maya_calendar_info(date_obj):
    """
    根據國曆日期查詢瑪雅曆日期、瑪雅月、瑪雅週等資訊。
    查詢依據: '國曆生日' (YYYY-MM-DD)
    """
    conn = get_db()
    result = {"Maya_Date": "-", "Maya_Month": "-", "Maya_Week": "-", "Heptad_Path": "-", "Plasma": "-", "Status": "查無資料"}
    
    try:
        query_date_str = date_obj.strftime('%Y-%m-%d')
        
        # 查詢 Calendar_Converter 表 (假設這個表是從 對應瑪雅生日.csv 匯入的)
        query = "SELECT * FROM Calendar_Converter WHERE 國曆生日 = ?"
        row = conn.execute(query, (query_date_str,)).fetchone()
        
        if row:
            result['Maya_Date'] = row.get('瑪雅生日', '-')
            result['Maya_Month'] = row.get('瑪雅月', '-')
            result['Maya_Week'] = row.get('瑪雅週', '-')
            result['Heptad_Path'] = row.get('七價路徑', '-')
            result['Plasma'] = row.get('等離子日', '-')
            result['Status'] = "查詢成功"
        
    except Exception as e:
        result['Status'] = f"Error: {e}"
        
    conn.close()
    return result

# --- 10. 瑪雅週關鍵句 ---
def get_week_key_sentence(week_name):
    """
    根據瑪雅週名稱查詢對應的關鍵句
    """
    conn = get_db()
    key_sentence = None
    try:
        # 查詢 Maya_Week_Key 表
        query = "SELECT 關鍵句 FROM Maya_Week_Key WHERE 瑪雅週 = ?"
        row = conn.execute(query, (week_name,)).fetchone()
        
        if row:
            key_sentence = row.get('關鍵句', '查無關鍵句內容')
        
    except Exception as e:
        print(f"Maya Week Key Error: {e}")
        
    conn.close()
    return key_sentence

# --- 11. 七價路徑祈禱文 ---
def get_heptad_prayer(path_name):
    """
    根據七價路徑名稱查詢對應的祈禱文
    """
    conn = get_db()
    prayer = None
    try:
        # 查詢 Heptad_Prayer 表
        query = "SELECT 祈禱文 FROM Heptad_Prayer WHERE 七價路徑 = ?"
        row = conn.execute(query, (path_name,)).fetchone()
        
        if row:
            prayer = row.get('祈禱文', '查無祈禱文內容')
        
    except Exception as e:
        print(f"Heptad Prayer Error: {e}")
        
    conn.close()
    return prayer

# --- 12. 用戶管理函數 ---
def save_user_data(name, dob_str, kin, main_sign):
    """將人員資料存入資料庫"""
    conn = get_db()
    try:
        conn.execute("INSERT INTO Users (姓名, 生日, KIN, 主印記) VALUES (?, ?, ?, ?)", (name, dob_str, kin, main_sign))
        conn.commit()
        return True, "建檔成功"
    except Exception as e:
        return False, f"存檔失敗: {e}"
    finally:
        conn.close()

def get_user_list():
    """獲取人員列表 (用於合盤下拉選單)"""
    conn = get_db()
    df = pd.read_sql("SELECT 姓名, 生日, KIN FROM Users", conn)
    conn.close()
    return df

def get_user_kin(name, df_users):
    """根據姓名從 DF 裡查找 KIN"""
    user_row = df_users[df_users['姓名'] == name]
    if not user_row.empty:
        return int(user_row.iloc[0]['KIN']), user_row.iloc[0]['生日']
    return None, None

def calculate_composite(kin_a, kin_b):
    """合盤 KIN = (Kin_A + Kin_B) % 260"""
    total = kin_a + kin_b
    comp = total % 260
    return 260 if comp == 0 else comp
