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
    try:
        df = read_csv_robust(file_path, header=[0, 1])
        if df is None: return None
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
        return df
    except: return None

def init_db():
    print(f"🚀 開始建置資料庫: {DB_NAME}...")
    if os.path.exists(DB_NAME): os.remove(DB_NAME)
    conn = sqlite3.connect(DB_NAME)
    
    # --- 1. 參照表 ---
    for kw, table, idx in [("kin_start_year", "Kin_Start", '年份'), ("month_day_accum", "Month_Accum", '月份'), ("kin_basic_info", "Kin_Basic", 'KIN'), ("PSI印記對照表", "PSI_Bank", '月日'), ("女神印記", "Goddess_Seal", 'KIN')]:
        f = find_file(kw)
        if f:
            print(f"🔹 匯入 {table}: {os.path.basename(f)}")
            df = read_csv_robust(f)
            if df is not None:
                df.columns = [c.strip() for c in df.columns]
                if 'KIN' in df.columns: df['KIN'] = pd.to_numeric(df['KIN'], errors='coerce').fillna(0).astype(int)
                df.to_sql(table, conn, if_exists="replace", index=False)
                if idx in df.columns: conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table} ON {table} ({idx})")

    # --- 2. 核心資料 ---
    for kw, table in [("卓爾金曆", "Kin_Data"), ("矩陣", "Matrix_Data"), ("銀河易經", "IChing")]:
        f = find_file(kw)
        if f:
            print(f"🔹 匯入 {table}: {os.path.basename(f)}")
            if kw == "矩陣": df = process_matrix_csv(f)
            else: df = read_csv_robust(f)
            
            if df is not None:
                if kw != "矩陣": df.columns = [c.strip() for c in df.columns]
                df.to_sql(table, conn, if_exists="replace", index=False)

    # --- 3. 通訊錄 (Users) - 特殊處理 Schema ---
    print("🔹 重建 Users 表格...")
    conn.execute("DROP TABLE IF EXISTS Users")
    conn.execute("""
        CREATE TABLE Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            姓名 TEXT NOT NULL,
            生日 TEXT NOT NULL,
            KIN INTEGER,
            主印記 TEXT
        )
    """)
    
    f_user = find_file("通訊錄")
    if f_user:
        df = read_csv_robust(f_user)
        if df is not None:
            try:
                # 欄位對應: 名字 -> 姓名
                if '名字' in df.columns: df['姓名'] = df['名字']
                elif 'Name' in df.columns: df['姓名'] = df['Name']
                
                # 處理生日
                if '出生年' in df.columns and '出生月' in df.columns and '出生日' in df.columns:
                    df['生日'] = df.apply(lambda x: f"{int(x['出生年'])}-{int(x['出生月'])}-{int(x['出生日'])}", axis=1)
                
                # 確保欄位存在
                for col in ['姓名', '生日', 'KIN', '主印記']:
                    if col not in df.columns: df[col] = None
                
                # 寫入
                df[['姓名', '生日', 'KIN', '主印記']].to_sql("Users", conn, if_exists="append", index=False)
                print("   ✅ Users 資料匯入成功")
            except Exception as e:
                print(f"   ⚠️ 通訊錄匯入部分失敗 (但表格已建立): {e}")

    conn.close()
    print("🎉 資料庫建置完成！")

if __name__ == "__main__":
    init_db()
