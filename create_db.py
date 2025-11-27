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
    """萬能編碼讀取 (解決中文亂碼問題)"""
    encodings = ['utf-8', 'cp950', 'big5', 'utf-8-sig', 'gbk']
    for enc in encodings:
        try:
            return pd.read_csv(file_path, encoding=enc, **kwargs)
        except: continue
    return None

def process_matrix_csv(file_path):
    """處理矩陣表 (去重複欄位)"""
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
    # 刪除舊檔，強制重建
    if os.path.exists(DB_NAME): os.remove(DB_NAME)
    conn = sqlite3.connect(DB_NAME)
    
    # ----------------------------------------------------
    # 1. 核心計算用表 (KIN_START, MONTH_ACCUM)
    # ----------------------------------------------------
    for keyword, table_name, index_col in [("kin_start_year", "Kin_Start", '年份'), ("month_day_accum", "Month_Accum", '月份'), ("kin_basic_info", "Kin_Basic", 'KIN')]:
        f = find_file(keyword)
        if f:
            print(f"🔹 匯入 {table_name}: {os.path.basename(f)}")
            df = read_csv_robust(f)
            if df is not None: 
                # 清理欄位名並匯入
                df.columns = [c.strip() for c in df.columns]
                df.to_sql(table_name, conn, if_exists="replace", index=False)
                if index_col in df.columns:
                    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name.lower()} ON {table_name} ({index_col})")
            else:
                print(f"❌ 警告：{table_name} 讀取失敗或為空。")
        else:
            print(f"❌ 警告：找不到 {keyword}.csv，將影響 KIN 查表功能。")

    # ----------------------------------------------------
    # 2. 其他參照表 (PSI, MATRIX, I Ching)
    # ----------------------------------------------------
    
    f_psi = find_file("PSI印記對照表")
    if f_psi:
        print(f"🔹 匯入 PSI 對照表: {os.path.basename(f_psi)}")
        df = read_csv_robust(f_psi)
        if df is not None:
            df.columns = [c.strip() for c in df.columns]
            df.to_sql("PSI_Bank", conn, if_exists="replace", index=False)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_psi_date ON PSI_Bank (月日)")

    # 卓爾金曆主表
    f_kin = find_file("卓爾金曆")
    if f_kin:
        df = read_csv_robust(f_kin)
        if df is not None:
            df.columns = [c.replace('\n', '').strip() for c in df.columns]
            if 'KIN' in df.columns: df.to_sql("Kin_Data", conn, if_exists="replace", index=False)

    # 矩陣主表
    f_matrix = find_file("矩陣")
    if f_matrix:
        df = process_matrix_csv(f_matrix)
        if df is not None: df.to_sql("Matrix_Data", conn, if_exists="replace", index=False)

    f_iching = find_file("銀河易經")
    if f_iching:
        df = read_csv_robust(f_iching)
        if df is not None: df.to_sql("IChing", conn, if_exists="replace", index=False)


    conn.close()
    print("🎉 資料庫建置完成！")

if __name__ == "__main__":
    init_db()
