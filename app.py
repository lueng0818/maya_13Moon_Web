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
        if keyword in os.path.basename(f):
            return f
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
    """
    處理矩陣.csv：
    1. 攤平雙層標題
    2. 強力去重複 (Deduplicate)
    """
    try:
        # 讀取雙層標題
        df = read_csv_robust(file_path, header=[0, 1])
        if df is None: return None

        # 1. 初步攤平標題
        raw_columns = []
        last_top = "Unknown"
        
        for top, bottom in df.columns:
            # 如果上層標題不是 Unnamed，就更新 last_top
            if "Unnamed" not in str(top): 
                last_top = str(top).strip()
            
            clean_bottom = str(bottom).replace('\n', '').strip()
            # 組合: "時間矩陣_KIN"
            col_name = f"{last_top}_{clean_bottom}"
            raw_columns.append(col_name)
        
        # 2. 強力去重複 (關鍵修正)
        # 如果出現 ["A", "B", "A", "A"] -> 變成 ["A", "B", "A_2", "A_3"]
        final_columns = []
        col_counts = {}
        
        for col in raw_columns:
            if col in col_counts:
                col_counts[col] += 1
                new_col = f"{col}_{col_counts[col]}"
            else:
                col_counts[col] = 1
                new_col = col
            final_columns.append(new_col)
        
        df.columns = final_columns
        return df
        
    except Exception as e:
        print(f"⚠️ 矩陣處理失敗: {e}")
        return None

def init_db():
    print(f"🚀 開始建置資料庫: {DB_NAME}...")
    
    # 刪除舊檔
    if os.path.exists(DB_NAME):
        try: os.remove(DB_NAME)
        except: pass

    conn = sqlite3.connect(DB_NAME)
    
    # --- 1. 計算用表 (優先) ---
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

    # --- 2. 核心資料 ---
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
        # 使用去重複邏輯處理矩陣表
        df = process_matrix_csv(f_matrix)
        if df is not None:
            df.to_sql("Matrix_Data", conn, if_exists="replace", index=False)

    f_iching = find_file("銀河易經")
    if f_iching:
        df = read_csv_robust(f_iching)
        if df is not None: df.to_sql("IChing", conn, if_exists="replace", index=False)

    f_user = find_file("通訊錄")
    if f_user:
        df = read_csv_robust(f_user)
        if df is not None:
            valid = [c for c in df.columns if c.strip() in ['編號','名字','出生年','出生月','出生日','KIN']]
            if valid: df[valid].to_sql("Users", conn, if_exists="replace", index=False)

    conn.close()
    print("🎉 資料庫建置完成！")

if __name__ == "__main__":
    init_db()
