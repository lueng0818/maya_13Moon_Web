import sqlite3
import datetime
import math
import base64
import os
import re

# 判斷是否在 Railway 環境 (通常 Railway 不會特別設這個，但我們可以偵測路徑)
if os.path.exists("/app/storage"):
    DB_PATH = "/app/storage/13moon.db"
else:
    DB_PATH = "13moon.db" # 本地開發用
import pandas as pd

DB_PATH = "13moon.db"

# --- 1. 靜態資源設定 ---
SEALS_NAMES = ["","紅龍","白風","藍夜","黃種子","紅蛇","白世界橋","藍手","黃星星","紅月","白狗","藍猴","黃人","紅天行者","白巫師","藍鷹","黃戰士","紅地球","白鏡","藍風暴","黃太陽"]
SEAL_FILES = { i: f"{str(i).zfill(2)}{name}.png" for i, name in enumerate(SEALS_NAMES) if i > 0 }
TONE_FILES = { i: f"瑪雅曆法圖騰-{i+33}.png" for i in range(1, 14) }
TONE_NAMES = ["","磁性","月亮","電力","自我存在","超頻","韻律","共振","銀河星系","太陽","行星","光譜","水晶","宇宙"]

# ✨ 更新後的波符十三問
TONE_QUESTIONS = {
    1: "生命的方向：靈魂的方向，前進的目標。也可以說使命和任務最重要的起始點。",
    2: "生命的挑戰：靈魂的黑暗面，包括心理陰影，比較恐懼的方面是什麼？",
    3: "生命的品質：靈魂內在的品質是什麼？",
    4: "展現的形式：你的靈魂想要做什麼形式的服務呢？",
    5: "靈魂的力量：生命想要綻放什麼樣的力量？",
    6: "生命的平衡：在人際間溝通互動、尋求關係平衡的方法是什麼？",
    7: "靈魂的共振：你的靈魂是用什麼方式和他人共振呢？",
    8: "靈魂的信念：你的靈魂本身內在與生俱來的信念，認為什麼是重要的？",
    9: "靈魂的渴望：靈魂的意願與想望是什麼？",
    10: "靈魂完美的顯化：用什麼方式讓自己完美？",
    11: "靈魂的釋放力：帶出內在信息的方式。",
    12: "靈魂的清晰度：可以合作與奉獻什麼力量？",
    13: "靈魂的目的地：你要成為什麼狀態的你、如何分享愛呢？"
}

# --- 2. 輔助函數 ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_img_b64(path):
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return ""

def get_year_range():
    default_min, default_max = 1800, 2100
    try:
        conn = get_db()
        res = conn.execute("SELECT MIN(年份), MAX(年份) FROM Kin_Start").fetchone()
        if res and res[0]: return int(res[0]), int(res[1])
    except: pass
    finally: 
        try: conn.close() 
        except: pass
    return default_min, default_max

# --- 3. KIN 計算邏輯 ---
def calculate_kin_v2(date_obj):
    conn = get_db()
    try:
        res_year = conn.execute(f"SELECT 起始KIN FROM Kin_Start WHERE 年份 = {date_obj.year}").fetchone()
        if not res_year: return None, f"無 {date_obj.year} 年資料"
        res_month = conn.execute(f"SELECT 累積天數 FROM Month_Accum WHERE 月份 = {date_obj.month}").fetchone()
        if not res_month: return None, f"無 {date_obj.month} 月資料"
        
        kin = (res_year['起始KIN'] + res_month['累積天數'] + date_obj.day) % 260
        return (260 if kin == 0 else kin), None
    except Exception as e: return None, str(e)
    finally: conn.close()

def calculate_kin_math(date_obj):
    base = datetime.date(2023, 7, 26)
    delta = (date_obj - base).days
    kin = (1 + delta) % 260
    return 260 if kin == 0 else kin

# --- 4. 資料獲取核心 ---
def get_base_matrix_data(kin_num):
    conn = get_db()
    result = {}
    try:
        row = conn.execute("SELECT * FROM Base_Matrix_441 WHERE KIN = ?", (kin_num,)).fetchone()
        if row:
            result = {"BMU_Position": row.get('矩陣位置','-'), "BMU_Note": row.get('八度音符','-'), "BMU_Brain": row.get('對應腦部','-')}
    except: pass
    finally: conn.close()
    return result

