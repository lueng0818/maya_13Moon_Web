import sqlite3
import datetime
import math
import base64
import os
import pandas as pd
import re

DB_PATH = "13moon.db"

# --- 1. 靜態資源與常數設定 ---
SEALS_NAMES = ["","紅龍","白風","藍夜","黃種子","紅蛇","白世界橋","藍手","黃星星","紅月","白狗","藍猴","黃人","紅天行者","白巫師","藍鷹","黃戰士","紅地球","白鏡","藍風暴","黃太陽"]
TONE_NAMES = ["","磁性","月亮","電力","自我存在","超頻","韻律","共振","銀河星系","太陽","行星","光譜","水晶","宇宙"]

# 關鍵：使用純數字檔名 (01.png ~ 20.png)
SEAL_FILES = { i: f"{str(i).zfill(2)}.png" for i in range(1, 21) }
# 關鍵：使用 tone-數字檔名 (tone-1.png ~ tone-13.png)
TONE_FILES = { i: f"tone-{i}.png" for i in range(1, 14) }

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

# --- 2. 資料庫與基礎函數 ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ✨ 最終容錯版：支援檢查 PNG/JPG 大小寫與多種副檔名
def get_img_b64(path):
    if not path: return ""

    # 檢查原始路徑
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    
    # 檢查替代副檔名大小寫
    base, ext = os.path.splitext(path)
    extensions = ['.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG']
    
    for check_ext in extensions:
        if ext.lower() == check_ext.lower(): continue 
        
        new_path = base + check_ext
        if os.path.exists(new_path):
            with open(new_path, "rb") as f: return base64.b64encode(f.read()).decode()

    return "" 

def get_year_range():
    default_min, default_max = 1800, 2100
    try:
        conn = get_db()
        res = conn.execute("SELECT MIN(年份), MAX(年份) FROM Kin_Start").fetchone()
        conn.close()
        if res and res[0]: return int(res[0]), int(res[1])
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
    
    data.update(get_base_matrix_data(kin))

    s_num = int(data.get('圖騰數字', (kin-1)%20+1))
    t_num = int(data.get('調性數字', (kin-1)%13+1))
    
    data['seal_img'] = SEAL_FILES.get(s_num, f"{str(s_num).zfill(2)}.png")
    data['tone_img'] = TONE_FILES.get(t_num, f"tone-{t_num}.png")
    
    if '調性' not in data: data['調性'] = TONE_NAMES[t_num]
    if '圖騰' not in data: data['圖騰'] = SEALS_NAMES[s_num]
    
    try:
        seal_name = SEALS_NAMES[s_num]
        row_seal = conn.execute("SELECT * FROM Seal_Info_Map WHERE 圖騰 = ?", (seal_name,)).fetchone()
        if row_seal:
            for k in ['星際原型', 'BMU', '行星', '流', '電路', '說明', '家族']:
                if k in dict(row_seal):
                    data[k] = row_seal[k]
    except: pass
    
    conn.close()
    
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

# --- 5. 五大神諭 ---
def get_oracle(kin):
    s = (kin - 1) % 20 + 1  
    t = (kin - 1) % 13 + 1  
    
    ana_s = 19 - s
    if ana_s <= 0: ana_s += 20
    ana_t = t
    
    anti_s = (s + 10) % 20
    if anti_s == 0: anti_s = 20
    anti_t = t
    
    occ_s = 21 - s
    occ_t = 14 - t
    
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

def get_kin_from_seal_tone(s, t):
    val = ((t - s) % 13) * 40 + s
    if val > 260: val -= 260
    return val

# --- 6. PSI 與 女神 ---
def get_psi_kin(date_obj):
    conn = get_db()
    res = {}
    try:
        df = pd.read_sql("SELECT * FROM PSI_Bank", conn)
        target_m = date_obj.month
        target_d = date_obj.day
        found_row = None
        
        for _, row in df.iterrows():
            raw_text = str(row.get('月日', row.get('國曆生日', '')))
            numbers = re.findall(r'\d+', raw_text)
            if len(numbers) >= 2:
                m = int(numbers[0])
                d = int(numbers[1])
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
            print(f"PSI 查詢失敗: {target_m}/{target_d}")
            
    except Exception as e:
        print(f"PSI Error: {e}")
    finally: conn.close()
    return res

def get_goddess_kin(kin):
    oracle = get_oracle(kin)
    k_destiny = kin
    k_analog = get_kin_from_seal_tone(oracle['analog']['s'], oracle['analog']['t'])
    k_antipode = get_kin_from_seal_tone(oracle['antipode']['s'], oracle['antipode']['t'])
    k_guide = get_kin_from_seal_tone(oracle['guide']['s'], oracle['guide']['t'])
    k_occult = get_kin_from_seal_tone(oracle['occult']['s'], oracle['occult']['t'])
    
    total_sum = k_destiny + k_analog + k_antipode + k_guide + k_occult
    g_kin = total_sum % 260
    if g_kin == 0: g_kin = 260
    
    return {"KIN": g_kin, "Info": get_full_kin_data(g_kin), "Base_KIN": kin}

