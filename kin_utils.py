# --- 在 kin_utils.py 中新增 ---

# 調性問句列表
TONE_QUESTIONS = {
    1: "我的目的是什麼？", 2: "我的挑戰是什麼？", 3: "我如何提供最好的服務？",
    4: "我採取什麼形式？", 5: "我如何被授權？", 6: "我如何組織平等？",
    7: "我如何歸於中心？", 8: "我是否活出所信？", 9: "我如何完成目的？",
    10: "我如何完美顯化？", 11: "我如何釋放與放下？", 12: "我如何奉獻自己？",
    13: "我如何活在當下？"
}

def get_wavespell_data(kin):
    """
    根據 KIN 計算所屬波符的完整 13 天旅程
    """
    conn = get_db()
    wave_data = []
    
    # 1. 計算波符起始 KIN (磁性調性)
    # 公式: kin - (tone - 1)
    current_tone = (kin - 1) % 13 + 1
    start_kin = kin - (current_tone - 1)
    if start_kin <= 0: start_kin += 260 # 修正跨年問題 (雖不常見但以防萬一)

    # 2. 迴圈生成 13 個 KIN 的資料
    try:
        for i in range(13):
            curr = start_kin + i
            if curr > 260: curr -= 260
            
            # 取得圖騰名稱
            info = get_full_kin_data(curr)
            
            wave_data.append({
                "Tone": i + 1,
                "KIN": curr,
                "Question": TONE_QUESTIONS[i + 1],
                "Seal": info.get('圖騰', '未知'),
                "Name": info.get('主印記', ''),
                "Image": info.get('seal_img', '')
            })
            
    except Exception as e:
        print(f"Wave Error: {e}")
        
    return wave_data

# ... (其餘函數保持不變) ...