def get_full_kin_data(kin):
    conn = get_db()
    data = {}
    try:
        row = conn.execute("SELECT * FROM Kin_Basic WHERE KIN = ?", (kin,)).fetchone()
        if row: data.update(dict(row))
        
        row_d = conn.execute("SELECT * FROM Kin_Data WHERE KIN = ?", (kin,)).fetchone()
        if row_d:
             for k, v in dict(row_d).items():
                if k not in data or k in ['諧波', '密碼子', '星際原型', 'BMU', '行星', '流', '電路', '說明', '家族', '對應脈輪', '電路說明']:
                    data[k] = v

        m = conn.execute("SELECT * FROM Matrix_Data WHERE 時間矩陣_KIN = ?", (kin,)).fetchone()
        if m:
            data['Matrix_Time'] = m.get('時間矩陣_矩陣位置')
            data['Matrix_Space'] = m.get('空間矩陣_矩陣位置')
            data['Matrix_Sync'] = m.get('共時矩陣_矩陣位置')
            data['Matrix_BMU'] = m.get('基本母體矩陣_BMU')
    except: pass
    conn.close()

    data.update(get_base_matrix_data(kin))

    s_num = int(data.get('圖騰數字', (kin-1)%20+1))
    t_num = int(data.get('調性數字', (kin-1)%13+1))
    data['seal_img'] = SEAL_FILES.get(s_num, "01紅龍.png")
    data['tone_img'] = TONE_FILES.get(t_num, "瑪雅曆法圖騰-34.png")
    if '調性' not in data: data['調性'] = TONE_NAMES[t_num]
    if '圖騰' not in data: data['圖騰'] = SEALS_NAMES[s_num]
    
    wid = math.ceil(kin/13)
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

# --- 5. 五大神諭 (關鍵修正) ---
def get_oracle(kin):
    """
    計算五大神諭 (Corrected Logic)
    - Guide, Analog, Antipode 調性相同 (t)
    - Occult 調性互補 (sum=14)
    """
    s = (kin - 1) % 20 + 1  # 主圖騰 (1-20)
    t = (kin - 1) % 13 + 1  # 主調性 (1-13)
    
    # 1. 支持 (Analog): 圖騰相加 19, 調性相同
    ana_s = 19 - s
    if ana_s <= 0: ana_s += 20
    ana_t = t
    
    # 2. 擴展 (Antipode): 圖騰相差 10, 調性相同
    anti_s = (s + 10) % 20
    if anti_s == 0: anti_s = 20
    anti_t = t
    
    # 3. 推動/隱藏 (Occult): 圖騰相加 21, 調性相加 14
    occ_s = 21 - s
    occ_t = 14 - t
    
    # 4. 引導 (Guide): 調性相同, 圖騰依調性公式計算
    # 規則: 調性除以5的餘數決定位移 (0, 12, 4, 16, 8)
    offset_map = {1:0, 2:12, 3:4, 4:16, 0:8} 
    offset = offset_map[t % 5]
    guide_s = (s + offset) % 20
    if guide_s == 0: guide_s = 20
    guide_t = t
    
    return { 
        "destiny": {"s":s, "t":t}, 
        "analog": {"s":ana_s, "t":ana_t}, 
        "antipode": {"s":anti_s, "t":anti_t}, 
        "occult": {"s":occ_s, "t":occ_t}, 
        "guide": {"s":guide_s, "t":guide_t} 
    }

# --- 6. PSI 與 女神 ---
def get_psi_kin(date_obj):
    conn = get_db()
    res = {}
    try:
        # 🎯 核彈級解法：不依賴 SQL 字串比對，直接把整張表抓出來 (才366筆，速度很快)
        df = pd.read_sql("SELECT * FROM PSI_Bank", conn)
        
        target_m = date_obj.month
        target_d = date_obj.day
        
        found_row = None
        
        # 逐行檢查，只看數字，不看中文或符號
        for _, row in df.iterrows():
            # 優先檢查 '月日' 欄位，沒有就檢查 '國曆生日'
            raw_text = str(row.get('月日', row.get('國曆生日', '')))
            
            # 使用正規表達式抓出所有數字 (例如 "04月14日" -> ['04', '14'])
            numbers = re.findall(r'\d+', raw_text)
            
            if len(numbers) >= 2:
                m = int(numbers[0])
                d = int(numbers[1])
                
                # 如果月和日都對上了，就是這一筆！
                if m == target_m and d == target_d:
                    found_row = row
                    break
        
        if found_row is not None:
            p = int(found_row['PSI印記'])
            res = {
                "KIN": p, 
                "Info": get_full_kin_data(p), 
                "Matrix": found_row.get('矩陣位置', '-'),
                "Maya_Date": found_row.get('瑪雅生日', '-')
            }
        else:
            print(f"PSI 暴力搜尋失敗: {target_m}/{target_d}")

    except Exception as e:
        print(f"PSI 查詢錯誤: {e}")
    finally: conn.close()
    return res
    
