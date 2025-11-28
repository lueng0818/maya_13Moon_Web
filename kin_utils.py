# --- 在 kin_utils.py 中新增此函數 ---

def get_telektonon_info(kin, maya_cal):
    """
    獲取國王預言棋盤資訊
    輸入: kin (int), maya_cal (dict - from get_maya_calendar_info)
    """
    conn = get_db()
    result = {
        "Crystal_Battery": "-", 
        "Warrior_Cube": "-",
        "Turtle_Day": "-",
        "Turtle_Color": "-",
        "Circuit": "-",
        "Rune": "-"
    }
    
    try:
        # 1. 水晶柱 (對應調性)
        tone_id = (kin - 1) % 13 + 1
        result['Crystal_Battery'] = f"調性 {tone_id} ({TONE_NAMES[tone_id]})"
        
        # 2. 戰士立方體 (對應圖騰)
        seal_id = (kin - 1) % 20 + 1
        result['Warrior_Cube'] = f"圖騰 {seal_id} ({SEALS_NAMES[seal_id]})"
        
        # 3. 烏龜日 (對應瑪雅日數字)
        maya_day_str = maya_cal.get('Maya_Date', '').split('.')[-1] # 取出日期部分 "13.20" -> "20"
        if maya_day_str and maya_day_str != '-':
            day_num = int(maya_day_str)
            
            # 查詢烏龜表 (Green, White, Yellow)
            # 邏輯：通常依據瑪雅日的不同區間或屬性來對應
            # 這裡簡化為查詢所有烏龜表，看哪一張表有這個天數的特殊說明
            
            # 綠烏龜 (Green Turtle)
            green = conn.execute("SELECT 屬宮, 說明 FROM Green_Turtle_Day WHERE 第幾天 = ?", (day_num,)).fetchone()
            if green:
                result['Turtle_Day'] = f"第 {day_num} 天"
                result['Turtle_Color'] = "綠烏龜"
                result['Turtle_Desc'] = f"{green['屬宮']} | {green['說明']}"
            
            # 白烏龜 (White Turtle)
            white = conn.execute("SELECT 位置, 說明 FROM White_Turtle_Day WHERE 第幾天 = ?", (day_num,)).fetchone()
            if white:
                result['Turtle_Day'] = f"第 {day_num} 天"
                result['Turtle_Color'] = "白烏龜"
                result['Turtle_Desc'] = f"位置 {white['位置']} | {white['說明']}"

            # 黃烏龜 (Yellow Turtle)
            yellow = conn.execute("SELECT 盧恩符文, 說明, 符文意涵 FROM Yellow_Turtle_Day WHERE 第幾天 = ?", (day_num,)).fetchone()
            if yellow:
                result['Turtle_Day'] = f"第 {day_num} 天"
                result['Turtle_Color'] = "黃烏龜"
                result['Turtle_Desc'] = f"{yellow['盧恩符文']} | {yellow['說明']}"
                result['Rune'] = yellow['符文意涵']

        # 4. 電路 (對應七價路徑)
        heptad = maya_cal.get('Heptad_Path', '')
        # 嘗試從七價路徑表反查電路，或直接從 Heptad_Gate_Path 表查
        if heptad:
             # 這裡做簡單處理，若有更詳細對照表可再精細化
             pass

    except Exception as e:
        print(f"Telektonon Error: {e}")
        
    conn.close()
    return result
