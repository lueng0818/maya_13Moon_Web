import sqlite3
import pandas as pd
import os
import glob

DB_NAME = "13moon.db"
DATA_DIR = "data"

def find_file(keyword):
    """模糊搜尋：只要檔名包含關鍵字就抓出來 (解決檔名太長的問題)"""
    if not os.path.exists(DATA_DIR): return None
    # 搜尋所有 csv
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    for f in files:
        if keyword in os.path.basename(f):
            return f
    return None

def read_csv_robust(file_path, **kwargs):
    """萬能讀取：自動嘗試 utf-8, big5, cp950 編碼"""
    encodings = ['utf-8', 'cp950', 'big5', 'utf-8-sig', 'gbk']
    for enc in encodings:
        try:
            df = pd.read_csv(file_path, encoding=enc, **kwargs)
            return df
        except UnicodeDecodeError:
            continue
        except Exception:
            continue
    return None

def process_matrix_csv(file_path):
    """處理矩陣.csv 的雙層標題"""
    try:
        # 使用萬能讀取
        df = read_csv_robust(file_path, header=[0, 1])
        if df is None: return None

        new_columns = []
        last_top = "Unknown"
        for top, bottom in df.columns:
            if "Unnamed" not in str(top): last_top = str(top).strip()
            clean_bottom = str(bottom).replace('\n', '').strip()
            new_columns.append(f"{last_top}_{clean_bottom}")
        df.columns = new_columns
        return df
    except:
        return None

def init_db():
    print(f"🚀 開始建置資料庫: {DB_NAME}...")
    
    # 刪除舊檔以防萬一
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

    conn = sqlite3.connect(DB_NAME)
    
    # 1. 核心：卓爾金曆 (Kin_Data)
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

    # 2. 核心：矩陣 (Matrix_Data)
    f = find_file("矩陣") 
    if f:
        print(f"🔹 匯入矩陣: {os.path.basename(f)}")
        df = process_matrix_csv(f)
        if df is not None:
            df.to_sql("Matrix_Data", conn, if_exists="replace", index=False)

    # 3. 易經 (IChing)
    f = find_file("銀河易經")
    if f:
        print(f"🔹 匯入易經: {os.path.basename(f)}")
        df = read_csv_robust(f)
        if df is not None:
            df.to_sql("IChing", conn, if_exists="replace", index=False)

    # 4. 通訊錄 (Users)
    f = find_file("通訊錄")
    if f:
        print(f"🔹 匯入通訊錄: {os.path.basename(f)}")
        df = read_csv_robust(f)
        if df is not None:
            valid = [c for c in df.columns if c.strip() in ['編號','名字','出生年','出生月','出生日','KIN']]
            if valid: df[valid].to_sql("Users", conn, if_exists="replace", index=False)

    conn.close()
    print("🎉 資料庫建置完成！")

if __name__ == "__main__":
    init_db()
