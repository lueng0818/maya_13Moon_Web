# --- 在 kin_utils.py 中更新此函數 ---

def get_maya_calendar_info(date_obj):
    """
    根據國曆日期查詢完整的瑪雅曆法資訊
    """
    conn = get_db()
    result = {
        "Maya_Date": "-",      # 完整日期 (例如 13.20)
        "Maya_Month": "-",     # 月份名稱 (例如 宇宙龜之月)
        "Maya_Day": "-",       # 日期 (例如 20)
        "Maya_Week": "-",      # 瑪雅週 (例如 藍色蛻變之週)
        "Heptad_Path": "-",    # 七價路徑
        "Plasma": "-",         # 等離子日
        "Solar_Year": "-",     # 星際年 (例如 NS 1.36)
        "Status": "查無資料"
    }
    
    try:
        query_date_str = date_obj.strftime('%Y-%m-%d')
        
        # 查詢 Calendar_Converter 表
        # 假設 CSV 欄位名稱為: 國曆生日, 瑪雅生日, 瑪雅月, 瑪雅週, 七價路徑, 等離子日...
        # 注意：對應瑪雅生日.csv 可能沒有「星際年」欄位，通常星際年是固定的 (7/26 切換)
        # 但我們可以嘗試從 kin_start_year 推算或看有無其他表
        
        row = conn.execute("SELECT * FROM Calendar_Converter WHERE 國曆生日 = ?", (query_date_str,)).fetchone()
        
        if row:
            result['Maya_Date'] = row.get('瑪雅生日', '-')
            result['Maya_Month'] = row.get('瑪雅月', '-')
            result['Maya_Week'] = row.get('瑪雅週', '-')
            result['Heptad_Path'] = row.get('七價路徑', '-')
            result['Plasma'] = row.get('等離子日', '-')
            
            # 嘗試解析日期數字 (從 13.20 取出 20)
            try:
                result['Maya_Day'] = result['Maya_Date'].split('.')[1]
            except:
                result['Maya_Day'] = "-"
                
            # 推算星際年 (Solar Year)
            # 規則: 每年 7/26 起為新的一年
            # 例如: 2023/07/26 ~ 2024/07/24 為 NS 1.36
            # 這部分可以寫死或查表，這裡先用簡單邏輯
            year = date_obj.year
            if (date_obj.month < 7) or (date_obj.month == 7 and date_obj.day < 26):
                year -= 1
            # 這裡僅作示意，若有星際年對照表可更精準
            result['Solar_Year'] = f"NS 1.{year-1987+30}" # 簡易推算，建議查表
            
            result['Status'] = "查詢成功"
        
    except Exception as e:
        result['Status'] = f"Error: {e}"
        
    conn.close()
    return result
