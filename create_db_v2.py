import sqlite3
import pandas as pd
import os
import glob

DB_NAME = "13moon.db"
DATA_DIR = "data"  # 請確認 CSV 檔案都放在這個資料夾

def find_file(keyword):
    """搜尋包含關鍵字的檔案"""
    if not os.path.exists(DATA_DIR):
        print(f"❌ 找不到資料夾 '{DATA_DIR}'")
        return None
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    for f in files:
        if keyword in f:
            return f
    return None

def process_matrix_csv(file_path):
    """特殊處理：矩陣.csv (處理雙層標題)"""
    try:
        # 讀取 header=0 和 1 (雙層標題)
        df = pd.read_csv(file_path, header=[0, 1])
        
        # 攤平標題: "時間矩陣_KIN", "空間矩陣_矩陣位置"...
        new_columns = []
        last_top = "Unknown"
        
        for top, bottom in df.columns:
            # 如果上層標題不是 Unnamed，就更新 last_top
            if "Unnamed" not in str(top):
                last_top = top
            
            # 清理下層標題
            clean_bottom = str(bottom).replace('\n', '').strip()
            
            # 組合新欄位名
            new_col = f"{last_top}_{clean_bottom}"
            new_columns.append(new_col)
            
        df.columns = new_columns
        return df
    except Exception as e:
        print(f"   ❌ 矩陣處理錯誤: {e}")
        return None

def init_db():
    print(f"🚀 開始執行 10 表單整合: {DB_NAME}...\n")
    conn = sqlite3.connect(DB_NAME)

    # 1. 矩陣.csv (核心中的核心)
    f = find_file("矩陣")
    if f:
        print(f"🔹 處理矩陣數據: {f}")
        df = process_matrix_csv(f)
        if df is not None:
            df.to_sql("Matrix_Data", conn, if_exists="replace", index=False)
            print(f"   ✅ Matrix_Data 建立成功 ({len(df)} 列)")

    # 2. 銀河易經編碼
    f = find_file("銀河易經")
    if f:
        print(f"🔹 處理易經編碼: {f}")
        df = pd.read_csv(f)
        df.to_sql("IChing", conn, if_exists="replace", index=False)
        print(f"   ✅ IChing 建立成功")

    # 3. 星際年
    f = find_file("星際年")
    if f:
        print(f"🔹 處理星際年: {f}")
        df = pd.read_csv(f)
        df.to_sql("Star_Years", conn, if_exists="replace", index=False)
        print(f"   ✅ Star_Years 建立成功")

    # 4. 對應瑪雅生日 (萬年曆)
    f = find_file("瑪雅生日")
    if f:
        print(f"🔹 處理瑪雅生日對照表: {f}")
        df = pd.read_csv(f)
        df.to_sql("Calendar_Converter", conn, if_exists="replace", index=False)
        print(f"   ✅ Calendar_Converter 建立成功")

    # 5. 圖騰調性對應清單 (名人範例)
    f = find_file("圖騰調性")
    if f:
        print(f"🔹 處理名人對照清單: {f}")
        df = pd.read_csv(f)
        df.to_sql("Reference_Examples", conn, if_exists="replace", index=False)
        print(f"   ✅ Reference_Examples 建立成功")

    # 6. 通訊錄 (補漏)
    f = find_file("通訊錄")
    if f:
        print(f"🔹 處理通訊錄: {f}")
        df = pd.read_csv(f)
        if '名字' in df.columns:
            df.to_sql("Users", conn, if_exists="replace", index=False)
            print(f"   ✅ Users 建立成功")

    # 7. 卓爾金曆 (補漏 - 這是網站運作的基礎，雖然這次清單沒列，但一定要有)
    f = find_file("卓爾金曆")
    if f:
        print(f"🔹 處理卓爾金曆: {f}")
        df = pd.read_csv(f)
        if 'KIN' in df.columns:
            df.to_sql("Kin_Data", conn, if_exists="replace", index=False)
            print(f"   ✅ Kin_Data 建立成功")
    else:
        print("   ⚠️ 提醒：這次上傳清單中未包含「卓爾金曆KIN對照表」，請確認資料庫中已有此表，否則網站無法運作。")

    print("\nℹ️  以下檔案為個人計算結果或非結構化資料，已略過匯入：")
    print("   - 流年印記.csv (動態計算)")
    print("   - 個人流日印記.csv (動態計算)")
    print("   - 對等印記.csv (動態計算)")
    print("   - 國王預言棋盤.csv (視覺版型)")

    conn.close()
    print("\n🎉 整合完成！現在您的資料庫擁有完整的矩陣與曆法數據了。")

if __name__ == "__main__":
    init_db()
