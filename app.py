# --- 在 app.py 中 "國王棋盤" 頁面 (約 400 行左右) ---

elif mode == "國王棋盤":
    st.title("👑 國王預言棋盤 (Telektonon)")
    st.markdown("""
    <div class="concept-text">
    <b>Telektonon：</b>這是一個將太陽系行星軌道、身體脈輪與時間頻率結合的預言遊戲。
    透過每日的移動，我們在棋盤上編織出時間的 telepathic 網絡。
    </div>
    """, unsafe_allow_html=True)
    
    d, _ = render_date_selector("king")
    
    if st.button("🔮 讀取棋盤訊息", type="primary"):
        # 計算基礎資訊
        kin, _ = calculate_kin_v2(d)
        if not kin: kin = calculate_kin_math(d)
        maya = get_maya_calendar_info(d)
        
        # 獲取棋盤資訊 (新函數)
        from kin_utils import get_telektonon_info
        tk_info = get_telektonon_info(kin, maya)
        
        st.divider()
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("🏰 時間旅程")
            st.info(f"**日期**：{maya['Maya_Date']}")
            st.write(f"**水晶柱 (Battery)**：{tk_info['Crystal_Battery']}")
            st.write(f"**戰士立方 (Cube)**：{tk_info['Warrior_Cube']}")
            
        with c2:
            st.subheader("🐢 烏龜日指引")
            if tk_info['Turtle_Color'] != '-':
                color_map = {"綠烏龜": "#e6fffa", "白烏龜": "#f0f0f0", "黃烏龜": "#fffff0"}
                bg = color_map.get(tk_info['Turtle_Color'], "#333")
                
                st.markdown(f"""
                <div style="background:{bg}; color:#333; padding:15px; border-radius:10px; border:2px solid #ccc;">
                    <h4 style="margin:0">🐢 {tk_info['Turtle_Color']}</h4>
                    <p style="font-size:18px; font-weight:bold;">{tk_info['Turtle_Day']}</p>
                    <p>{tk_info.get('Turtle_Desc','')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if tk_info['Rune'] != '-':
                    st.success(f"**盧恩符文意涵**：{tk_info['Rune']}")
            else:
                st.warning("無烏龜日資料")
        
        # 顯示棋盤原始資料 (供進階參考)
        with st.expander("📜 查看原始對照表"):
             df = pd.read_sql("SELECT * FROM King_Prophecy", sqlite3.connect("13moon.db"))
             st.dataframe(df)
