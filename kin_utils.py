# ... (保留前面的代碼) ...

def get_user_list():
    conn = get_db()
    try:
        ensure_users_table(conn)
        # 【關鍵】必須包含 '主印記' 欄位
        df = pd.read_sql("SELECT 姓名, 生日, KIN, 主印記 FROM Users", conn)
        return df
    except:
        return pd.DataFrame() # 回傳空 DataFrame 避免報錯
    finally:
        conn.close()

# ... (保留後面的代碼) ...
