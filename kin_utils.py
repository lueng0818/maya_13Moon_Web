import sqlite3
import datetime
import math
import base64
import os

DB_PATH = "13moon.db"

# --- 靜態資源對照表 ---
# 圖騰檔名 (1-20)
SEAL_FILES = {
    1: "01紅龍.jpg", 2: "02白風.jpg", 3: "03藍夜.jpg", 4: "04黃種子.jpg", 5: "05紅蛇.jpg",
    6: "06白世界橋.jpg", 7: "07藍手.jpg", 8: "08黃星星.jpg", 9: "09紅月.jpg", 10: "10白狗.jpg",
    11: "11藍猴.jpg", 12: "12黃人.jpg", 13: "13紅天行者.jpg", 14: "14白巫師.jpg", 15: "15藍鷹.jpg",
    16: "16黃戰士.jpg", 17: "17紅地球.jpg", 18: "18白鏡.jpg", 19: "19藍風暴.jpg", 20: "20黃太陽.jpg"
}

# 調性檔名 (1-13) - 對應 34.png 到 46.png
TONE_FILES = { i: f"瑪雅曆法圖騰-{i+33}.png" for i in range(1, 14) }

def get_db_connection():
    """建立資料庫連線"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # 讓回傳結果可用欄位名存取
    return conn

def get_img_as_base64(file_path):
    """將圖片轉為 base64 字串以便在 HTML 中顯示"""
    if not os.path.exists(file_path):
        return ""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return ""

def calculate_kin_from_date(input_date):
    """
    計算日期的 KIN (NS 1.36.1.1 = 2023-07-26 = KIN 1)
    這是簡易算法，不包含 0.0 Hunab Ku (2/29) 的複雜處理。
    """
    base_date = datetime.date(2023, 7, 26)
    base_kin = 1
    delta = input_date - base_date
    kin = (base_kin + delta.days) % 260
    if kin <= 0: kin += 260
    return kin

def get_kin_info(kin_num):
    """從資料庫撈取 KIN 的完整資料"""
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM Kin_Data WHERE KIN = ?", (kin_num,)).fetchone()
    except:
        row = None
    conn.close()
    
    if row:
        data = dict(row)
        # 補上圖片路徑
        s_num = data.get('圖騰數字', 1)
        t_num = data.get('調性數字', 1)
        data['seal_img'] = SEAL_FILES.get(s_num, '01紅龍.jpg')
        data['tone_img'] = TONE_FILES.get(t_num, '瑪雅曆法圖騰-34.png')
        
        # 處理波符圖片 (格式: 瑪雅曆20波符-01.png)
        wave_id = math.ceil(kin_num / 13)
        data['wave_id'] = wave_id
        data['wave_name'] = data.get('波符', '未知') # 從資料庫讀取波符名
        data['wave_img'] = f"瑪雅曆20波符-{str(wave_id).zfill(2)}.png"
        
        return data
    else:
        # 如果資料庫沒建好，回傳一個 Dummy Data 防止報錯
        return {
            "KIN": kin_num, "圖騰": "未知", "調性": "未知", "圖騰數字": 1, "調性數字": 1,
            "seal_img": "01紅龍.jpg", "tone_img": "瑪雅曆法圖騰-34.png", 
            "wave_name": "未知", "wave_img": "瑪雅曆20波符-01.png"
        }

def get_composite_kin(kin1, kin2):
    """計算合盤: (K1+K2) % 260"""
    total = kin1 + kin2
    comp = total % 260
    return 260 if comp == 0 else comp

def get_oracle_system(kin_num):
    """計算五大神諭 ID"""
    data = get_kin_info(kin_num)
    seal = data.get('圖騰數字', 1)
    tone = data.get('調性數字', 1)
    
    # 1. 主印記
    destiny = kin_num
    
    # 2. 支持 (Analog) = 19 - seal
    analog_seal = 19 - seal
    if analog_seal <= 0: analog_seal += 20
    # 反推支持 KIN (簡單版只算 seal)
    
    # 3. 擴展 (Antipode) = seal + 10
    antipode_seal = (seal + 10)
    if antipode_seal > 20: antipode_seal -= 20
    
    # 4. 推動 (Occult) -> seal+occult=21, tone+occult=14
    occult_seal = 21 - seal
    occult_tone = 14 - tone
    
    # 5. 引導 (Guide) - 這裡簡化為與主印記相同 (完整版需查表)
    guide_seal = seal 
    
    return {
        "destiny": {"seal": seal, "tone": tone, "kin": destiny},
        "analog": {"seal": analog_seal, "tone": tone},
        "antipode": {"seal": antipode_seal, "tone": tone},
        "occult": {"seal": occult_seal, "tone": occult_tone},
        "guide": {"seal": guide_seal, "tone": tone}
    }

def calculate_life_path(birth_date, view_age_limit=104):
    """
    計算流年路徑 (支援無限歲數)
    公式: 每年 KIN + 105
    """
    base_kin = calculate_kin_from_date(birth_date)
    path_data = []
    
    for age in range(view_age_limit + 1):
        target_year = birth_date.year + age
        
        # 流年公式
        delta_kin = (age * 105) % 260
        current_kin = (base_kin + delta_kin) % 260
        if current_kin == 0: current_kin = 260
        
        info = get_kin_info(current_kin)
        
        # 52年週期的城堡顏色 (紅白藍黃)
        cycle_age = age % 52
        cycle_round = (age // 52) + 1
        
        if 0 <= cycle_age < 13: castle_color = "#fff0f0" # 紅 (淡色背景)
        elif 13 <= cycle_age < 26: castle_color = "#f8f8f8" # 白
        elif 26 <= cycle_age < 39: castle_color = "#f0f8ff" # 藍
        else: castle_color = "#fffff0" # 黃
        
        # 邊框顏色
        if 0 <= cycle_age < 13: border_color = "#ffaaaa"
        elif 13 <= cycle_age < 26: border_color = "#dddddd"
        elif 26 <= cycle_age < 39: border_color = "#aaaaff"
        else: border_color = "#eeeebb"

        path_data.append({
            "Age": age,
            "Cycle_Age": cycle_age,
            "Cycle_Round": cycle_round,
            "Year": target_year,
            "KIN": current_kin,
            "Label": f"{info['調性']}{info['圖騰']}",
            "Seal_Img": info['seal_img'],
            "Wave": info['wave_name'],
            "BG_Color": castle_color,
            "Border_Color": border_color
        })
            
    return path_data