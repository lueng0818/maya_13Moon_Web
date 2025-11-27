import sqlite3
import pandas as pd
import os
import glob

DB_NAME = "13moon.db"
DATA_DIR = "data"  # 請確認您的 CSV 都在 data 資料夾內

def find_file(keyword):
    """強力搜尋：只要檔名包含關鍵字就抓出來"""
    if not os.path.exists(DATA_DIR):
        print(f"❌ 錯誤：找不到 data 資料夾 ({DATA_DIR})")
        return None
    
    # 搜尋所有 csv (不分大小寫)
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    for f in files:
        if keyword in f:
            return f
    return None

def process_matrix_csv(file_path):
    """處理矩陣.csv 的雙層標題問題"""
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
    
    # 先刪除舊的資料庫，確保重建
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print("🗑️ 已刪除舊資料庫，準備重建...")

    conn = sqlite3.connect(DB_NAME)
    
    # 1. 核心：卓爾金曆 (最重要！)
    f = find_file("卓爾金曆")
    if f:
        print(f"🔹 匯入 KIN 對照表: {os.path.basename(f)}")
        try:
            df = pd.read_csv(f)
            # 清理欄位名稱
            df.columns = [c.replace('\n', '').strip() for c in df.columns]
            
            # 確保 KIN 是數字
            if 'KIN' in df.columns:
                df['KIN'] = pd.to_numeric(df['KIN'], errors='coerce').fillna(0).astype(int)
                df.to_sql("Kin_Data", conn, if_exists="replace", index=False)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_kin ON Kin_Data (KIN)")
                print("   ✅ Kin_Data 建立成功")
            else:
                print("   ❌ 錯誤：CSV 中找不到 'KIN' 欄位")
        except Exception as e:
            print(f"   ❌ 讀取失敗: {e}")
    else:
        print("❌ 嚴重錯誤：找不到「卓爾金曆」CSV 檔！資料庫將會是空的。")

    # 2. 核心：矩陣 (441)
    f = find_file("矩陣") 
    if f:
        print(f"🔹 匯入矩陣: {os.path.basename(f)}")
        df = process_matrix_csv(f)
        if df is not None:
            df.to_sql("Matrix_Data", conn, if_exists="replace", index=False)
            print("   ✅ Matrix_Data 建立成功")

    # 3. 易經
    f = find_file("銀河易經")
    if f:
        print(f"🔹 匯入易經: {os.path.basename(f)}")
        df = pd.read_csv(f)
        df.to_sql("IChing", conn, if_exists="replace", index=False)
        print("   ✅ IChing 建立成功")

    # 4. 通訊錄
    f = find_file("通訊錄")
    if f:
        print(f"🔹 匯入通訊錄: {os.path.basename(f)}")
        df = pd.read_csv(f)
        valid_cols = [c for c in df.columns if c.strip() in ['編號','名字','出生年','出生月','出生日','KIN']]
        if valid_cols:
            df[valid_cols].to_sql("Users", conn, if_exists="replace", index=False)
            print("   ✅ Users 建立成功")

    conn.close()
    print("🎉 資料庫建置程序結束。")

if __name__ == "__main__":
    init_db()
