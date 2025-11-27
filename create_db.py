import sqlite3
import pandas as pd
import os

# 設定資料庫名稱
DB_NAME = "13moon.db"

# 定義要匯入的 CSV 檔案 (請確認路徑與檔名是否與您的實際檔案一致)
FILES = {
    "Kin_Data": "data/13月亮曆計算 (DM版) - 高階.xlsx - 卓爾金曆KIN對照表.csv",
    "Users": "data/13月亮曆計算 (DM版) - 高階.xlsx - 通訊錄.csv"
}

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    print(f"🚀 開始建立資料庫: {DB_NAME}...")

    # 1. 匯入 KIN 對照表
    if os.path.exists(FILES["Kin_Data"]):
        try:
            df = pd.read_csv(FILES["Kin_Data"])
            df.columns = [c.replace('\n', '').strip() for c in df.columns] # 清理欄位名
            df['KIN'] = pd.to_numeric(df['KIN'], errors='coerce').fillna(0).astype(int)
            
            # 建立表格
            df.to_sql("Kin_Data", conn, if_exists="replace", index=False)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kin ON Kin_Data (KIN)")
            print(f"✅ Kin_Data 資料表建立完成 ({len(df)} 筆)")
        except Exception as e:
            print(f"❌ Kin_Data 匯入失敗: {e}")
    else:
        print(f"⚠️ 找不到檔案: {FILES['Kin_Data']} (請確認路徑)")

    # 2. 匯入通訊錄 (Users)
    if os.path.exists(FILES["Users"]):
        try:
            df = pd.read_csv(FILES["Users"])
            df.columns = [c.replace('\n', '').strip() for c in df.columns]
            # 只取關鍵欄位，避免髒資料
            valid_cols = [c for c in df.columns if c in ['編號', '名字', '出生年', '出生月', '出生日', 'KIN']]
            if valid_cols:
                df = df[valid_cols]
                df.to_sql("Users", conn, if_exists="replace", index=False)
                print(f"✅ Users 資料表建立完成 ({len(df)} 筆)")
            else:
                print("⚠️ Users CSV 內無有效欄位")
        except Exception as e:
             print(f"❌ Users 匯入失敗: {e}")
    else:
        print(f"⚠️ 找不到檔案: {FILES['Users']} (合盤功能將無通訊錄可用)")

    conn.close()
    print("🎉 資料庫建置作業結束。")

if __name__ == "__main__":
    init_db()