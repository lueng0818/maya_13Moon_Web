import sqlite3
import pandas as pd
import os
import glob

DB_NAME = "13moon.db"
DATA_DIR = "data"

def find_file(keyword):
    if not os.path.exists(DATA_DIR): return None
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    for f in files:
        if keyword in os.path.basename(f): return f
    return None

def read_csv_robust(file_path, **kwargs):
    encodings = ['utf-8', 'cp950', 'big5', 'utf-8-sig', 'gbk']
    for enc in encodings:
        try: return pd.read_csv(file_path, encoding=enc, **kwargs)
        except: continue
    return None

def init_db():
    print(f"🚀 開始建置資料庫: {DB_NAME}...")
    conn = sqlite3.connect(DB_NAME)
    
    # 1. 參照表設定
    # 格式: (CSV關鍵字, 資料庫表名, 索引欄位)
    tables_config = [
        ("kin_start_year", "Kin_Start", '年份'), 
        ("month_day_accum", "Month_Accum", '月份'), 
        ("kin_basic_info", "Kin_Basic", 'KIN'), 
        ("PSI印記對照表", "PSI_Bank", '月日'),
        ("女神印記", "Goddess_Seal", 'KIN'),
        ("對應瑪雅生日", "Maya_1328_Map", "月日"),
        ("七價路徑對應祈禱文", "Heptad_Prayer", "七價路徑"),
        ("瑪亞週關鍵句", "Maya_Week_Key", "瑪雅週"),
        # ✨ 新增：圖騰對應表 (星際原型、BMU、行星、流...)
        ("圖騰對應表", "Seal_Info_Map", "圖騰")
    ]

    for kw, table, idx in tables_config:
        f = find_file(kw)
        if f:
            print(f"處理檔案: {f} -> 表格: {table}")
            df = read_csv_robust(f)
            if df is not None:
                # 清理欄位名稱
                df.columns = [str(c).strip() for c in df.columns]
                
                # 數值欄位轉型
                if 'PSI印記' in df.columns:
                    df['PSI印記'] = pd.to_numeric(df['PSI印記'], errors='coerce').fillna(0).astype(int)
                if 'KIN' in df.columns: 
                    df['KIN'] = pd.to_numeric(df['KIN'], errors='coerce').fillna(0).astype(int)
                
                # 七價路徑特殊處理
                if table == "Heptad_Prayer" and '七價路徑' in df.columns:
                     df['七價路徑'] = df['七價路徑'].astype(str).str.replace('\n', ' ').str.strip()

                df.to_sql(table, conn, if_exists="replace", index=False)
                if idx in df.columns: 
                    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table} ON {table} ({idx})")
        else:
            print(f"⚠️ 找不到關鍵字 '{kw}' 的 CSV 檔案，將跳過建立 {table}！")

    # 2. 核心資料
    for kw, table in [("卓爾金曆", "Kin_Data"), ("矩陣", "Matrix_Data"), ("銀河易經", "IChing"), ("星際年", "Star_Years")]:
        f = find_file(kw)
        if f:
            if kw == "矩陣": 
                try:
                    df = read_csv_robust(f, header=[0, 1])
                    new_cols = []
                    last_top = "Unknown"
                    for top, bottom in df.columns:
                        if "Unnamed" not in str(top): last_top = str(top).strip()
                        clean_bottom = str(bottom).replace('\n', '').strip()
                        new_cols.append(f"{last_top}_{clean_bottom}")
                    final_cols = []
                    counts = {}
                    for col in new_cols:
                        if col in counts:
                            counts[col] += 1
                            final_cols.append(f"{col}_{counts[col]}")
                        else:
                            counts[col] = 1
                            final_cols.append(col)
                    df.columns = final_cols
                except: df = None
            else: 
                df = read_csv_robust(f)
            
            if df is not None:
                if kw != "矩陣": df.columns = [str(c).strip() for c in df.columns]
                df.to_sql(table, conn, if_exists="replace", index=False)
                
    conn.execute("CREATE TABLE IF NOT EXISTS Users (id INTEGER PRIMARY KEY AUTOINCREMENT, 姓名 TEXT, 生日 TEXT, KIN INTEGER, 主印記 TEXT)")
    conn.close()
    print("🎉 資料庫建置完成！")

if __name__ == "__main__":
    init_db()