# --- 7. 13:28 曆法 ---
def get_maya_calendar_info(date_obj):
    conn = get_db()
    res = {
        "Maya_Date": "-", "Maya_Month": "-", "Maya_Week": "-", 
        "Heptad_Path": "-", "Plasma": "-", "Vinal": "-",
        "Solar_Year": "未知", "Status": "查無資料"
    }

    try:
        target_m = date_obj.month
        target_d = date_obj.day
        check_table = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Maya_1328_Map'").fetchone()
        
        found_row = None
        if check_table:
            df = pd.read_sql("SELECT * FROM Maya_1328_Map", conn)
            for _, row in df.iterrows():
                raw_text = str(row.get('月日', row.get('國曆生日', '')))
                numbers = re.findall(r'\d+', raw_text)
                if len(numbers) >= 2:
                    m = int(numbers[0])
                    d = int(numbers[1])
                    if m == target_m and d == target_d:
                        found_row = row
                        break
        
        if found_row is not None:
            res.update({
                "Maya_Date": found_row.get('瑪雅生日', '-'),
                "Maya_Month": found_row.get('瑪雅月', '-'),
                "Maya_Week": found_row.get('瑪雅週', '-'),
                "Heptad_Path": found_row.get('七價路徑', '-').replace('\n', ' '), 
                "Plasma": found_row.get('等離子日', '-').replace('\n', ' '),
                "Vinal": found_row.get('Vinal 肯定句', '-'),
                "Status": "查詢成功"
            })
        else:
            if target_m == 2 and target_d == 29:
                res.update({"Maya_Date": "0.0.Hunab Ku", "Maya_Month": "無時間月"})
            elif target_m == 7 and target_d == 25:
                res.update({"Maya_Date": "Day Out of Time", "Maya_Month": "無時間日"})

        start_year = date_obj.year
        if (target_m < 7) or (target_m == 7 and target_d < 26): start_year -= 1
        
        try:
            row_y = conn.execute("SELECT 對應星際年 FROM Star_Years WHERE 起始年 = ?", (start_year,)).fetchone()
            if row_y: res['Solar_Year'] = row_y['對應星際年']
            else: res['Solar_Year'] = f"NS 1.{start_year - 1987 + 30}"
        except: pass

    except Exception as e:
        print(f"13:28 Error: {e}")
    finally: conn.close()
    return res

# --- 8. 對等印記 (矩陣V5-V17限定) ---

def get_matrix_val_by_pos(table, pos):
    conn = get_db()
    try:
        row = conn.execute(f"SELECT Value FROM {table} WHERE Position = ?", (pos,)).fetchone()
        return row['Value'] if row else 0
    except: return 0
    finally: conn.close()

def get_matrix_pos_by_val(table, val):
    conn = get_db()
    try:
        row = conn.execute(f"SELECT Position FROM {table} WHERE Value = ?", (val,)).fetchone()
        return row['Position'] if row else None
    except: return None
    finally: conn.close()

