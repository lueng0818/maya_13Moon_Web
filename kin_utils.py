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

# 調性問句列表
TONE_QUESTIONS = {
    1: "我的目的是什麼？", 2: "我的挑戰是什麼？", 3: "我如何提供最好的服務？",
    4: "我採取什麼形式？", 5: "我如何被授權？", 6: "我如何組織平等？",
    7: "我如何歸於中心？", 8: "我是否活出所信？", 9: "我如何完成目的？",
    10: "我如何完美顯化？", 11: "我如何釋放與放下？", 12: "我如何奉獻自己？",
    13: "我如何活在當下？"
}

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
    default_min, default_max = 1800, 2100
    try:
        conn = get_db()
        # 檢查 Kin_Start 表格是否存在
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Kin_Start'")
        if cursor.fetchone():
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
    """
    邏輯：(年起始 KIN + 月累積天數 + 日期) % 260
    """
    conn = get_db()
    try:
        # 1. 查年份 (Kin_Start)
        q_year = f"SELECT 起始KIN FROM Kin_Start WHERE 年份 = {date_obj.year}"
        res_year = conn.execute(q_year).fetchone()
        if not res_year: return None, f"無 {date_obj.year} 年起始KIN資料"
        start_kin = res_year['起始KIN']
        
        # 2. 查月份 (Month_Accum)
        q_month = f"SELECT 累積天數 FROM Month_Accum WHERE 月份 = {date_obj.month}"
        res_month = conn.execute(q_month).fetchone()
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
    
    # 1. 從 Kin_Basic 讀取基礎資料 (主印記、波符、城堡等文字)
    try:
        row = conn.execute("SELECT * FROM Kin_Basic WHERE KIN = ?", (kin,)).fetchone()
        if row: data.update(dict(row))
    except: pass
    
    # 2. 補充從 Kin_Data 讀取進階資料 (諧波, 密碼子, 城堡, 銀河季節, 脈輪, 原型, BMU, 流)
    try:
        row_data = conn.execute("SELECT * FROM Kin_Data WHERE KIN = ?", (kin,)).fetchone()
        if row_data:
             for key, value in dict(row_data).items():
                # 僅補充 Kin_Basic 沒有的欄位，或重要的結構資訊
                if key not in data or key in ['諧波', '密碼子', '星際原型', 'BMU', '行星', '流', '電路', '說明', '家族', '對應脈輪', '電路說明']:
                    data[key] = value
    except: pass

    # 3. 補充矩陣資料 (若 Matrix_Data 存在)
    try:
        m = conn.execute("SELECT * FROM Matrix_Data WHERE 時間矩陣_KIN = ?", (kin,)).fetchone()
        if m:
            data['Matrix_Time'] = m.get('時間矩陣_矩陣位置')
            data['Matrix_Space'] = m.get('空間矩陣_矩陣位置')
            data['Matrix_Sync'] = m.get('共時矩陣_矩陣位置')
            data['Matrix_BMU'] = m.get('基本母體矩陣_BMU')
    except: pass
    
    conn.close()

    # 4. 補充 Base Matrix (BMU 詳細資訊)
    bmu_data = get_base_matrix_data(kin)
    data.update(bmu_data)

    # 5. 補充圖片路徑與名稱 ID (使用數學推算 ID)
    s_num = int(data.get('圖騰數字', (kin - 1) % 20 + 1))
    t_num = int(data.get('調性數字', (kin - 1) % 13 + 1))
    
    data['seal_img'] = SEAL_FILES.get(s_num, "01紅龍.png")
    data['tone_img'] = TONE_FILES.get(t_num, "瑪雅曆法圖騰-34.png")
    
    # 補充中文名稱 (確保名稱對應正確)
    if '調性' not in data: data['調性'] = TONE_NAMES[t_num]
    if '圖騰' not in data: data['圖騰'] = SEALS_NAMES[s_num]
    
    wid = math.ceil(kin / 13)
    data['wave_name'] = data.get('波符', '未知') # 優先使用 Kin_Basic 裡的波符名稱
    data['wave_img'] = f"瑪雅曆20波符-{str(wid).zfill(2)}.png"

    return data

def get_base_matrix_data(kin_num):
    """從 Base_Matrix_441 表查詢 KIN 對應的基礎矩陣資訊"""
    conn = get_db()
    result = {}
    try:
        # 查詢
        query = "SELECT * FROM Base_Matrix_441 WHERE KIN = ?"
        row = conn.execute(query, (kin_num,)).fetchone()
        
        if row:
            result = {
                "BMU_Position": row.get('矩陣位置', '-'),
                "BMU_Note": row.get('八度音符', '-'),
                "BMU_Brain": row.get('對應腦部', '-')
            }
        
    except: pass
    finally: conn.close()
    return result

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

# --- 5. PSI 與 女神計算 ---
def get_psi_kin(date_obj):
    """查詢 PSI 印記 (查表)"""
    conn = get_db()
    psi_data = {}
    try:
        # 嘗試多種日期格式查詢
        q_dates = [
            date_obj.strftime("%m月%d日"), # 07月26日 (補零)
            f"{date_obj.month}月{date_obj.day}日" # 7月26日 (不補零)
        ]
        
        for q in q_dates:
            row = conn.execute("SELECT * FROM PSI_Bank WHERE 月日 = ?", (q,)).fetchone()
            if row:
                p_kin = int(row['PSI印記'])
                p_info = get_full_kin_data(p_kin)
                psi_data = {"KIN": p_kin, "Info": p_info, "Matrix": row.get('矩陣位置','-')}
                break
    except: pass
    finally: conn.close()
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