def get_kin_from_seal_tone(s, t):
    """
    輔助函式：將圖騰(1-20)與調性(1-13)轉回 KIN(1-260)
    公式推導：k = ((t - s) % 13) * 40 + s
    """
    val = ((t - s) % 13) * 40 + s
    if val > 260: val -= 260
    return val

def get_goddess_kin(kin):
    """
    計算女神力量印記 (修正版)
    定義：出生主印記五個印記 (主/支/擴/引/推) 的 KIN 加總
    規則：總和除以 260 取餘數，若為 0 則為 260
    """
    # 1. 取得五大神諭的 圖騰(s) 與 調性(t)
    oracle = get_oracle(kin)
    
    # 2. 將五個位置轉換回 KIN 數值
    k_destiny = kin  # 主印記本身
    k_analog = get_kin_from_seal_tone(oracle['analog']['s'], oracle['analog']['t'])
    k_antipode = get_kin_from_seal_tone(oracle['antipode']['s'], oracle['antipode']['t'])
    k_guide = get_kin_from_seal_tone(oracle['guide']['s'], oracle['guide']['t'])
    k_occult = get_kin_from_seal_tone(oracle['occult']['s'], oracle['occult']['t'])
    
    # 3. 加總
    total_sum = k_destiny + k_analog + k_antipode + k_guide + k_occult
    
    # 4. 取餘數 (MOD 260)
    g_kin = total_sum % 260
    if g_kin == 0: g_kin = 260
    
    return {
        "KIN": g_kin, 
        "Info": get_full_kin_data(g_kin), 
        "Base_KIN": kin, # 紀錄源頭 KIN
        "Sum_Details": [k_destiny, k_analog, k_antipode, k_guide, k_occult] # (除錯用) 紀錄五個組成 KIN
    }

# --- 7. 其他應用 ---
def calculate_equivalent_kin(kin):
    conn = get_db()
    res = {}
    try:
        row = conn.execute("SELECT 時間矩陣_矩陣位置, 空間矩陣_矩陣位置, 共時矩陣_矩陣位置 FROM Matrix_Data WHERE 時間矩陣_KIN = ?", (kin,)).fetchone()
        if row:
            tc, sc, sync = row['時間矩陣_矩陣位置'], row['空間矩陣_矩陣位置'], row['共時矩陣_矩陣位置']
            bt, bs, bsyn = get_bmu_from_coord(tc), get_bmu_from_coord(sc), get_bmu_from_coord(sync)
            tfi = bt + bs + bsyn
            eq = tfi % 260
            if eq==0 and tfi>0: eq=260
            res = {"TFI": tfi, "Eq_Kin": eq, "Eq_Info": get_full_kin_data(eq), "Coords": [tc, sc, sync], "BMUs": [bt, bs, bsyn]}
    except: pass
    finally: conn.close()
    return res

def get_bmu_from_coord(coord):
    if not coord: return 0
    conn = get_db()
    try:
        row = conn.execute("SELECT 基本母體矩陣_KIN FROM Matrix_Data WHERE 基本母體矩陣_矩陣位置 = ?", (coord.strip(),)).fetchone()
        return row[0] if row else 0
    except: return 0
    finally: conn.close()

