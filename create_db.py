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
        df.columns = new_cols
        return df
    except: return None

def init_db():
    print(f"🚀 開始建置資料庫: {DB_NAME}...")
    if os.path.exists(DB_NAME): os.remove(DB_NAME)
    conn = sqlite3.connect(DB_NAME)
    
    # ------------------------------------------------
    # 1. 新增：PSI 對照表 (NEW)
    # ------------------------------------------------
    f_psi = find_file("PSI印記對照表")
    if f_psi:
        print(f"🔹 匯入 PSI 對照表: {os.path.basename(f_psi)}")
        df = read_csv_robust(f_psi)
        if df is not None:
            # 清理欄位
            df.columns = [c.strip() for c in df.columns]
            # 確保 PSI 印記是整數
            if 'PSI印記' in df.columns:
                df['PSI印記'] = pd.to_numeric(df['PSI印記'], errors='coerce').fillna(0).astype(int)
            # 建立查詢索引 (用 '月日' 欄位)
            df.to_sql("PSI_Bank", conn, if_exists="replace", index=False)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_psi_date ON PSI_Bank (月日)")

    # ------------------------------------------------
    # 2. 計算用表
    # ------------------------------------------------
    f_start = find_file("kin_start_year")
    if f_start:
        df = read_csv_robust(f_start)
        if df is not None: df.to_sql("Kin_Start", conn, if_exists="replace", index=False)

    f_accum = find_file("month_day_accum")
    if f_accum:
        df = read_csv_robust(f_accum)
        if df is not None: df.to_sql("Month_Accum", conn, if_exists="replace", index=False)

    f_basic = find_file("kin_basic_info")
    if f_basic:
        df = read_csv_robust(f_basic)
        if df is not None: df.to_sql("Kin_Basic", conn, if_exists="replace", index=False)

    # ------------------------------------------------
    # 3. 核心資料
    # ------------------------------------------------
    f_kin = find_file("卓爾金曆")
    if f_kin:
        df = read_csv_robust(f_kin)
        if df is not None:
            df.columns = [c.replace('\n', '').strip() for c in df.columns]
            if 'KIN' in df.columns:
                df['KIN'] = pd.to_numeric(df['KIN'], errors='coerce').fillna(0).astype(int)
                df.to_sql("Kin_Data", conn, if_exists="replace", index=False)

    f_matrix = find_file("矩陣")
    if f_matrix:
        df = process_matrix_csv(f_matrix)
        if df is not None: df.to_sql("Matrix_Data", conn, if_exists="replace", index=False)

    f_iching = find_file("銀河易經")
    if f_iching:
        df = read_csv_robust(f_iching)
        if df is not None: df.to_sql("IChing", conn, if_exists="replace", index=False)

    f_user = find_file("通訊錄")
    if f_user:
        df = read_csv_robust(f_user)
        if df is not None:
            cols = [c for c in df.columns if c.strip() in ['編號','名字','出生年','出生月','出生日','KIN']]
            if cols: df[cols].to_sql("Users", conn, if_exists="replace", index=False)

    conn.close()
    print("🎉 資料庫建置完成！")

if __name__ == "__main__":
    init_db()
