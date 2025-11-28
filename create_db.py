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
    
    # ==========================================
    # 1. 一般參照表 (標準 CSV)
    # ==========================================
    tables_config = [
        ("kin_start_year", "Kin_Start", '年份'), 
        ("month_day_accum", "Month_Accum", '月份'), 
        ("kin_basic_info", "Kin_Basic", 'KIN'), 
        ("PSI印記對照表", "PSI_Bank", '月日'),
        ("女神印記", "Goddess_Seal", 'KIN'),
        ("對應瑪雅生日", "Maya_1328_Map", "月日"),
        ("瑪亞週關鍵句", "Maya_Week_Key", "瑪雅週"),
        ("七價路徑對應祈禱文", "Heptad_Prayer", "七價路徑"),
        ("圖騰對應表", "Seal_Info_Map", "圖騰"),
        # ✨ 新增：瑪雅生日對時間矩陣對照表
        ("瑪雅生日對時間矩陣對照表", "Maya_Time_Map", "瑪雅生日")
    ]

    for kw, table, idx in tables_config:
        f = find_file(kw)
        if f:
            print(f"處理檔案: {f} -> 表格: {table}")
            df = read_csv_robust(f)
            if df is not None:
                df.columns = [str(c).strip() for c in df.columns]
                
                # 數值欄位轉型
                for col in ['PSI印記', 'KIN']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                
                # 七價路徑特殊處理
                if table == "Heptad_Prayer" and '七價路徑' in df.columns:
                     df['七價路徑'] = df['七價路徑'].astype(str).str.replace(r'\n', ' ', regex=True).str.strip()

                df.to_sql(table, conn, if_exists="replace", index=False)
                if idx in df.columns: 
                    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table} ON {table} ({idx})")
        else:
            print(f"⚠️ 找不到關鍵字 '{kw}' 的 CSV！")

    # ==========================================
    # 2. 矩陣檔案特殊處理 (Time, Space, Synchronic)
    # ==========================================
    # 定義: (關鍵字, 表格名, 位置欄位名, 值欄位名)
    matrix_files = [
        ("Time_Matrix", "Matrix_Time", "矩陣位置", "KIN"),
        ("Space_Matrix", "Matrix_Space", "矩陣位置", "KIN"),
        ("Synchronic_Matrix", "Matrix_Sync", "矩陣位置", "KIN")
    ]
    
    for kw, table, pos_col_hint, val_col_hint in matrix_files:
        f = find_file(kw)
        if f:
            print(f"處理矩陣: {f} -> {table}")
            try:
                # 矩陣 CSV 通常第 2 行才是標題 (header=1)
                df = read_csv_robust(f, header=1)
                
                # 尋找正確的欄位名稱 (避免空白干擾)
                pos_col = next((c for c in df.columns if pos_col_hint in str(c)), None)
                val_col = next((c for c in df.columns if val_col_hint in str(c)), None)
                
                if pos_col and val_col:
                    df_clean = df[[pos_col, val_col]].copy()
                    df_clean.columns = ["Position", "Value"] # 統一欄位名稱
                    
                    df_clean['Value'] = pd.to_numeric(df_clean['Value'], errors='coerce').fillna(0).astype(int)
                    df_clean['Position'] = df_clean['Position'].astype(str).str.strip()
                    
                    df_clean.to_sql(table, conn, if_exists="replace", index=False)
                    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_pos ON {table} (Position)")
                    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_val ON {table} (Value)")
            except Exception as e:
                print(f"矩陣匯入錯誤 {table}: {e}")

    # 3. 核心資料 (其他)
    for kw, table in [("卓爾金曆", "Kin_Data"), ("矩陣", "Matrix_Data"), ("銀河易經", "IChing"), ("星際年", "Star_Years")]:
        f = find_file(kw)
        if f and kw != "矩陣": # 矩陣已在上一步處理，這裡跳過舊邏輯
             df = read_csv_robust(f)
             if df is not None:
                df.columns = [str(c).strip() for c in df.columns]
                df.to_sql(table, conn, if_exists="replace", index=False)
                
    conn.execute("CREATE TABLE IF NOT EXISTS Users (id INTEGER PRIMARY KEY AUTOINCREMENT, 姓名 TEXT, 生日 TEXT, KIN INTEGER, 主印記 TEXT)")
    conn.close()
    print("🎉 資料庫建置完成！")

if __name__ == "__main__":
    init_db()