def get_maya_calendar_info(date_obj):
    conn = get_db()
    
    # 預設回傳值
    res = {
        "Maya_Date": "-", "Maya_Month": "-", "Maya_Week": "-", 
        "Heptad_Path": "-", "Plasma": "-", 
        "Solar_Year": "未知", "Status": "計算中"
    }

    MOON_NAMES = ['', '磁性之月', '月亮之月', '電力之月', '自我存在之月', '超頻之月', '韻律之月', '共振之月', '銀河星系之月', '太陽之月', '行星之月', '光譜之月', '水晶之月', '宇宙之月']
    PLASMA_NAMES = ['Dali 達利', 'Seli 瑟利', 'Gamma 伽馬', 'Kali 卡利', 'Alpha 阿爾法', 'Limi 利米', 'Silio 西利歐']
    WEEK_NAMES = ['紅色啟動之週', '白色淨化之週', '藍色蛻變之週', '黃色收成之週']

    try:
        # 1. 處理特殊日期：2/29 (Hunab Ku)
        if date_obj.month == 2 and date_obj.day == 29:
            res.update({
                "Maya_Date": "0.0.Hunab Ku",
                "Maya_Month": "無時間月",
                "Maya_Week": "-",
                "Plasma": "-",
                "Heptad_Path": "-"
            })
        
        # 2. 處理特殊日期：7/25 (無時間日)
        elif date_obj.month == 7 and date_obj.day == 25:
            res.update({
                "Maya_Date": "Day Out of Time",
                "Maya_Month": "無時間日",
                "Maya_Week": "-",
                "Plasma": "-",
                "Heptad_Path": "-"
            })
            
        else:
            # 3. 一般日期計算
            # 判斷星際年起始點 (每年 7/26)
            start_year = date_obj.year
            if (date_obj.month < 7) or (date_obj.month == 7 and date_obj.day < 26):
                start_year -= 1
            
            start_date = datetime.date(start_year, 7, 26)
            
            # 計算經過天數 (Day of Year)
            delta = (date_obj - start_date).days
            
            # 修正閏年影響：如果是閏年，且日期在 2/29 之後，天數要減 1 (因為 13月亮曆不計 2/29)
            # 判斷該星際年是否跨越了閏日 (即 start_year 的隔年是閏年)
            next_year = start_year + 1
            is_leap = (next_year % 4 == 0 and next_year % 100 != 0) or (next_year % 400 == 0)
            if is_leap and date_obj > datetime.date(next_year, 2, 29):
                delta -= 1

            # 計算月 (1-13) 與 日 (1-28)
            moon_idx = (delta // 28) + 1
            day_idx = (delta % 28) + 1
            
            # 計算週 (0-3) 與 等離子 (0-6)
            week_idx = (day_idx - 1) // 7
            plasma_idx = (day_idx - 1) % 7
            
            # 計算七價路徑 (1-52)
            heptad_path = (moon_idx - 1) * 4 + week_idx + 1

            # 填入結果
            if 1 <= moon_idx <= 13:
                res.update({
                    "Maya_Date": f"{moon_idx}.{day_idx}", # 格式: 月.日
                    "Maya_Month": f"{MOON_NAMES[moon_idx]} (第{day_idx}天)",
                    "Maya_Week": WEEK_NAMES[week_idx],
                    "Plasma": PLASMA_NAMES[plasma_idx],
                    "Heptad_Path": f"路徑 {heptad_path}"
                })

        # 4. 查詢流年名稱 (維持資料庫查詢，或若無資料則顯示 NS 年份)
        # 嘗試從資料庫抓取 "星際年" (如果有該表格)
        try:
            row_y = conn.execute("SELECT 對應星際年 FROM Star_Years WHERE 起始年 = ?", (start_year,)).fetchone()
            if row_y:
                res['Solar_Year'] = row_y['對應星際年']
            else:
                # 備用顯示
                res['Solar_Year'] = f"NS 1.{start_year - 1987 + 30}" # 簡單推算
        except:
            pass

    except Exception as e:
        print(f"13:28 計算錯誤: {e}")
        res['Status'] = "計算失敗"
        
    finally:
        conn.close()
        
    return res

def get_week_key_sentence(week_name):
    conn = get_db()
    try:
        if week_name:
            row = conn.execute(f"SELECT 關鍵句 FROM Maya_Week_Key WHERE 瑪雅週 LIKE '%{week_name}%'").fetchone()
            if row: return row['關鍵句']
    except: pass
    finally: conn.close()
    return None

def get_heptad_prayer(path_name):
    conn = get_db()
    try:
        if path_name:
            clean = path_name.split('\n')[0]
            row = conn.execute(f"SELECT 祈禱文 FROM Heptad_Prayer WHERE 七價路徑 LIKE '%{clean}%'").fetchone()
            if row: return row['祈禱文']
    except: pass
    finally: conn.close()
    return None

def get_whole_brain_tuning():
    conn = get_db()
    res = []
    try:
        rows = conn.execute("SELECT 全腦調頻_對應腦部, 全腦調頻_調頻語 FROM Matrix_Data WHERE 全腦調頻_對應腦部 IS NOT NULL").fetchall()
        seen = set()
        for r in rows:
            if r[0] and r[0] not in seen:
                res.append({"Part": r[0], "Text": r[1]})
                seen.add(r[0])
    except: pass
    finally: conn.close()
    return res

def get_king_prophecy():
    conn = get_db()
    try: return pd.read_sql("SELECT * FROM King_Prophecy", conn)
    except: return pd.DataFrame()
    finally: conn.close()

def get_telektonon_info(kin, maya_cal):
    conn = get_db()
    res = {"Crystal_Battery":"-", "Warrior_Cube":"-", "Turtle_Day":"-", "Turtle_Color":"-", "Rune":"-"}
    try:
        t_id = (kin - 1) % 13 + 1
        s_id = (kin - 1) % 20 + 1
        res['Crystal_Battery'] = f"調性 {t_id} ({TONE_NAMES[t_id]})"
        res['Warrior_Cube'] = f"圖騰 {s_id} ({SEALS_NAMES[s_id]})"
        
        m_day = maya_cal.get('Maya_Date', '').split('.')[-1]
        if m_day and m_day != '-':
            dn = int(m_day)
            res['Turtle_Day'] = f"第 {dn} 天"
            
            for tbl, color in [("Green_Turtle_Day", "綠烏龜"), ("White_Turtle_Day", "白烏龜"), ("Yellow_Turtle_Day", "黃烏龜")]:
                cols = "說明" if color!="黃烏龜" else "說明, 符文意涵"
                row = conn.execute(f"SELECT {cols} FROM {tbl} WHERE 第幾天 = ?", (dn,)).fetchone()
                if row:
                    res.update({"Turtle_Color": color, "Turtle_Desc": row['說明']})
                    if color == "黃烏龜": res['Rune'] = row['符文意涵']
    except: pass
    finally: conn.close()
    return res

def get_wavespell_data(kin):
    wd = []
    ct = (kin - 1) % 13 + 1
    sk = kin - (ct - 1)
    if sk <= 0: sk += 260
    for i in range(13):
        c = sk + i
        if c > 260: c -= 260
        info = get_full_kin_data(c)
        wd.append({"Tone": i+1, "KIN": c, "Question": TONE_QUESTIONS[i+1], "Seal": info.get('圖騰'), "Name": info.get('主印記'), "Image": info.get('seal_img')})
    return wd

def get_octave_positions(note):
    conn = get_db()
    res = []
    try:
        rows = conn.execute("SELECT 矩陣位置, 行, 列 FROM Octave_Scale WHERE 八度音符 = ?", (note,)).fetchall()
        for r in rows: res.append(dict(r))
    except: pass
    finally: conn.close()
    return res

def calculate_life_castle(birth_date):
    bk, _ = calculate_kin_v2(birth_date)
    if not bk: bk = calculate_kin_math(birth_date)
    p = []
    for age in range(105):
        ck = (bk + age*105)%260
        if ck==0: ck=260
        info = get_full_kin_data(ck)
        c = age%52
        col = "#fff0f0" if c<13 else ("#f8f8f8" if c<26 else ("#f0f8ff" if c<39 else "#fffff0"))
        p.append({"Age":age, "Year":birth_date.year+age, "KIN":ck, "Info":info, "Color":col})
    return p

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

def update_user_data(oname, name, dob, kin, sign):
    conn = get_db()
    try:
        conn.execute("UPDATE Users SET 姓名=?, 生日=?, KIN=?, 主印記=? WHERE 姓名=?", (name, dob, kin, sign, oname))
        conn.commit(); return True, "成功"
    except Exception as e: return False, str(e)
    finally: conn.close()

def delete_user_data(names):
    conn = get_db()
    try:
        p = ','.join('?'*len(names))
        conn.execute(f"DELETE FROM Users WHERE 姓名 IN ({p})", tuple(names))
        conn.commit(); return True, "成功"
    except Exception as e: return False, str(e)
    finally: conn.close()

def get_user_list():
    conn = get_db()
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS Users (id INTEGER PRIMARY KEY, 姓名 TEXT, 生日 TEXT, KIN INTEGER, 主印記 TEXT)")
        return pd.read_sql("SELECT 姓名, 生日, KIN, 主印記 FROM Users", conn)
    except: return pd.DataFrame()
    finally: conn.close()

def get_user_kin(name, df):
    r = df[df['姓名']==name]
    if not r.empty: return int(r.iloc[0]['KIN']), r.iloc[0]['生日']
    return None, None

def calculate_composite(k1, k2):
    r = (k1+k2)%260
    return 260 if r==0 else r








