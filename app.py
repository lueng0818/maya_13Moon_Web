# --- 在 app.py 的 tab_20 區塊下方新增 ---

from kin_utils import get_wavespell_data # 記得匯入新函數

# ... (前面是神諭盤代碼) ...

            # --- 新增：波符旅程 (Wavespell Journey) ---
            st.markdown("---")
            st.subheader(f"🌊 {data.get('wave_name','')} 波符旅程")
            
            # 取得波符資料
            wavespell = get_wavespell_data(kin)
            
            if wavespell:
                # 使用 expander 收納，避免頁面太長
                with st.expander("📜 查看完整 13 天波符問答", expanded=True):
                    for w in wavespell:
                        # 標示出「當日」的 KIN
                        highlight = "border: 2px solid #d4af37; background: #333;" if w['KIN'] == kin else "border: 1px solid #444;"
                        
                        # 顯示單行波符資料
                        c_img, c_txt = st.columns([0.5, 4])
                        with c_img:
                             if os.path.exists(f"assets/seals/{w['Image']}"):
                                st.image(f"assets/seals/{w['Image']}", width=40)
                        with c_txt:
                            st.markdown(f"""
                            <div style="{highlight} padding: 8px; border-radius: 5px; margin-bottom: 5px;">
                                <b style="color:#d4af37">調性 {w['Tone']}：{w['Question']}</b><br>
                                <span style="font-size:14px;">KIN {w['KIN']} {w['Name']}</span>
                            </div>
                            """, unsafe_allow_html=True)

# ... (後面是 tab_28 的代碼) ...
