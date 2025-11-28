import sqlite3
import pandas as pd
import os
import glob

DB_NAME = "13moon.db"
DATA_DIR = "data"

def find_file(keyword):
    """模糊搜尋檔案"""
    if not os.path.exists(DATA_DIR): return None
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    for f in files:
        if keyword in os.path.basename(f): return f
    return None

def read_csv_robust(file_path, **kwargs):
    """萬能編碼讀取"""
    encodings = ['utf-8', 'cp950', 'big5', 'utf-8-sig', 'gbk']
    for enc in encodings:
        try:
            return pd.read_csv(file_path, encoding=enc, **kwargs)
        except: continue
    return None

def process_matrix_csv(file_path):
    """處理矩陣表 (雙層標題與去重複欄位)"""
    try:
        df = read_csv_robust(file_path, header=[0, 1])
        if df is None: return None
        new_columns = []
        last_top = "Unknown"
        for top, bottom in df.columns:
            if "Unnamed" not in str(top): last_top = str(top).strip()
            clean_bottom = str(bottom).replace('\n', '').strip()
            new_columns.append(f"{last_top}_{clean_bottom}")
        
        # 去重複
        final_cols = []
        counts = {}
        for col in new_columns:
            if col in counts:
                counts[col] += 1
                final_cols.append(f"{col}_{counts[col]}")
            else:
                counts[col] = 1
                final_cols.append(col)
        df.columns = final_cols
        return df
    except: return None

def init_db():
    print(f"🚀 開始建置資料庫: {DB_NAME}...")
    if os.path.exists(DB_NAME): os.remove(DB_NAME)
    conn = sqlite3.connect(DB_NAME)
    
    # 1. 計算與參照表
    ref_tables = [
        ("kin_start_year", "Kin_Start", '年份'), 
        ("month_day_accum", "Month_Accum", '月份'), 
        ("kin_basic_info", "Kin_Basic", 'KIN'), 
        ("PSI印記對照表", "PSI_Bank", '月日'), 
        ("女神印記", "Goddess_Seal", 'KIN'),
        ("對應瑪雅生日", "Calendar_Converter", '國曆生日'),
        ("七價路徑對應祈禱文", "Heptad_Prayer", '七價路徑'),
        ("瑪亞週關鍵句", "Maya_Week_Key", '瑪雅週'),
        ("八度音階", "Octave_Scale", '八度音符')
    ]

    for keyword, table_name, index_col in ref_tables:
        f = find_file(keyword)
        if f:
            print(f"🔹 匯入 {table_name}: {os.path.basename(f)}")
            df = read_csv_robust(f)
            if df is not None: 
                df.columns = [str(c).strip() for c in df.columns]
                if 'KIN' in df.columns:
                    df['KIN'] = pd.to_numeric(df['KIN'], errors='coerce').fillna(0).astype(int)
                
                df.to_sql(table_name, conn, if_exists="replace", index=False)
                if index_col in df.columns:
                    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name.lower()} ON {table_name} ({index_col})")

    # 2. 核心資料 (矩陣、易經、卓爾金)
    for keyword, table_name in [("卓爾金曆", "Kin_Data"), ("矩陣", "Matrix_Data"), ("銀河易經", "IChing")]:
        f = find_file(keyword)
        if f:
            print(f"🔹 匯入 {table_name}: {os.path.basename(f)}")
            if keyword == "矩陣": df = process_matrix_csv(f)
            else: df = read_csv_robust(f)
            
            if df is not None:
                if keyword != "矩陣": df.columns = [str(c).replace('\n', '').strip() for c in df.columns]
                df.to_sql(table_name, conn, if_exists="replace", index=False)

    # 3. 國王預言棋盤 (NEW)
    f_king = find_file("國王預言棋盤")
    if f_king:
        print(f"🔹 匯入國王棋盤: {os.path.basename(f_king)}")
        # 棋盤結構較特殊，直接匯入不做太多處理，供前端直接顯示
        df = read_csv_robust(f_king)
        if df is not None: df.to_sql("King_Prophecy", conn, if_exists="replace", index=False)

    # 4. 通訊錄 (Users)
    print("🔹 建立 Users 表格...")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            姓名 TEXT,
            生日 TEXT,
            KIN INTEGER,
            主印記 TEXT
        )
    """)
    
    f_user = find_file("通訊錄")
    if f_user:
        df = read_csv_robust(f_user)
        if df is not None:
            try:
                col_map = {'名字': '姓名', 'Name': '姓名'}
                df.rename(columns=col_map, inplace=True)
                required_cols = ['出生年', '出生月', '出生日']
                if '姓名' in df.columns and all(c in df.columns for c in required_cols):
                    for c in required_cols: df[c] = pd.to_numeric(df[c], errors='coerce')
                    df_clean = df.dropna(subset=required_cols).copy()
                    df_clean['生日'] = df_clean.apply(lambda x: f"{int(x['出生年'])}-{int(x['出生月'])}-{int(x['出生日'])}", axis=1)
                    
                    valid_cols = ['姓名', '生日', 'KIN', '主印記']
                    for vc in valid_cols: 
                        if vc not in df_clean.columns: df_clean[vc] = None
                    df_clean[valid_cols].to_sql("Users", conn, if_exists="append", index=False)
            except: pass

    conn.close()
    print("🎉 資料庫建置完成！")

if __name__ == "__main__":
    init_db()
