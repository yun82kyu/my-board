import streamlit as st

def show_category_manager(categories, cat_sha, all_data, save_json_func):
    st.title("⚙️ 대분류 관리 센터")
    
    # --- 1. 신규 분류 추가 섹션 ---
    with st.container(border=True):
        st.subheader("➕ 신규 분류 추가")
        new_name = st.text_input("새 분류 이름", key="m_input_add_name")
        # st.form 대신 일반 버튼 사용 (파일 분리 시 가장 안전함)
        if st.button("분류 추가 실행", key="m_btn_add_exec", use_container_width=True):
            if new_name and new_name not in categories:
                categories.append(new_name)
                save_json_func("categories.json", categories, cat_sha)
                st.success(f"'{new_name}' 추가 완료!")
                st.rerun()
            elif new_name in categories:
                st.warning("이미 있는 이름입니다.")

    st.write("")

    # --- 2. 분류 삭제 섹션 ---
    with st.container(border=True):
        st.subheader("🗑️ 분류 삭제")
        
        # 글이 0개인 것만 삭제 가능
        deletable_cats = [
            c for c in categories 
            if len([i for i in all_data if i.get('category') == c]) == 0
        ]
        
        if not deletable_cats:
            st.info("삭제 가능한 빈 분류가 없습니다.")
        else:
            target = st.selectbox("삭제할 분류 선택", deletable_cats, key="m_select_del", index=None, placeholder="분류를 고르세요")
            confirm = st.checkbox("정말로 삭제하시겠습니까?", key="m_check_confirm")
            
            # 삭제 실행 버튼
            if st.button("🔥 선택 분류 삭제", key="m_btn_del_exec", type="danger", use_container_width=True):
                if not target:
                    st.error("분류를 선택해주세요.")
                elif not confirm:
                    st.warning("삭제 확인 체크박스에 체크해주세요.")
                elif len(categories) <= 1:
                    st.error("최소 1개는 유지해야 합니다.")
                else:
                    categories.remove(target)
                    save_json_func("categories.json", categories, cat_sha)
                    if st.session_state.current_cat == target:
                        st.session_state.current_cat = categories[0]
                    st.rerun()

    st.divider()
    # 돌아가기
    if st.button("⬅️ 메인으로 돌아가기", key="m_btn_exit"):
        st.session_state.view_mode = "list"
        st.rerun()
