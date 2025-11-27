import sqlite3
import pandas as pd
import os
import glob

DB_NAME = "13moon.db"
DATA_DIR = "data"

def find_file(keyword):
    """模糊搜尋：只要檔名包含關鍵字就抓出來"""
    if not os.path.exists(DATA_DIR): return None
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    for f in files:
        if keyword in os.path.basename(f):
            return f
    return None

def read_csv_robust(file_path, **kwargs):
    """萬能讀取：自動嘗試多種編碼"""
    encodings = ['utf-8', 'cp950', 'big5', 'utf-8-sig', 'gbk']
    for enc in encodings:
        try:
            df = pd.read_csv(file_path, encoding=enc, **kwargs)
            return df
        except Exception:
            continue
    return None

def process_matrix_csv(file_path):
    """
    處理矩陣.csv：
    1. 攤平雙層標題
    2. 【關鍵修正】解決欄位名稱重複的問題 (Deduplicate columns)
    """
    try:
        # 使用萬能讀取，讀取雙層標題
        df = read_csv_robust(file_path, header=[0, 1])
        if df is None: return None

        # 1. 攤平標題
        raw_columns = []
        last_top = "Unknown"
        for top, bottom in df.columns:
            # 如果上層標題不是 Unnamed，就更新 last_top
            if "Unnamed" not in str(top): 
                last_top = str(top).strip()
            
            clean_bottom = str(bottom).replace('\n', '').strip()
            # 組合新欄位名，例如 "時間矩陣_KIN"
            raw_columns.append(f"{last_top}_{clean_bottom}")
        
        # 2. 【關鍵修正】處理重複欄位名稱
        # 如果有兩個 "空間矩陣_KIN"，第二個會變成 "空間矩陣_KIN_2"
        seen_cols = {}
        deduped_columns = []
        
        for col in raw_columns:
            if col not in seen_cols:
                seen_cols[col] = 1
                deduped_columns.append(col)
            else:
                seen_cols[col] += 1
                deduped_columns.append(f"{col}_{seen_cols[col]}")
        
        df.columns = deduped_columns
        return df
    except Exception as e:
        print(f"⚠️ 矩陣處理警告: {e}")
        return None

def init_db():
    print(f"🚀 開始建置資料庫: {DB_NAME}...")
    
    # 刪除舊檔以確保乾淨重建
    if os.path.exists(DB_NAME):
        try:
            os.remove(DB_NAME)
        except: pass

    conn = sqlite3.connect(DB_NAME)
    
    # 1. 核心：卓爾金曆
    f = find_file("卓爾金曆")
    if f:
        print(f"🔹 匯入卓爾金曆: {os.path.basename(f)}")
        df = read_csv_robust(f)
        if df is not None:
            df.columns = [c.replace('\n', '').strip() for c in df.columns]
            if 'KIN' in df.columns:
                df['KIN'] = pd.to_numeric(df['KIN'], errors='coerce').fillna(0).astype(int)
                df.to_sql("Kin_Data", conn, if_exists="replace", index=False)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_kin ON Kin_Data (KIN)")

    # 2. 核心：矩陣 (Matrix_Data) - 這裡就是剛剛報錯的地方
    f = find_file("矩陣") 
    if f:
        print(f"🔹 匯入矩陣: {os.path.basename(f)}")
        df = process_matrix_csv(f)
        if df is not None:
            # 現在 df 的欄位已經去重複了，可以安全寫入
            df.to_sql("Matrix_Data", conn, if_exists="replace", index=False)

    # 3. 易經
    f = find_file("銀河易經")
    if f:
        print(f"🔹 匯入易經: {os.path.basename(f)}")
        df = read_csv_robust(f)
        if df is not None:
            df.to_sql("IChing", conn, if_exists="replace", index=False)

    # 4. 通訊錄
    f = find_file("通訊錄")
    if f:
        print(f"🔹 匯入通訊錄: {os.path.basename(f)}")
        df = read_csv_robust(f)
        if df is not None:
            # 篩選有效欄位
            valid = [c for c in df.columns if c.strip() in ['編號','名字','出生年','出生月','出生日','KIN']]
            if valid: df[valid].to_sql("Users", conn, if_exists="replace", index=False)

    conn.close()
    print("🎉 資料庫建置完成！")

if __name__ == "__main__":
    init_db()