# --- 8. 瑪雅曆法日期查詢 ---
def get_maya_calendar_info(date_obj):
    conn = get_db()
    result = {"Maya_Date": "-", "Maya_Month": "-", "Maya_Week": "-", "Heptad_Path": "-", "Plasma": "-", "Solar_Year": "-", "Status": "查無資料"}
    
    try:
        # 嘗試多種日期格式查詢
        q_dates = [
            date_obj.strftime('%m月%d日'),       # 07月26日 (最優先)
            f"{date_obj.month}月{date_obj.day}日", # 7月26日
            date_obj.strftime('%Y-%m-%d')        # 2023-07-26 (備用)
        ]
        
        for q in q_dates:
            row = conn.execute("SELECT * FROM Calendar_Converter WHERE 國曆生日 = ?", (q,)).fetchone()
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
                break
        
    except Exception as e:
        result['Status'] = f"Error: {e}"
        
    conn.close()
    return result

def get_week_key_sentence(week_name):
    conn = get_db()
    key_sentence = None
    try:
        if week_name:
            query = "SELECT 關鍵句 FROM Maya_Week_Key WHERE 瑪雅週 = ?"
            row = conn.execute(query, (week_name,)).fetchone()
            if row: key_sentence = row.get('關鍵句', '查無關鍵句內容')
    except: pass
    conn.close()
    return key_sentence

def get_heptad_prayer(path_name):
    conn = get_db()
    prayer = None
    try:
        if path_name:
            # 處理換行符號問題
            clean_path = path_name.split('\n')[0]
            # 模糊查詢
            query = f"SELECT 祈禱文 FROM Heptad_Prayer WHERE 七價路徑 LIKE '%{clean_path}%'"
            row = conn.execute(query).fetchone()
            if row: prayer = row.get('祈禱文', '查無祈禱文內容')
    except: pass
    conn.close()
    return prayer

def get_wavespell_data(kin):
    """根據 KIN 計算所屬波符的完整 13 天旅程"""
    conn = get_db()
    wave_data = []
    
    # 1. 計算波符起始 KIN (磁性調性)
    current_tone = (kin - 1) % 13 + 1
    start_kin = kin - (current_tone - 1)
    if start_kin <= 0: start_kin += 260 

    # 2. 迴圈生成 13 個 KIN 的資料
    try:
        for i in range(13):
            curr = start_kin + i
            if curr > 260: curr -= 260
            
            info = get_full_kin_data(curr)
            
            wave_data.append({
                "Tone": i + 1,
                "KIN": curr,
                "Question": TONE_QUESTIONS[i + 1],
                "Seal": info.get('圖騰', '未知'),
                "Name": info.get('主印記', ''),
                "Image": info.get('seal_img', '')
            })
            
    except: pass
    return wave_data

def get_octave_positions(note):
    conn = get_db()
    results = []
    try:
        query = "SELECT 矩陣位置, 行, 列 FROM Octave_Scale WHERE 八度音符 = ?"
        rows = conn.execute(query, (note,)).fetchall()
        for row in rows:
            results.append({
                "Position": row.get('矩陣位置', '-'),
                "Row": row.get('行', '-'),
                "Col": row.get('列', '-')
            })
    except: pass
    conn.close()
    return results

# --- 用戶管理功能 ---
def ensure_users_table(conn):
    """確保 Users 表格存在，若無則建立"""
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
    """將人員資料存入資料庫"""
    conn = get_db()
    try:
        ensure_users_table(conn)
        # 檢查是否已存在
        exist = conn.execute("SELECT COUNT(*) FROM Users WHERE 姓名 = ?", (name,)).fetchone()[0]
        if exist == 0:
            conn.execute("INSERT INTO Users (姓名, 生日, KIN, 主印記) VALUES (?, ?, ?, ?)", (name, dob_str, kin, main_sign))
            conn.commit()
            return True, "建檔成功"
        else:
            return False, "此姓名已存在，請使用不同名稱"
    except Exception as e:
        return False, f"存檔失敗: {e}"
    finally:
        conn.close()

def get_user_list():
    """獲取人員列表"""
    conn = get_db()
    try:
        ensure_users_table(conn)
        df = pd.read_sql("SELECT 姓名, 生日, KIN FROM Users", conn)
        return df
    except:
        return pd.DataFrame()
    finally:
        conn.close()

def get_user_kin(name, df_users):
    """根據姓名從 DF 裡查找 KIN"""
    if df_users.empty: return None, None
    user_row = df_users[df_users['姓名'] == name]
    if not user_row.empty:
        return int(user_row.iloc[0]['KIN']), user_row.iloc[0]['生日']
    return None, None

def calculate_composite(kin_a, kin_b):
    """合盤 KIN"""
    total = kin_a + kin_b
    comp = total % 260
    return 260 if comp == 0 else comp
