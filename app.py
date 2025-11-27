# app.py 的 show_card 函數部分

def show_card(label, s_id, t_id, is_main=False):
    """
    顯示單張印記卡片
    """
    # 取得檔名 (確保 kin_utils.py 的對照表正確)
    # 【修正】：這裡預設值改成 .png
    s_file = SEAL_FILES.get(s_id, f"{str(s_id).zfill(2)}.png") 
    t_file = TONE_FILES.get(t_id, f"tone-{t_id}.png")
    
    # 組合路徑
    path_seal = f"assets/seals/{s_file}"
    path_tone = f"assets/tones/{t_file}"
    
    with st.container():
        # ... (中間不變) ...
        
        # 顯示圖騰 (中間)
        if os.path.exists(path_seal):
            st.image(path_seal, width=70 if not is_main else 100)
        else:
            # 顯示錯誤時，也順便顯示它在找哪個檔名
            st.warning(f"缺圖: {s_file}")
            
        # ... (後面不變) ...
