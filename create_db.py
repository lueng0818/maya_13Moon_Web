import sqlite3
import pandas as pd
import os
import glob

DB_NAME = "13moon.db"
DATA_DIR = "data"

def find_file(keyword):
    """在 data 資料夾中模糊搜尋檔案"""
    if not os.path.exists(DATA_DIR): return None
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    for f in files:
        if keyword in os.path.basename(f):
            return f
    return None

def process_matrix_csv(file_path):
    """特殊處理：矩陣.csv (攤平雙層標題)"""
    try:
        df = pd.read_csv(file_path, header=[0, 1])
        new_columns = []
        last_top = "Unknown"
        for top, bottom in df.columns:
            if "Unnamed" not in str(top): last_top = str(top).strip()
            clean_bottom = str(bottom).replace('\n', '').strip()
            new_columns.append(f"{last_top}_{clean_bottom}")
        df.columns = new_columns
        return df
    except Exception as e:
        print(f"⚠️ 矩陣處理警告: {e}")
        return None

def init_db():
    print(f"🚀 開始建置資料庫: {DB_NAME}...")
    conn = sqlite3.connect(DB_NAME)

    # 1. 核心：卓爾金曆
    f = find_file("卓爾金曆")
    if f:
        print(f"🔹 匯入: {os.path.basename(f)}")
        df = pd.read_csv(f)
        df.columns = [c.replace('\n', '').strip() for c in df.columns]
        if 'KIN' in df.columns:
            df['KIN'] = pd.to_numeric(df['KIN'], errors='coerce').fillna(0).astype(int)
            df.to_sql("Kin_Data", conn, if_exists="replace", index=False)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_kin ON Kin_Data (KIN)")

    # 2. 核心：矩陣 (441)
    f = find_file("矩陣.csv") # 精確一點避免抓到其他的
    if f:
        print(f"🔹 匯入: {os.path.basename(f)}")
        df = process_matrix_csv(f)
        if df is not None:
            df.to_sql("Matrix_Data", conn, if_exists="replace", index=False)

    # 3. 全腦調頻 (座標參考)
    f = find_file("全腦調頻")
    if f:
        print(f"🔹 匯入: {os.path.basename(f)}")
        try:
            df = pd.read_csv(f, header=1) # 標題在第2行
            df.rename(columns={df.columns[0]: 'Row_Label'}, inplace=True)
            df.to_sql("Matrix_441", conn, if_exists="replace", index=False)
        except: pass

    # 4. 易經
    f = find_file("銀河易經")
    if f:
        print(f"🔹 匯入: {os.path.basename(f)}")
        df = pd.read_csv(f)
        df.to_sql("IChing", conn, if_exists="replace", index=False)

    # 5. 星際年
    f = find_file("星際年")
    if f:
        print(f"🔹 匯入: {os.path.basename(f)}")
        df = pd.read_csv(f)
        df.to_sql("Star_Years", conn, if_exists="replace", index=False)

    # 6. 通訊錄
    f = find_file("通訊錄")
    if f:
        print(f"🔹 匯入: {os.path.basename(f)}")
        df = pd.read_csv(f)
        # 只取需要的欄位，避免格式錯誤
        valid_cols = [c for c in df.columns if c.strip() in ['編號','名字','出生年','出生月','出生日','KIN']]
        if valid_cols:
            df[valid_cols].to_sql("Users", conn, if_exists="replace", index=False)

    conn.close()
    print("🎉 資料庫建置完成！")

if __name__ == "__main__":
    init_db()
