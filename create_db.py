import sqlite3
import pandas as pd
import os
import glob

DB_NAME = "13moon.db"
DATA_DIR = "data"

def find_file(keyword):
    """模糊搜尋檔案 (解決檔名不精確問題)"""
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
    
    # 建立計算用表 (KIN_START, MONTH_ACCUM, KIN_BASIC, PSI, GODDESS)
    for keyword, table_name, index_col in [("kin_start_year", "Kin_Start", '年份'), ("month_day_accum", "Month_Accum", '月份'), ("kin_basic_info", "Kin_Basic", 'KIN'), ("PSI印記對照表", "PSI_Bank", '月日'), ("女神印記", "Goddess_Seal", 'KIN')]:
        f = find_file(keyword)
        if f:
            df = read_csv_robust(f)
            if df is not None: 
                df.columns = [c.strip() for c in df.columns]
                if 'KIN' in df.columns:
                    df['KIN'] = pd.to_numeric(df['KIN'], errors='coerce').fillna(0).astype(int)
                df.to_sql(table_name, conn, if_exists="replace", index=False)
    
    # 建立人員生日管理表 (Users - 新增欄位，確保可以寫入)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                姓名 TEXT NOT NULL,
                生日 TEXT NOT NULL,
                KIN INTEGER,
                主印記 TEXT
            )""")
        
        # 匯入原有通訊錄資料 (如果存在)
        f_user = find_file("通訊錄")
        if f_user:
            df = read_csv_robust(f_user)
            if df is not None:
                 # 這裡需要一個強大的邏輯來計算 KIN，但暫時只匯入姓名和生日
                 # 網站 runtime 會重新計算 KIN
                df_subset = df.rename(columns={'名字': '姓名'}).filter(['姓名', '出生年', '出生月', '出生日'])
                df_subset['生日'] = df_subset.apply(lambda row: f"{row['出生年']}-{row['出生月']}-{row['出生日']}", axis=1)
                
                for _, row in df_subset.iterrows():
                    conn.execute("INSERT INTO Users (姓名, 生日) VALUES (?, ?)", (row['姓名'], row['生日']))
                conn.commit()

    except Exception as e:
        print(f"❌ Users 表格建立失敗: {e}")

    # 核心資料 (卓爾金曆, 矩陣, 易經)
    for keyword, table_name in [("卓爾金曆", "Kin_Data"), ("矩陣", "Matrix_Data"), ("銀河易經", "IChing")]:
        f = find_file(keyword)
        if f:
            if keyword == "矩陣": df = process_matrix_csv(f)
            else: df = read_csv_robust(f)
            if df is not None:
                if keyword != "矩陣": df.columns = [c.replace('\n', '').strip() for c in df.columns]
                df.to_sql(table_name, conn, if_exists="replace", index=False)

    conn.close()
    print("🎉 資料庫建置完成！")

if __name__ == "__main__":
    init_db()
