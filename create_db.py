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
    
    # 1. 匯入星際年 (Star_Years) - 關鍵修正
    f_star = find_file("星際年")
    if f_star:
        print(f"🔹 匯入星際年: {os.path.basename(f_star)}")
        df = read_csv_robust(f_star)
        if df is not None:
            df.columns = [c.strip() for c in df.columns]
            # 確保起始年是數字
            if '起始年' in df.columns:
                df['起始年'] = pd.to_numeric(df['起始年'], errors='coerce').fillna(0).astype(int)
                df.to_sql("Star_Years", conn, if_exists="replace", index=False)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_star_year ON Star_Years (起始年)")

    # 2. 其他參照表
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
                if table_name == "Calendar_Converter" and '國曆生日' not in df.columns:
                    df.rename(columns={df.columns[0]: '國曆生日'}, inplace=True)
                if 'KIN' in df.columns:
                    df['KIN'] = pd.to_numeric(df['KIN'], errors='coerce').fillna(0).astype(int)
                
                df.to_sql(table_name, conn, if_exists="replace", index=False)
                if index_col in df.columns:
                    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name.lower()} ON {table_name} ({index_col})")

    # 3. 核心資料
    for keyword, table_name in [("卓爾金曆", "Kin_Data"), ("矩陣", "Matrix_Data"), ("銀河易經", "IChing")]:
        f = find_file(keyword)
        if f:
            if keyword == "矩陣": df = process_matrix_csv(f)
            else: df = read_csv_robust(f)
            if df is not None:
                if keyword != "矩陣": df.columns = [str(c).replace('\n', '').strip() for c in df.columns]
                df.to_sql(table_name, conn, if_exists="replace", index=False)

    # 4. 通訊錄
    print("🔹 建立 Users 表格...")
    conn.execute("CREATE TABLE IF NOT EXISTS Users (id INTEGER PRIMARY KEY AUTOINCREMENT, 姓名 TEXT, 生日 TEXT, KIN INTEGER, 主印記 TEXT)")
    f_user = find_file("通訊錄")
    if f_user:
        df = read_csv_robust(f_user)
        if df is not None:
            try:
                if '名字' in df.columns: df['姓名'] = df['名字']
                if '出生年' in df.columns:
                    df['生日'] = df.apply(lambda x: f"{int(x['出生年'])}-{int(x['出生月'])}-{int(x['出生日'])}", axis=1)
                valid = [c for c in ['姓名', '生日', 'KIN', '主印記'] if c in df.columns]
                if valid: df[valid].to_sql("Users", conn, if_exists="append", index=False)
            except: pass

    conn.close()
    print("🎉 資料庫建置完成！")

if __name__ == "__main__":
    init_db()
