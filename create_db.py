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
        df.columns = new_cols
        return df
    except: return None

def init_db():
    print(f"🚀 開始建置資料庫: {DB_NAME}...")
    if os.path.exists(DB_NAME): os.remove(DB_NAME)
    conn = sqlite3.connect(DB_NAME)
    
    # ----------------------------------------------------
    # 1. 新增：計算用查表資料 (您的新需求)
    # ----------------------------------------------------
    f_start = find_file("kin_start_year")
    if f_start:
        print(f"🔹 匯入起始年表: {os.path.basename(f_start)}")
        df = read_csv_robust(f_start)
        if df is not None: df.to_sql("Kin_Start", conn, if_exists="replace", index=False)

    f_accum = find_file("month_day_accum")
    if f_accum:
        print(f"🔹 匯入月累積表: {os.path.basename(f_accum)}")
        df = read_csv_robust(f_accum)
        if df is not None: df.to_sql("Month_Accum", conn, if_exists="replace", index=False)

    f_basic = find_file("kin_basic_info")
    if f_basic:
        print(f"🔹 匯入基礎資訊: {os.path.basename(f_basic)}")
        df = read_csv_robust(f_basic)
        if df is not None: df.to_sql("Kin_Basic", conn, if_exists="replace", index=False)

    # ----------------------------------------------------
    # 2. 原有核心資料 (保持不變)
    # ----------------------------------------------------
    f_kin = find_file("卓爾金曆")
    if f_kin:
        print(f"🔹 匯入卓爾金曆: {os.path.basename(f_kin)}")
        df = read_csv_robust(f_kin)
        if df is not None:
            df.columns = [c.replace('\n', '').strip() for c in df.columns]
            if 'KIN' in df.columns:
                df['KIN'] = pd.to_numeric(df['KIN'], errors='coerce').fillna(0).astype(int)
                df.to_sql("Kin_Data", conn, if_exists="replace", index=False)

    f_matrix = find_file("矩陣")
    if f_matrix:
        print(f"🔹 匯入矩陣: {os.path.basename(f_matrix)}")
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