def calculate_equivalent_kin_new(kin, maya_date_str):
    conn = get_db()
    logs = [] 
    res = {}
    
    try:
        try:
            m_part, d_part = maya_date_str.split('.')
            clean_maya_date = f"{int(m_part)}.{int(d_part)}"
        except:
            clean_maya_date = maya_date_str 

        row = conn.execute("SELECT 時間矩陣位置 FROM Maya_Time_Map WHERE 瑪雅生日 = ?", (clean_maya_date,)).fetchone()
        
        if not row:
            return {"Error": f"找不到瑪雅生日 {clean_maya_date} 的對應矩陣位置"}
            
        pos_1 = row['時間矩陣位置']
        v1_t = get_matrix_val_by_pos("Matrix_Time", pos_1)
        v1_s = get_matrix_val_by_pos("Matrix_Space", pos_1)
        v1_y = get_matrix_val_by_pos("Matrix_Sync", pos_1)
        sum_1 = v1_t + v1_s + v1_y
        
        logs.append(f"1️⃣ **時間矩陣路徑**")
        logs.append(f"瑪雅生日 {clean_maya_date} ➜ 座標 `{pos_1}`")
        logs.append(f"數值：{v1_t} (時) + {v1_s} (空) + {v1_y} (共) = **{sum_1}**")
        
        pos_2 = get_matrix_pos_by_val("Matrix_Space", kin)
        if not pos_2:
            sum_2 = 0
            logs.append(f"⚠️ KIN {kin} 在空間矩陣中找不到對應座標")
        else:
            v2_t = get_matrix_val_by_pos("Matrix_Time", pos_2)
            v2_s = get_matrix_val_by_pos("Matrix_Space", pos_2)
            v2_y = get_matrix_val_by_pos("Matrix_Sync", pos_2)
            sum_2 = v2_t + v2_s + v2_y
            logs.append(f"2️⃣ **空間矩陣路徑**")
            logs.append(f"KIN {kin} ➜ 座標 `{pos_2}`")
            logs.append(f"數值：{v2_t} (時) + {v2_s} (空) + {v2_y} (共) = **{sum_2}**")

        rows_3 = conn.execute("SELECT Position FROM Matrix_Sync WHERE Value = ?", (kin,)).fetchall()
        pos_3 = None
        for r in rows_3:
            p_str = r['Position']
            try:
                v_part = p_str.split(':')[0] 
                if v_part.startswith('V'):
                    v_val = int(v_part[1:])
                    if 5 <= v_val <= 17:
                        pos_3 = p_str
                        break
            except: continue
            
        if not pos_3:
            sum_3 = 0
            logs.append(f"⚠️ KIN {kin} 在共時矩陣 V5~V17 範圍內找不到對應座標")
        else:
            v3_t = get_matrix_val_by_pos("Matrix_Time", pos_3)
            v3_s = get_matrix_val_by_pos("Matrix_Space", pos_3)
            v3_y = get_matrix_val_by_pos("Matrix_Sync", pos_3)
            sum_3 = v3_t + v3_s + v3_y
            logs.append(f"3️⃣ **共時矩陣路徑**")
            logs.append(f"KIN {kin} ➜ 座標 `{pos_3}` (V5-V17 區間)")
            logs.append(f"數值：{v3_t} (時) + {v3_s} (空) + {v3_y} (共) = **{sum_3}**")

        total = sum_1 + sum_2 + sum_3
        eq_kin = total % 260
        if eq_kin == 0: eq_kin = 260
        
        res = {
            "Eq_Kin": eq_kin,
            "Eq_Info": get_full_kin_data(eq_kin),
            "Logs": logs,
            "Total": total,
            "Sums": [sum_1, sum_2, sum_3]
        }
        
    except Exception as e:
        res = {"Error": str(e)}
    finally: conn.close()
    
    return res

# --- 9. 其他功能 ---
def calculate_equivalent_kin(kin):
    return {"Error": "請使用 calculate_equivalent_kin_new"}

def get_week_key_sentence(week_name):
    conn = get_db()
    try:
        if week_name:
            clean_week = week_name.strip()
            row = conn.execute("SELECT 關鍵句 FROM Maya_Week_Key WHERE 瑪雅週 = ?", (clean_week,)).fetchone()
            if row: return row['關鍵句']
            row = conn.execute(f"SELECT 關鍵句 FROM Maya_Week_Key WHERE 瑪雅週 LIKE ?", (f"%{clean_week}%",)).fetchone()
            if row: return row['關鍵句']
    except: pass
    finally: conn.close()
    return None

def get_heptad_prayer(path_name):
    conn = get_db()
    try:
        if path_name:
            clean = path_name.strip()
            row = conn.execute("SELECT 祈禱文 FROM Heptad_Prayer WHERE 七價路徑 = ?", (clean,)).fetchone()
            if row: return row['祈禱文']
            short_key = clean.split(' ')[0] 
            if short_key:
                row = conn.execute(f"SELECT 祈禱文 FROM Heptad_Prayer WHERE 七價路徑 LIKE ?", (f"{short_key}%",)).fetchone()
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
        if m_day and m_day.isdigit():
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
        conn.execute("CREATE TABLE IF NOT EXISTS Users (id INTEGER PRIMARY KEY AUTOINCREMENT, 姓名 TEXT, 生日 TEXT, KIN INTEGER, 主印記 TEXT)")
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

# 修改 kin_utils.py

def get_user_list():
    conn = get_db()
    try:
        # 確保表格存在
        conn.execute("CREATE TABLE IF NOT EXISTS Users (id INTEGER PRIMARY KEY AUTOINCREMENT, 姓名 TEXT, 生日 TEXT, KIN INTEGER, 主印記 TEXT)")
        
        # 讀取所有資料，即使表格是空的
        df = pd.read_sql("SELECT 姓名, 生日, KIN, 主印記 FROM Users", conn)
        
        # 增加一個檢查點，以防未來表格結構變更
        for col in ['姓名', '生日', 'KIN', '主印記']:
            if col not in df.columns:
                df[col] = None 
                
        return df[['姓名', '生日', 'KIN', '主印記']]
        
    except Exception as e:
        # 如果讀取或創建表格失敗，打印錯誤並返回空的 DataFrame
        print(f"Error accessing Users table: {e}")
        return pd.DataFrame()
    finally: conn.close()

def get_user_kin(name, df):
    r = df[df['姓名']==name]
    if not r.empty: return int(r.iloc[0]['KIN']), r.iloc[0]['生日']
    return None, None

def calculate_composite(k1, k2):
    r = (k1+k2)%260
    return 260 if r==0 else r

